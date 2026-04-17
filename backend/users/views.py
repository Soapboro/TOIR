from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdminUser
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserAdminUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register — регистрация нового пользователя."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login — получение access + refresh токенов."""

    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me — данные текущего пользователя."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        # Always return full UserSerializer data after update
        return Response(UserSerializer(self.get_object()).data)


class UserViewSet(viewsets.ModelViewSet):
    """Управление пользователями внутри /api/auth/ (create + change-password)."""

    queryset = User.objects.all()
    search_fields = ['email', 'full_name', 'first_name', 'last_name', 'department']
    ordering_fields = ['full_name', 'last_name', 'date_joined', 'role']

    def get_permissions(self):
        if self.action in ('list', 'create', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль успешно изменён.'})


# ── Admin-only user management: /api/users/ ──────────────────────────────────

class UserAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/users/       — список пользователей
    GET    /api/users/{id}/  — детальная карточка
    PUT    /api/users/{id}/  — изменение роли, статуса и данных
    PATCH  /api/users/{id}/  — частичное изменение
    DELETE /api/users/{id}/  — удаление

    Доступ: только IsAdminUser.
    """

    queryset = User.objects.all().order_by('full_name', 'email')
    permission_classes = [IsAdminUser]
    search_fields = ['email', 'full_name', 'first_name', 'last_name', 'department']
    filterset_fields = ['role', 'is_active', 'department']
    ordering_fields = ['full_name', 'email', 'role', 'date_joined', 'is_active']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        if self.action in ('update', 'partial_update'):
            return UserAdminUpdateSerializer
        return UserDetailSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {'detail': 'Невозможно удалить собственный аккаунт.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = kwargs.pop('partial', False)
        response = super().update(request, *args, **kwargs)
        # После сохранения всегда возвращаем полный UserDetailSerializer
        return Response(UserDetailSerializer(self.get_object()).data)
