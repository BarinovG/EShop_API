from django.conf import settings
from django.core.mail import send_mail
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework.authtoken.models import Token
from .models import ConfirmEmailToken, User
from celery import shared_task
from django.dispatch import receiver


class SendTokens:

    @staticmethod
    def _send_token_mail(token, text):
        return send_mail(f'{token.user.first_name}',
                         f'ur tokken {token.key}. {text}',
                         f'{settings.EMAIL_HOST_USER}',
                         [token.user.email])

    @shared_task
    def send_confirm_token(self, user_id):
        """
        отправляем письмо с подтрердждением почты
        """
        # send an e-mail to the user
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

        self._send_token_mail(token, 'confirm ur email')

    @shared_task
    def send_auth_token(self, user_id):
        """
        отправляем письмо с токкеном для работы в системе
        """
        # send an e-mail to the user
        token, _ = Token.objects.get_or_create(user_id=user_id)

        self._send_token_mail(token, 'have a good work')

    @staticmethod
    @receiver(reset_password_token_created)
    def send_reset_password_tokken(reset_password_token, **kwargs):
        SendTokens._send_token_mail(reset_password_token, 'thats tok for reser password')


postman = SendTokens()


@shared_task
def send_change_info(user_id, data):
    """
    Информационное письмо о смене данных
    """

    user = User.objects.get(id=user_id)

    return send_mail(f'{user.first_name}',
                     f'You or someone else changed ur account information {data}',
                     f'{settings.EMAIL_HOST_USER}',
                     [user.email])
