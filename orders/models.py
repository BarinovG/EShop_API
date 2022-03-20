from django.db import models
from django.db.models import UniqueConstraint, options
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django_rest_passwordreset.tokens import get_token_generator


class TypeContacts(models.TextChoices):
    SHOP = 'SHOP', 'Магазин'
    BUYER = 'CLIENT', 'Покупатель'


class StatusOrders(models.TextChoices):
    # BASKET = 'BASKET', 'Корзина'
    NEW = 'NEW', 'Новый заказ'
    CONFIRMED = 'CONFIRMED', 'Подтвержденный заказ'
    ASSEMBLED = 'ASSEMBLED', 'Заказ собран'
    SENT = 'SENT', 'Заказ отправлен'
    DELIVERED = 'DELIVERED', 'Заказ доставлен'
    CANCELED = 'CANCELED', 'Заказ отменен'


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователем
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Пользовательская модель
    """
    objects = UserManager()
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    email = models.EmailField('Электронная почта', unique=True)
    company = models.CharField('Компания', max_length=60, blank=True)
    position = models.CharField('Должность', max_length=60, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        'Имя пользователя',
        max_length=200,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={'unique': 'A user with that username already exists.'},
        )
    is_active = models.BooleanField(
        'Активация',
        default=False,
        help_text='Designates whether this user should be treated as active. \
        Unselect this instead of deleting accounts.'
    )
    type = models.TextField(
        'Тип пользователя',
        choices=TypeContacts.choices,
        default=TypeContacts.BUYER,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'
        ordering = ('email',)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Shop(models.Model):
    name = models.CharField('Имя пользователя', max_length=200)
    url = models.URLField('Cсылка', null=True, blank=True)
    user = models.OneToOneField(
        User,
        verbose_name='Пользователь',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    state = models.BooleanField('Возможность заказа из магазина', default=True)
    # upload = models.FileField(name=None, upload_to='uploads/', )

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Cписок магазинов'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField('Название', max_length=50)
    shop = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Список категорий'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('Название', max_length=50)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='products',
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ('-name', )

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    name = models.CharField('Название', max_length=50)
    shop = models.ForeignKey(
        Shop,
        verbose_name='Магазин',
        on_delete=models.CASCADE,
        related_name='product_info',
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        related_name='product_info',
        blank=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField('Количество')
    price = models.PositiveIntegerField('Цена')
    price_rrc = models.PositiveIntegerField('Рекомендуемая розничная цена')

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Список информации о продуктах'
        constraints = [
            UniqueConstraint(fields=['product', 'shop', 'external_id'], name='unique_product_info'),
        ]

    def __str__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField('Параметр', max_length=60)

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Список имён параметров'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name='Информация о продукте',
        related_name='product_parameters',
        blank=True,
        on_delete=models.CASCADE,
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name='Параметр',
        related_name='product_parameters',
        blank=True,
        on_delete=models.CASCADE,
    )
    value = models.CharField('Значение', max_length=80)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Cписок параметров'
        constraints = [
            UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='contacts',
        blank=True,
        on_delete=models.CASCADE,
    )
    city = models.CharField('Город', max_length=100)
    street = models.CharField('Улица', max_length=100)
    house = models.CharField('Дом', max_length=100, blank=True)
    structure = models.CharField('Корпус', max_length=100, blank=True)
    building = models.CharField('Строение', max_length=100, blank=True)
    apartment = models.CharField('Квартира', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=100)

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователя'

    def __str__(self):
        return f'{self.city} {self.street} {self.house} {self.apartment}'


class Order(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='orders',
        blank=True,
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)
    state = models.TextField(
        'Cтатус',
        choices=StatusOrders.choices,
        default=StatusOrders.NEW,
    )
    contact = models.ForeignKey(
        Contact,
        verbose_name='Контакт',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='orders',
        blank='True',
        on_delete=models.CASCADE,
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name='Информация о продукте',
        related_name='ordered_items',
        blank=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'
        constraints = [
            UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item')
        ]


class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь, связанный с этим токеном сброса пароля',
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField('Дата создания токена', auto_now_add=True)
    key = models.CharField('Ключ', max_length=64, db_index=True, unique=True)

    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Cписок токенов подтверждения Email'

    def __str__(self):
        return f'Токен сброса пароля для юзера {self.user}'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()