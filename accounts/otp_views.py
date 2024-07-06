from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex

class OTPSerializer(serializers.Serializer):
    otp = serializers.CharField()

class OTPSetupSerializer(serializers.Serializer):
    otp_uri = serializers.CharField()

class OTPViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def setup_otp(self, request):
        user = request.user
        device = TOTPDevice.objects.create(user=user, name='default', key=random_hex())
        uri = device.config_url
        user.otp_device = device
        user.save()

        return Response({'otp_uri': uri}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        user = request.user

        if user.otp_device.verify_token(otp):
            user.is_otp_verified = True
            user.save()
            return Response({'message': 'OTP verified successfully! Your account is now active.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
