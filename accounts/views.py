from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import User, Account, UserDevice, SiteViewLog, SearchHistory, DeliveryAddress
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserDataSerializer,  AdminUserDataSerializer, UserDeviceSerializer, 
    SiteViewLogSerializer, BulkUserActionSerializer,
    DeliveryAddressSerializer, SearchHistorySerializer, UserDetailSerializer
)
from .renderers import UserRenderer
from .tokens import generate_token
from django.core.files.base import ContentFile
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db import transaction, IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.http import JsonResponse
from datetime import datetime
from django.views import View
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .otp_utils import generate_otp, send_otp_email, is_otp_valid 
from django.utils import timezone

import requests 

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
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

class UserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = UserDataSerializer
    renderer_classes = [UserRenderer]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy', 'get_all_users']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super(UserViewSet, self).get_permissions()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user

        serializer = UserDetailSerializer(user, context = {'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            token = generate_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = config('Frontend_Domain')
            link = f"{domain}/auth/{uid}/{token}"

            subject = "Active your account"
            message = render_to_string('Active_account.html', {
                'name': user.username,
                'link': link,
            })
            email = EmailMessage(subject, message, to=[user.email])
            email.content_subtype = "html"
            email.send()

            return Response({'message': 'Acivation link sent to your email'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def social_login(self, request):
        data = request.data
        provider = data.get('provider')
        email = data.get('email')
        username = data.get('username')
        profile = data.get('profile', {})
        provider_id = profile.get('id') or profile.get('sub')
        
        if not provider or not email or not username:
            return Response({'error': 'Required fields missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_url = profile.get('avatar_url') or profile.get('picture')
        User = get_user_model()

        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(email=email, defaults={
                    'username': username,
                    'state': 'active',
                    'password': User.objects.make_random_password(),
                })
                
                if avatar_url:
                    self._save_user_avatar(user, avatar_url, username)
                
                account, account_created = Account.objects.get_or_create(
                    user=user,
                    provider=provider,
                    defaults={'providerId': provider_id, 'details': str(profile)}
                )
                
                if not account_created:
                    account.providerId = provider_id
                    account.details = str(profile)
                    account.save()

                tokens = get_tokens_for_user(user)
                return Response({'message': 'Login successful!', 'token': tokens}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _save_user_avatar(self, user, avatar_url, username):
        try:
            response = requests.get(avatar_url)
            response.raise_for_status()
            user.profile.save(f'{username}_avatar.png', ContentFile(response.content))
        except requests.RequestException as e:
            print(f"Failed to download avatar: {e}")
        except Exception as e:
            print(f"Failed to save avatar: {e}")
    
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
        
        # if user.state != 'active':
        #     try:
        #         token = generate_token.make_token(user)
        #         uid = urlsafe_base64_encode(force_bytes(user.pk))
        #         domain = config('Frontend_Domain')
        #         link = f"{domain}/auth/{uid}/{token}"

        #         subject = "Active your account"
        #         message = render_to_string('Active_account.html', {
        #             'name': user.username,
        #             'link': link,
        #         })
        #         email = EmailMessage(subject, message, to=[user.email])
        #         email.content_subtype = "html"
        #         email.send()

        #         return Response({'message': 'Acivation link sent to your email'}, status=status.HTTP_200_OK)
        #     except User.DoesNotExist:
        #         return Response({'error': 'Something went wrong'}, status=status.HTTP_404_NOT_FOUND)
                
        if not user.check_password(password):
            user_data = {
                'email': user.email,
                'username': user.username,
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
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'Object deleted'}, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response("Profile Updated.", status=status.HTTP_200_OK)

class UserActivationView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None:
            if generate_token.check_token(user, token):
                user.state = 'active'
                user.save()
                return Response({'success': 'Your account has been activated successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Activation link is expired.'}, status=status.HTTP_410_GONE)
        else:
            return Response({'error': 'Activation link is invalid.'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None        

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        if user:
            otp = generate_otp()
            user.otp_token = otp
            user.otp_created_at = timezone.now()
            user.save()
            send_otp_email(user, otp)
            return Response({'message': 'OTP sent to your email', 'uid': uid}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def patch(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token', None)
        password = request.data.get('password', None)
        otp = request.data.get('otp', None)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            print(user)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and otp:
            if is_otp_valid(user, otp):
                token = generate_token.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                return Response({'message': 'OTP verified successfully', 'token': token, 'uid': uid}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        elif user and token:
            if generate_token.check_token(user, token):
                user.set_password(password)
                user.save()
                return Response({'success': 'Your account has been activated successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = AdminUserDataSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['state', 'email']
    search_fields = ['username', 'email']
    ordering_fields = ['email', 'username']
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        exclude_data = self.request.query_params.get('exclude_by', '')
        exclude_data = exclude_data.split(',')
        if 'active' in exclude_data:
            queryset = queryset.exclude(is_active=True)
        if 'blocked' in exclude_data:
            queryset = queryset.exclude(is_blocked=True)
        if 'inactive' in exclude_data:
            queryset = queryset.exclude(is_active=False)
        return queryset


    @action(detail=False, methods=['get'])
    def list_users(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-username/(?P<username>[^/.]+)')
    def retrieve_user_by_username(self, request, username=None):
        if not request.user.is_admin or not request.user.role == 'Admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

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

class SearchView(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all().order_by('-search_date')
    serializer_class = SearchHistorySerializer
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    pagination_class = CustomPagination        

    def create(self, request, *args, **kwargs):
        keyword = request.data.get('keyword')
        user = request.user if request.user.is_authenticated else None
        if not keyword:
            return Response({'error': 'Keyword is required'}, status=status.HTTP_400_BAD_REQUEST)

        search_history = SearchHistory.objects.create(
            user=user,
            keyword=keyword,
        )

        serializer = self.get_serializer(search_history)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class DeliveryAddressView(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all().order_by('-id')
    serializer_class = DeliveryAddressSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data['user'] = user.id
        
        if data.get('default'):
            DeliveryAddress.objects.filter(user=user, default=True).update(default=False)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response("Address Created", status=status.HTTP_201_CREATED) 

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        data = request.data.copy()
        
        if data.get('default'):
            DeliveryAddress.objects.filter(user=user, default=True).update(default=False)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response("Address Updated", status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get'])
    def get_default(self, request):
        user = request.user
        default_address = DeliveryAddress.objects.filter(user=user, default=True).first()
        if default_address:
            serializer = self.get_serializer(default_address)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No data available"}, status=status.HTTP_404_NOT_FOUND)    