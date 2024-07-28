from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.files.base import ContentFile
import requests

# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def populate_user(self, request, sociallogin, data):
#         print("Social Login Data:", data)
#         user = super().populate_user(request, sociallogin, data)
#         user.email = data.get('email', '')
#         user.first_name = data.get('first_name', '')
#         user.last_name = data.get('last_name', '')
#         user.social = sociallogin.account.provider
#         picture_url = data.get('picture', '')
#         if picture_url:
#             response = requests.get(picture_url)
#             if response.status_code == 200:
#                 user.profile.save(f"{user.email}_profile.jpg", ContentFile(response.content), save=False)

#         user.gender = data.get('gender', '')
        
#         birthdate = data.get('birthdate', '')
#         if birthdate:
#             try:
#                 user.dob = datetime.strptime(birthdate, '%Y-%m-%d').date()
#             except ValueError:
#                 user.dob = None
#         return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        print(data)
        user.email = data.get('email', '')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')

        user.social = sociallogin.account.provider
        additional_data = sociallogin.account.extra_data
        if 'picture' in additional_data:
            picture_url = additional_data.get('picture')
            response = requests.get(picture_url)
            if response.status_code == 200:
                user.profile.save(f"{user.email}_profile.jpg", ContentFile(response.content), save=False)
            else:
                print(f"Failed to download profile picture. Status code: {response.status_code}")

        return user

