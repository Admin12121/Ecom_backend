from rest_framework import serializers
from .models import User, UserDevice, SiteViewLog, SearchHistory, DeliveryAddress
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
import requests 

class SiteViewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteViewLog
        fields = '__all__'

class BulkUserActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_blocked']



class CustomSocialLoginSerializer(SocialLoginSerializer):
    def save(self, request):
        adapter_class = GoogleOAuth2Adapter
        adapter = adapter_class()
        app = adapter.get_provider().get_app(request)
        token = self.validated_data.get('access_token')
        token_secret = self.validated_data.get('token_secret', None)

        if not token:
            raise serializers.ValidationError("Access token is missing.")
        
        social_login = adapter.complete_login(request, app, token, response=token_secret)
        social_login.token = token
        social_login.state = self.validated_data.get('state', None)
        self.custom_signup(request, social_login)

        # Fetch additional user data from Google People API
        additional_data = self.fetch_additional_data(token)
        social_login.account.extra_data.update(additional_data)
        social_login.save(request)

        return social_login

    def fetch_additional_data(self, token):
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://people.googleapis.com/v1/people/me?personFields=birthdays,genders,addresses,phoneNumbers',
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise serializers.ValidationError(f"Failed to fetch additional data. Status code: {response.status_code}")



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'tc', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        user = self.context['user']
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError('Old password is incorrect')
        return data

class SendUserPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class UserPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField()

class AdminUserDataSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = '__all__'
    def get_profile(self, obj):
        request = self.context.get('request')
        if obj.profile and hasattr(obj.profile, 'url'):
            return request.build_absolute_uri(obj.profile.url)
        return None

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = '__all__'

class DeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'
