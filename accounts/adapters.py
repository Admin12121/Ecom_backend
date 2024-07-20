from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.core.files.base import ContentFile
import requests
from datetime import datetime

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        print(request)
        user = super().populate_user(request, sociallogin, data)
        user.email = data.get('email', '')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        picture_url = data.get('picture', '')
        if picture_url:
            response = requests.get(picture_url)
            if response.status_code == 200:
                user.profile.save(f"{user.email}_profile.jpg", ContentFile(response.content), save=False)

        user.gender = data.get('gender', '')
        
        birthdate = data.get('birthdate', '')
        if birthdate:
            try:
                user.dob = datetime.strptime(birthdate, '%Y-%m-%d').date()
            except ValueError:
                user.dob = None
        return user
