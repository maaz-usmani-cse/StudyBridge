from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'username', 'email', 'mobile', 'role', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('full_name', 'username', 'email', 'mobile')
    list_editable = ('role',) 