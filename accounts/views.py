from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from .models import User, UserDevice
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserDataSerializer,
    UserChangePasswordSerializer, SendUserPasswordResetEmailSerializer,
    UserPasswordResetSerializer, AdminUserDataSerializer, UserDeviceSerializer, CustomSocialLoginSerializer
)
from .renderers import UserRenderer
from .tokens import generate_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django_otp.oath import TOTP
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_admin'] = user.is_admin
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = CustomSocialLoginSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)    
        user = self.request.user
        tokens = get_tokens_for_user(user)
        response.data.update(tokens)
        return response


class UserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = UserDataSerializer
    renderer_classes = [UserRenderer]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy', 'get_all_users']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super(UserViewSet, self).get_permissions()


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        device = TOTPDevice.objects.create(user=user, name='default', key=random_hex())
        user.otp_device = device
        user.save()

        totp = TOTP(key=device.bin_key)
        otp_token = totp.token()
        subject = "Activate your KitPOS account"
        message = render_to_string('activation_email.html', {
            'name': user.first_name,
            'otp_code': otp_token,
            'domain': config('DOMAIN'),
        })
        email = EmailMessage(subject, message, to=[user.email])
        email.send()

        return Response({
            'message': 'Registration successful! Please verify your email to activate your account.',
        }, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_otp_verified:
            return Response({'error': 'Please verify your account first.'}, status=status.HTTP_403_FORBIDDEN)
        
        if not user.check_password(password):
            user_data = {
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}",
                'profile': request.build_absolute_uri(user.profile.url) if user.profile else None,
            }
            return Response({'error': 'Password does not match', 'user': user_data}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({ 'message': 'Login successful!', 'token': get_tokens_for_user(user), }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def device(self,request):
        user = request.user
        data = request.data.copy()
        data['user'] = user.id
        existing_device = UserDevice.objects.filter(user=user, device_type=data['device_type']).first()
        
        if existing_device:
            return Response({ 'message': 'Device already exists' }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserDeviceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({ 'message': 'Updated' }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = UserChangePasswordSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({'message': 'Password changed successfully!'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def send_reset_password_email(self, request):
        serializer = SendUserPasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            token = generate_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = config('DOMAIN')
            link = f"{domain}/reset/{uid}/{token}"

            subject = "Password Reset Requested"
            message = render_to_string('reset_password_email.html', {
                'name': user.first_name,
                'domain': domain,
                'uid': uid,
                'token': token,
                'link': link,
            })
            email = EmailMessage(subject, message, to=[user.email])
            email.send()

            return Response({'message': 'Password reset link sent!'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def reset_password(self, request, uidb64, token):
        serializer = UserPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = force_str(urlsafe_base64_decode(uidb64))
        try:
            user = User.objects.get(pk=uid)
            if generate_token.check_token(user, token):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password reset successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid token or UID'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid token or UID'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'Object deleted'}, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy', 'deactivate', 'block']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super(UserViewSet, self).get_permissions()

    @action(detail=True, methods=['patch'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User activated successfully!'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully!'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def block(self, request, pk=None):
        user = self.get_object()
        user.is_blocked = True
        user.save()
        return Response({'message': 'User blocked successfully!'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_all_users(self, request):
        users = User.objects.all()
        serializer = AdminUserDataSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
