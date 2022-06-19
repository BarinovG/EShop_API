from rest_framework.permissions import BasePermission


class IsAuthenticatedAndBuyer(BasePermission):
    """
    Allows access only to authenticated users with BUYER status
    """

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.type == 'BUYER')


class IsAuthenticatedAndShop(BasePermission):
    """
    Allows access only to authenticated users with SHOP status
    """

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.type == 'SHOP')
