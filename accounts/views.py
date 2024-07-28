from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from .models import User, UserDevice, SiteViewLog
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserDataSerializer,
    UserChangePasswordSerializer, SendUserPasswordResetEmailSerializer,
    UserPasswordResetSerializer, AdminUserDataSerializer, UserDeviceSerializer, 
    CustomSocialLoginSerializer, SiteViewLogSerializer, BulkUserActionSerializer,
    DeliveryAddressSerializer, SearchHistorySerializer
)
from .renderers import UserRenderer
from .tokens import generate_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db import transaction, IntegrityError
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
from django.db.models import Count, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.http import JsonResponse
from datetime import datetime
from django.views import View
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
import requests 
from rest_framework import serializers

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_admin'] = user.is_admin
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'page_size': self.get_page_size(self.request),
            'results': data
        })

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = CustomSocialLoginSerializer

    def fetch_additional_data(self, token):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://people.googleapis.com/v1/people/me?personFields=birthdays,genders,addresses,phoneNumbers',
            headers=headers
        )
        if response.status_code == 200:
            additional_data = response.json()
            print("response JSON:", additional_data)
            return additional_data
        else:
            print(f"Failed to fetch additional data. Status code: {response.status_code}, Response: {response.text}")
            raise serializers.ValidationError(f"Failed to fetch additional data. Status code: {response.status_code}")

    def post(self, request, *args, **kwargs):
        print("Incoming data: ", request.data)
        response = super().post(request, *args, **kwargs)
        print("Post response data:", response.data)
        
        user = self.request.user
        if user.is_authenticated:
            access_token = request.data.get('access_token')
            if access_token:
                additional_data = self.fetch_additional_data(access_token)
                print("Additional data:", additional_data)

                if 'genders' in additional_data and additional_data['genders']:
                    user.gender = additional_data['genders'][0].get('value', '')

                if 'birthdays' in additional_data and additional_data['birthdays']:
                    birthday = additional_data['birthdays'][0].get('date', {})
                    year = birthday.get('year')
                    month = birthday.get('month')
                    day = birthday.get('day')
                    if year and month and day:
                        try:
                            user.dob = datetime(year, month, day)
                        except ValueError:
                            print(f"Invalid date: {year}-{month}-{day}")

                if 'addresses' in additional_data and additional_data['addresses']:
                    user.address = additional_data['addresses'][0].get('formattedValue', '')

                if 'phoneNumbers' in additional_data and additional_data['phoneNumbers']:
                    user.phone = additional_data['phoneNumbers'][0].get('value', '')

                user.save()
                tokens = get_tokens_for_user(user)
                response.data.update(tokens)
            else:
                print("Access token not found in request data.")
        else:
            print("User is not authenticated.")
        
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
    

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminUserDataSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_blocked', 'email']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['email', 'first_name', 'last_name']
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'])
    def list_users(self, request):
        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-username/(?P<username>[^/.]+)')
    def retrieve_user_by_username(self, request, username=None):
        if not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Include related model data
        context = {'request': request}
        user_data = AdminUserDataSerializer(user, context=context).data
        user_data['delivery_address'] = DeliveryAddressSerializer(user.delivery_address.all(), many=True).data
        user_data['search_history'] = SearchHistorySerializer(user.search_history.all(), many=True).data
        user_data['devices'] = UserDeviceSerializer(user.devices.all(), many=True).data
        user_data['site_view_logs'] = SiteViewLogSerializer(user.site_view_logs.all(), many=True).data

        return Response(user_data, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        serializer = BulkUserActionSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        updates = []
        for data in serializer.validated_data:
            user_id = data.get('id')
            updates.append(User(id=user_id, **data))
        
        try:
            # Use `bulk_update` for efficiency
            User.objects.bulk_update(updates, fields=[field for field in serializer.validated_data[0].keys() if field != 'id'])
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Users updated successfully!'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response({'error': 'No user IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use `bulk_delete` for efficiency
            User.objects.filter(id__in=user_ids).delete()
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Users deleted successfully!'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['patch'])
    def bulk_activate(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response({'error': 'No user IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use `update` for efficiency
            User.objects.filter(id__in=user_ids).update(is_active=True)
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Users activated successfully!'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['patch'])
    def bulk_deactivate(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response({'error': 'No user IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use `update` for efficiency
            User.objects.filter(id__in=user_ids).update(is_active=False)
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Users deactivated successfully!'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['patch'])
    def bulk_block(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response({'error': 'No user IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use `update` for efficiency
            User.objects.filter(id__in=user_ids).update(is_blocked=True)
        except IntegrityError as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Users blocked successfully!'}, status=status.HTTP_200_OK)
    

class SiteViewLogViewSet(viewsets.ModelViewSet):
    queryset = SiteViewLog.objects.all()
    serializer_class = SiteViewLogSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        print(request.data)
        user = request.user if request.user.is_authenticated else None
        ip_address = request.data.get('ip_address')
        user_agent = request.data.get('user_agent')
        location = request.data.get('location', {})
        city = location.get('city')
        region = location.get('region')
        country = location.get('country')
        encsh =  request.data.get('encsh')
        enclg =  request.data.get('enclg')

        site_view_log = SiteViewLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            city=city,
            region=region,
            country=country,
            encsh=encsh,
            enclg=enclg
        )
        return Response({"status": "logged"}, status=201)
    
class SiteViewLogAnalyticsView(View):
    
    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()    
    
    def get(self, request):
        filter_by = request.GET.get('filter_by', 'day')
        group_by = request.GET.get('group_by', None)
        country = request.GET.get('country', None)
        city = request.GET.get('city', None)
        region = request.GET.get('region', None)
        user_agent = request.GET.get('user_agent', None)
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)
        year = request.GET.get('year', None)
        month = request.GET.get('month', None)
        day = request.GET.get('day', None)

        queryset = SiteViewLog.objects.all()

        if country:
            queryset = queryset.filter(country=country)
        if city:
            queryset = queryset.filter(city=city)
        if region:
            queryset = queryset.filter(region=region)
        if user_agent:
            queryset = queryset.filter(user_agent=user_agent)

        if start_date and end_date:
            queryset = queryset.filter(timestamp__range=[start_date, end_date])
        elif year and month and day:
            date = datetime(int(year), int(month), int(day))
            queryset = queryset.filter(timestamp__date=date)
        elif year and month:
            queryset = queryset.filter(timestamp__year=year, timestamp__month=month)
        elif year:
            queryset = queryset.filter(timestamp__year=year)
        
        if filter_by == 'day':
            trunc_func = TruncDay
        elif filter_by == 'week':
            trunc_func = TruncWeek
        elif filter_by == 'month':
            trunc_func = TruncMonth
        elif filter_by == 'year':
            trunc_func = TruncYear
        else:
            return JsonResponse({'error': 'Invalid filter_by parameter'}, status=400)

        queryset = queryset.annotate(period=trunc_func('timestamp')).values('period').annotate(total_views=Count('id')).order_by('period')

        results = {}
        overall_views = queryset.aggregate(overall_views=Count('id'))['overall_views']

        if group_by:
            group_fields = {
                'country': 'country',
                'city': 'city',
                'region': 'region',
                'user_agent': 'user_agent',
            }
            group_field = group_fields.get(group_by)
            if not group_field:
                return JsonResponse({'error': 'Invalid group_by parameter'}, status=400)
            
            grouped_queryset = queryset.values(group_field, 'period').annotate(total_views=Count('id')).order_by(group_field, 'period')
            for entry in grouped_queryset:
                group_value = entry[group_field]
                period = entry['period'].strftime('%Y-%m-%d') if filter_by == 'day' else entry['period'].strftime('%Y-%W') if filter_by == 'week' else entry['period'].strftime('%Y-%m') if filter_by == 'month' else entry['period'].strftime('%Y')
                if group_value not in results:
                    results[group_value] = {}
                results[group_value][period] = entry['total_views']
        
        else:
            for entry in queryset:
                period = entry['period'].strftime('%Y-%m-%d') if filter_by == 'day' else entry['period'].strftime('%Y-%W') if filter_by == 'week' else entry['period'].strftime('%Y-%m') if filter_by == 'month' else entry['period'].strftime('%Y')
                results[period] = entry['total_views']
        
        response_data = {
            'overall_views': overall_views,
            'details': results
        }

        return JsonResponse(response_data, safe=False)    