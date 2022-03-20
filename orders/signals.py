from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from .models import ConfirmEmailToken, User
from celery import shared_task


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    """

    msg = EmailMultiAlternatives(
        # subject:
        f"Password Reset Token for {reset_password_token.user}",
        # body:
        reset_password_token.key,
        # from_email:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.send()


@shared_task
def new_user_registered(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """

    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()


@shared_task
def new_order(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """

    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # subject:
        f"Обновление статуса заказа",
        # body:
        'Заказ сформирован',
        # from_email:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()