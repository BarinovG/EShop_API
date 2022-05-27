from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import PartnerUpdate, RegisterAccount, LoginAccount, CategoryView, ShopView, ProductInfoView,\
    BasketView, AccountDetails, ContactViewList, ContactViewDetail, OrderView, PartnerState, PartnerOrders, ConfirmAccount

router = DefaultRouter()
router.register('category', CategoryView)
router.register('shops', ShopView)
router.register('product_info', ProductInfoView)


app_name = 'orders'
urlpatterns = [
    # path('user/register', RegisterAccount.as_view(), name='user-register'),
    # path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    # path('user/details', AccountDetails.as_view(), name='user-details'),
    # path('user/login', LoginAccount.as_view(), name='user-login'),
    # path('user/contact', ContactViewList.as_view(), name='user-contact'),
    # path('user/contact/<int:pk>/', ContactViewDetail.as_view(), name='user-contact-delete'),
    # path('user/password_reset', reset_password_request_token, name='password-reset'),
    # path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),

    # path('categories', CategoryView.as_view(), name='categories'),
    # path('shops', ShopView.as_view(), name='shops'),
    # path('products', ProductInfoView.as_view(), name='shops'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('api/v2/', include(router.urls))

]