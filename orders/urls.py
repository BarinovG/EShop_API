from django.urls import path
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import CategoryView, ShopView, ProductInfoView, OrderViewSet, UserViewSet, SellerViewSet, \
    ShoppingCartViewSet, ContactsViewSet, SellersShopsViewSet, AuthViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('auth', AuthViewSet, basename='auth')
router.register('users/contacts', ContactsViewSet, basename='contacts')
router.register('sellers', SellerViewSet, basename='partners')
router.register('sellers/shop', SellersShopsViewSet, basename='partner')
router.register('carts', ShoppingCartViewSet, basename='shopping_cart')
router.register('orders', OrderViewSet, basename='order')
router.register('categories', CategoryView, basename='category')
router.register('shops', ShopView, basename='shops')
router.register('products', ProductInfoView, basename='product_info')

app_name = 'orders'
urlpatterns = [
    path('users/reset_password', reset_password_request_token, name='reset-password'),
    path('users/reset_password_confirm', reset_password_confirm, name='reset-password-confirm')
] + router.urls
