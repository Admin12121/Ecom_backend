from rest_framework import serializers
from .models import User, UserDevice, SiteViewLog, SearchHistory, DeliveryAddress

class SiteViewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteViewLog
        fields = '__all__'

class BulkUserActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'state']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['email', 'phone', 'username', 'password']

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

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id','email', 'profile', 'phone', 'username', 
            'last_name', 'first_name', 'role', 'gender', 'dob'
        ]
        
class SocialLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        user = self.context['user']
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError('Old password is incorrect')
        return data

class AdminUserDataSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()  # Add this line

    class Meta:
        model = User
        exclude = ['password']
    def get_profile(self, obj):
        request = self.context.get('request')
        if obj.profile and hasattr(obj.profile, 'url'):
            return request.build_absolute_uri(obj.profile.url)
        return None
    def get_provider(self, obj):  # Add this method
        return obj.account.provider if hasattr(obj, 'account') else None

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = '__all__'

class DeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        exclude = ['is_deleted']

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'
