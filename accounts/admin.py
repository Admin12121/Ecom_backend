###
from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

 # Register your models here.
class UserModelAdmin(BaseUserAdmin):
   list_display = ( 'email', 'first_name' , 'phone' , 'is_admin')
   list_filter = ('is_admin',)
   fieldsets = (
       ('User Credentials', {'fields': ('email', 'password')}),
       ('Personal info', {'fields': ('profile','username','first_name','last_name','phone','dob','gender','social', 'otp_device','created_at','last_login','tc')}),
       ('Permissions', {'fields': ('role','is_otp_verified','is_blocked','is_active','is_admin',)}),
   )
   # add_fieldsets is not a standard ModelAdmin attribute. UserModelAdmin
   # overrides get_fieldsets to use this attribute when creating a user.
   add_fieldsets = (
       (None, {
           'classes': ('wide',),
           'fields': ('email', 'first_name','last_name', 'tc', 'password1', 'password2'),
       }),
   )
   readonly_fields = ('created_at',)
   search_fields = ( 'email','first_name')
   ordering = ('email', 'id')
   filter_horizontal = ()

class UserInfoInline(admin.StackedInline):
     model = User
     can_delete = False
     verbose_name_plural = 'User Profiles'

 # Now register the new UserModelAdmin...
admin.site.register(User, UserModelAdmin)
admin.site.register(UserDevice)
admin.site.register(SiteViewLog)
admin.site.register(SearchHistory)
