from rest_framework.permissions import BasePermission

from .models import Role


class IsAdminUser(BasePermission):
    """Только администраторы."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsMechanic(BasePermission):
    """Только механики."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.MECHANIC
        )


class IsOperator(BasePermission):
    """Только операторы."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.OPERATOR
        )


class IsManager(BasePermission):
    """Только менеджеры."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.MANAGER
        )


class IsAdminOrMechanic(BasePermission):
    """Администраторы или механики."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.MECHANIC)
        )


class IsAdminOrManager(BasePermission):
    """Администраторы или менеджеры."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.MANAGER)
        )
