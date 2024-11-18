import random
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

def generate_otp():
    return str(random.randint(10000, 99999))
    # return "123456"

def send_otp_email(user, otp):
    try:
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.EMAIL_HOST_USER,  
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

def is_otp_valid(user, otp):
    if user.otp_token == otp and (timezone.now() - user.otp_created_at).seconds < 300:
        return True
    return False
