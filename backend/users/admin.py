from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'department', 'is_active']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Роль и контакты', {'fields': ('role', 'phone', 'department', 'is_email_notifications_enabled')}),
    )
