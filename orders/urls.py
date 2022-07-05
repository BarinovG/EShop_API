from django.urls import path
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import CategoryView, ShopView, ProductInfoView, OrderViewSet, UserViewSet, PartnerFunctionsViewSet, \
    ShoppingCartViewSet

router = DefaultRouter()
router.register('user', UserViewSet, basename='user')
router.register('partner', PartnerFunctionsViewSet, basename='partner')
router.register('shopping_cart', ShoppingCartViewSet, basename='shopping_cart')
router.register('order', OrderViewSet, basename='order')
router.register('category', CategoryView, basename='category')
router.register('shops', ShopView, basename='shops')
router.register('products', ProductInfoView, basename='product_info')

app_name = 'orders'
urlpatterns = [
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm')
] + router.urls
