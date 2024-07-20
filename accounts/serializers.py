from rest_framework import serializers
from .models import User, UserDevice
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

class CustomSocialLoginSerializer(SocialLoginSerializer):
    def save(self, request):
        # adapter_class = self.adapter_class if self.adapter_class else GoogleOAuth2Adapter
        adapter_class = GoogleOAuth2Adapter    
        adapter = adapter_class()
        app = adapter.get_provider().get_app(request)
        token = self.validated_data['access_token']
        token_secret = self.validated_data.get('token_secret', None)
        social_login = adapter.complete_login(request, app, token, response=token_secret)
        social_login.token = token
        social_login.state = self.validated_data['state']
        self.custom_signup(request, social_login)
        return social_login


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
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'is_otp_verified', 'is_admin', 'is_superuser', 'profile']

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = '__all__'