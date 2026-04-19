from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'department', 'phone', 'is_active']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['email', 'full_name', 'phone', 'department']
    ordering = ['full_name']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Личные данные', {'fields': ('full_name', 'phone', 'department')}),
        ('Роль и доступ', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Уведомления', {'fields': ('is_email_notifications_enabled',)}),
        ('Служебные даты', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'role', 'password1', 'password2'),
        }),
    )
