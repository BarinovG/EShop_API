from django.conf import settings
from django.core.mail import send_mail
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework.authtoken.models import Token
from .models import ConfirmEmailToken, User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from celery import shared_task
from django.dispatch import receiver


class SendTokens:

    @staticmethod
    def _send_token_mail(token, text):
        return send_mail(f'{token.user.first_name}',
                         f'ur tokken {token.key}. {text}',
                         f'{settings.EMAIL_HOST_USER}',
                         [token.user.email])

    @staticmethod
    @shared_task
    def send_confirm_token(user_id):
        """
        отправляем письмо с подтрердждением почты
        """
        # send an e-mail to the user
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

        SendTokens._send_token_mail(token, 'confirm ur email')

    @staticmethod
    @shared_task
    def send_auth_token(user_id):
        """
        отправляем письмо с токкеном для работы в системе
        """
        # send an e-mail to the user
        token, _ = Token.objects.get_or_create(user_id=user_id)

        SendTokens._send_token_mail(token, 'have a good work')

    @staticmethod
    @receiver(reset_password_token_created)
    def send_reset_password_token(reset_password_token, **kwargs):
        SendTokens._send_token_mail(reset_password_token, 'thats tok for reser password')


token_postman = SendTokens()


class SendInfo:

    @staticmethod
    def _send_mail(user, text, data):
        return send_mail(f'{user.first_name}',
                         f'{text} {data}',
                         f'{settings.EMAIL_HOST_USER}',
                         [user.email])

    @staticmethod
    @shared_task
    def send_change_user_info(user_id, data):
        """
        Информационное письмо о смене данных
        """
        user = User.objects.get(id=user_id)
        text = 'You or someone else changed ur account information'
        SendInfo._send_mail(user, text, data)

    @staticmethod
    @shared_task
    def new_order(user_id, data):
        """
         Информационное письмо о переводе из корзины в статус нового заказа
         """
        user = User.objects.get(id=user_id)
        text = f'Your order change status from BASKET to NEW'
        SendInfo._send_mail(user, text, data)


info_postman = SendInfo()


@shared_task
def import_yaml(user_id, data):
    shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=user_id)
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shop.add(shop.id)
        category_object.save()
        ProductInfo.objects.filter(shop_id=shop.id).delete()
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

        product_info = ProductInfo.objects.create(product_id=product.id,
                                                  external_id=item['id'],
                                                  model=item['model'],
                                                  name=item['name'],
                                                  price=item['price'],
                                                  price_rrc=item['price_rrc'],
                                                  quantity=item['quantity'],
                                                  shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(name=name)
            ProductParameter.objects.create(product_info_id=product_info.id,
                                            parameter_id=parameter_object.id,
                                            value=value)
