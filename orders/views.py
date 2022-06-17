from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
import yaml
from rest_framework.viewsets import ViewSet
from yaml.loader import SafeLoader

from .models import Shop, Category, ProductInfo, Order, OrderItem, Contact, ConfirmEmailToken
from .serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializerPatch, OrderSerializer, ContactSerializer, OrderItemSerializerGet, OrderItemSerializerPost
from .tasks import token_postman, info_postman, import_yaml


class UserViewSet(ViewSet):
    """
    ViewSet for working with User functions
    """
    def get_object(self, pk):
        try:
            return Contact.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(f'Status: False, Errors: u dont have contact by #{pk}')

    """
    Регистрация пользователя
    """
    @action(detail=False, methods=['POST'], name='New registration')
    def registration(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', 'type'}.issubset(request.data):

            # проверяем пароль на сложность

            try:
                validate_password(request.data.get('password'))
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data.get('password'))
                    user.save()
                    token_postman.send_confirm_token.delay(user.id)

                    return JsonResponse({'Status': True, 'Info': 'To your email send confirm token'})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    """
    Подтверждение регистрации, активация аккаунта
    """
    @action(detail=False, methods=['POST'], name='Confirm registration')
    def confirm_registration(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            queryset = ConfirmEmailToken.objects.filter(user__email=request.data.get('email'),
                                                        key=request.data.get('token')).first()
            if queryset:
                queryset.user.is_active = True
                queryset.user.save()
                return JsonResponse({'Status': 'Аккаунт активирован'})
            else:
                return JsonResponse({'Status': False,
                                     'Errors': 'Неправильно указан токен или email, аккаунт не активирован'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    """
    Авторизация пользователя
    """
    @action(detail=False, methods=['POST'], name='Login')
    def login_account(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data.get('email'), password=request.data.get('password'))

            if user is not None and user.is_active:
                user = user
                token_postman.delay(user.id)
                return JsonResponse({'Status': True, 'Token': 'send to email'})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    """
    Получить информацию пользователя
    """
    @action(detail=False, methods=['GET'], name='User information')
    def user_info(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    """
    Редактировать информацию пользователя
    """
    @action(detail=False, methods=['POST'], name='Change user-info')
    def change_user_info(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        # проверяем обязательные аргументы

        password = request.data.get('password')
        if password:
            # проверяем пароль на сложность
            try:
                validate_password(password)
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(password)
                request.data['password'] = 'closed info, remember ur new password please'

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            info_postman.send_change_user_info.delay(request.user.id, request.data)
            return JsonResponse({'Status': f'{request.data} is update'})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

    """
    Получить список контактов пользователей
    """
    @action(detail=False, methods=['GET'], name='List of user contacts')
    def user_contacts(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    """
    Добавить новый контакт
    """
    @action(detail=False, methods=['POST'], name='Add new contact')
    def add_user_contact(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if len(request.data) == 0:
            return Response('Не указаны никакие данные')

        request.data.update({'user': request.user.id})
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': serializer.errors})

    """
    Удалить контакт
    """
    @action(detail=True, methods=['DELETE'], name='Delete contact')
    def delete_user_contact(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        info = self.get_object(pk)
        info.delete()
        return JsonResponse({'Status': True, 'Ваши данные': f'с #{pk} удалены'})

    """
    Редактировать контакт 
    """
    @action(detail=True, methods=['PUT'], name='Change contact')
    def change_user_contact(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        contact = self.get_object(pk)
        serializer = ContactSerializer(contact, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerFunctionsViewSet(ViewSet):
    """
    Viewset for working with User SHOP status
    """

    """
    Получить информацию о магазине
    """
    @action(detail=False, methods=['GET'], name='Get info about shop')
    def shop_info(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'SHOP':
            return JsonResponse({'Status': False, 'Error': 'not permission'}, status=403)

        try:
            shop = request.user.shop
            serializer = ShopSerializer(shop)
            return Response(serializer.data)

        except ObjectDoesNotExist:
            return Response("That's user dont have a shop")

    """
    Изменить статус магазина
    """
    @action(detail=False, methods=['POST'], name='Change shop status')
    def change_shop_status(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'SHOP':
            return JsonResponse({'Status': False, 'Error': 'not permission'}, status=403)

        state = request.data.get('state')
        if state is not None:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=state)
                return JsonResponse({'Status': 'OK', 'State': state})
            except ValidationError as error:
                return Response(f'Status: False, Errors: {error}')

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    """
    Загрузить/добавить позиции для прайса
    """
    @action(detail=False, methods=['POST'], name='Add price')
    def add_price(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'SHOP':
            return JsonResponse({'Status': False, 'Error': 'not permission'}, status=403)

        try:
            file = request.data['file']
            user_id = request.user.id
            data = yaml.load(file, SafeLoader)
            import_yaml.delay(user_id, data)
            return Response(f"{data['shop']} price update")

        except KeyError:
            raise ParseError('Request has no resource file attached')

    """
    Посмотреть заказы в магазине
    """
    @action(detail=False, methods=['GET'], name='See orders by buyers')
    def users_orders(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'SHOP':
            return JsonResponse({'Status': False, 'Error': 'not permission'}, status=403)

        order = Order.objects.filter(
            orders__product_info__shop__user_id=request.user.id).exclude(state='BASKET').prefetch_related(
            'orders__product_info__product__category',
            'orders__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('orders__quantity') * F('orders__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Класс для поиска товаров
    """

    def get(self, request, *args, **kwargs):
        queryset = ProductInfo.objects.filter(
            Q(product__name__icontains=request.data['text']) | Q(
                product__category__name__icontains=request.data['text'])
        ).select_related('shop', 'product__category').prefetch_related('product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class ShoppingCartViewSet(ViewSet):
    """
    Viewset for working with buyer basket
    """

    # Method for get obj from SC by id, used in another class methods
    def get_object(self, request, pk):

        try:
            return OrderItem.objects.filter(order__user=request.user.id, id=pk, order__state='BASKET').annotate(
                total_sum_position=Sum(F('quantity') * F('product_info__price')))
        except ObjectDoesNotExist:
            return Response(f'Status: False, Errors: u dont have item with id{pk}')

    """
    Получить корзину пользователя
    """
    @action(detail=False, methods=['GET'], name='See shopping cart')
    def basket(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        queryset = OrderItem.objects.filter(order__user=request.user.id, order__state='BASKET').annotate(
            total_sum_position=Sum(F('quantity') * F('product_info__price')))
        serializer = OrderItemSerializerGet(queryset, many=True)
        return Response(serializer.data)

    """
    Добавить позицию в корзину
    """
    @action(detail=False, methods=['POST'], name='Add new position to shopping cart')
    def add_position(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if len(request.data) <= 0:
            return JsonResponse({"Status": False, "Error": "Не указаны никакие данные"})

        order_id = Order.objects.get(user=request.user.id, state='BASKET').id
        product_info_id = request.data.get('product_info_id')
        quantity = request.data.get('quantity')

        data = {
            "order": order_id,
            "product_info": product_info_id,
            "quantity": quantity
        }

        try:
            serializer = OrderItemSerializerPost(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data)

        except IntegrityError as errors:
            return Response(str(errors))

        return JsonResponse({'Status': False, 'Errors': serializer.errors})

    """
    Получить информацию по конкретному продукту в корзине
    """
    @action(detail=True, methods=['GET'], name='See info about product')
    def product_info(self, request, pk, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        queryset = self.get_object(request, pk).distinct()
        if queryset:
            serializer = OrderItemSerializerGet(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response(f'Позиции с id{pk} в корзине нет')

    """
    Изменение количества конкретного товара в корзине
    """
    @action(detail=True, methods=['PATCH'], name='Change quantity for position')
    def change_quantity(self, request, pk, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        item = self.get_object(request, pk).first()

        try:
            available_qnt = ProductInfo.objects.get(product__name=item.product_info.product.name).quantity
        except AttributeError as er:
            return Response(str(er))

        try:
            if int(request.data.get('quantity')) <= available_qnt:
                try:
                    serializer = OrderItemSerializerPatch(item, data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                except IntegrityError as er:
                    return Response(str(er))
            else:
                return Response(f'Available qnty {available_qnt} less then request {request.data["quantity"]}')
        except ValueError as ve:
            return Response(str(ve))

    """
    Удалить конкретную позицию в корзине
    """
    @action(detail=True, methods=['DELETE'], name='Delete position from shopping cart')
    def delete_position(self, request, pk, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        info = self.get_object(request, pk)
        info.delete()
        return JsonResponse({'Status': True, 'Позиция': f'с id{pk} удалена'})


class OrderViewSet(ViewSet):
    """
    Класс для получения и размешения заказов пользователями
    """

    """
    Просмотреть заказы покупателей
    """
    @action(detail=False, methods=['GET'], name='See orders of buyers')
    def get_orders(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        order = Order.objects.filter(user_id=request.user.id).exclude(state='BASKET').annotate(
            total_sum=Sum(F('orders__quantity') * F('orders__product_info__price')))

        try:
            serializer = OrderSerializer(order, many=True)
            return Response(serializer.data)
        except IntegrityError as er:
            return Response(str(er))

    """
    Создать заказ из корзины
    """
    @action(detail=False, methods=['POST'], name='Create new order')
    def new_order(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'order_id', 'contact_id'}.issubset(request.data):
            if request.data['order_id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, pk=request.data['order_id']).update(
                        contact_id=request.data['contact_id'],
                        state='NEW')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        info_postman.new_order.delay(request.user.id, request.data)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
