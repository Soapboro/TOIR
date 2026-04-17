from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


# ── Общий сериализатор (используется в auth/me и JWT-ответе) ─────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'first_name', 'last_name',
            'role', 'phone', 'department', 'is_email_notifications_enabled',
            'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


# ── Сериализаторы для админского управления пользователями ───────────────────

class UserListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для GET /api/users/ (список)."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name',
            'role', 'department', 'is_active', 'date_joined',
        ]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для GET /api/users/{id}/."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'first_name', 'last_name',
            'role', 'phone', 'department', 'is_email_notifications_enabled',
            'is_active', 'is_staff', 'date_joined', 'last_login',
        ]
        read_only_fields = fields


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """PUT /api/users/{id}/ — изменение роли, статуса и основных данных."""

    class Meta:
        model = User
        fields = [
            'role', 'is_active',
            'full_name', 'first_name', 'last_name',
            'phone', 'department',
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'full_name', 'first_name', 'last_name',
            'password', 'role', 'phone', 'department',
        ]
        extra_kwargs = {
            'role': {'required': False},
            'phone': {'required': False},
            'department': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'full_name': {'required': False},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'full_name', 'first_name', 'last_name',
            'role', 'phone', 'department', 'password',
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'full_name', 'first_name', 'last_name',
            'phone', 'department', 'is_email_notifications_enabled',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
