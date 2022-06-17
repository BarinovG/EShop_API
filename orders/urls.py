from django.urls import path
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import CategoryView, ShopView, ProductInfoView, OrderViewSet, UserViewSet, PartnerFunctionsViewSet, \
    ShoppingCartViewSet

router = DefaultRouter()
router.register('user', UserViewSet, basename='user')
router.register('partner', PartnerFunctionsViewSet, basename='partner')
router.register('shopping_cart', ShoppingCartViewSet, basename='basket')
router.register('order', OrderViewSet, basename='order')

app_name = 'orders'
urlpatterns = [
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('product_info', ProductInfoView.as_view(), name='product_info'),
    path('shops', ShopView.as_view(), name='shops'),
] + router.urls
