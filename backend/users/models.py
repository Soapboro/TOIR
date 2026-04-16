from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    MECHANIC = 'mechanic', 'Механик'
    OPERATOR = 'operator', 'Оператор'
    MANAGER = 'manager', 'Менеджер'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, verbose_name='Полное имя')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_email_notifications_enabled = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name or self.email} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_mechanic(self):
        return self.role in (Role.ADMIN, Role.MECHANIC)
