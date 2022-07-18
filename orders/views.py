from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet

import yaml
from yaml.loader import SafeLoader

from .models import Shop, Category, ProductInfo, Order, OrderItem, Contact, ConfirmEmailToken
from .serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializerPatch, OrderSerializer, ContactSerializer, OrderItemSerializerGet, OrderItemSerializerPost
from .permission import IsAuthenticatedAndShop
from .tasks import token_postman, info_postman, import_yaml


def doc_view(request):
    return HttpResponseRedirect(reverse('swagger-ui'))


class AuthViewSet(ViewSet):
    """
    ViewSet for User authentication
    """

    @extend_schema(
        description='Registrate a new user',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        responses=UserSerializer,
        examples=[
            OpenApiExample(
                'Example 1',
                summary='registrate Foo Bar',
                description='all required fields are filled in, request will be done and'
                            'to your email send confirm token',
                value={
                    "first_name": "Foo",
                    "last_name": "Bar",
                    "email": "email@email.com",
                    "password": "Valid1Password",
                    "company": "MU",
                    "position": "Fw",
                    "type": "CLIENT"
                }
            ),
        ]
    )
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

    @extend_schema(
        description='Сonfirm registration a new user',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Сonfirm registration our user',
                description='all required fields are filled in, request will be done and your account will be active.'
                            'In the next u can log in.',
                value={
                    "email": "email",
                    "token": "TokenFromMail"
                }
            ),
        ]
    )
    @action(detail=False, methods=['POST'], name='Confirm registration')
    def confirm_registration(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            confirm = ConfirmEmailToken.objects.filter(user__email=request.data.get('email'),
                                                       key=request.data.get('token')).first()
            if confirm:
                confirm.user.is_active = True
                confirm.user.save()
                return JsonResponse({'Status': True, 'Description': 'Аккаунт активирован'})
            else:
                return JsonResponse({'Status': False,
                                     'Errors': 'Неправильно указан токен или email, аккаунт не активирован'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    @extend_schema(
        description='login account',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='login account',
                description='all required fields are filled in, request will be done and you will get AuthToken for'
                            'work with API',
                value={
                    "email": "use_ur_email",
                    "password": "use_ur_password"
                }
            ),
        ])
    @action(detail=False, methods=['POST'], name='Login')
    def login(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data.get('email'), password=request.data.get('password'))

            if user is not None and user.is_active:
                user = user
                token_postman.send_auth_token.delay(user.id)
                return JsonResponse({'Status': True, 'Token': 'send to email'})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class UserViewSet(ViewSet):
    """
    ViewSet for working with User
    """

    @extend_schema(description='Get info about your account. Auth only', responses=UserSerializer)
    def list(self, request, *args, **kwargs):

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        description='Change info about you. Auth only',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='change password',
                description='save it to your password manager',
                value={
                    "password": "new_password!"
                }
            ),
            OpenApiExample(
                'Example 2',
                summary='change company',
                description='Maybe you are change job',
                value={
                    "company": "Some Company"
                }
            ),
        ]
    )
    @action(detail=False, methods=['PATCH'])
    def change_info(self, request, *args, **kwargs):

        password = request.data.get('password')
        if password:
            try:
                validate_password(password)
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': str(error_array)}})
            else:
                request.user.set_password(password)
                request.data['password'] = 'closed info, remember ur new password please'

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            info_postman.send_change_user_info.delay(request.user.id, request.data)
            return JsonResponse({'Status': True, 'Update info': f'{request.data} is update'})
        else:
            return JsonResponse({'Status': False, 'Errors': str(user_serializer.errors)})


class ContactsViewSet(ViewSet):
    """
    ViewSet for working with User contacts
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            contact = Contact.objects.get(pk=pk)
            return contact
        except ObjectDoesNotExist:
            return Response(f'Status: False, Errors: u dont have contact by #{pk}')

    @extend_schema(description='Get your contacts. Auth only', responses=ContactSerializer)
    def list(self, request, *args, **kwargs):
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Add new contact. Auth only',
        responses=ContactSerializer,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='You can add any information. Used fields: city, street, house, structure, building,'
                        'apartment, phone',
                description='save it to your password manager',
                value={
                    "street": "FooBar street"
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        if len(request.data) == 0:
            return Response('Не указаны никакие данные')

        request.data.update({'user': request.user.id})
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': str(serializer.errors)})

    @extend_schema(description='Delete your contact by id. Auth only')
    def delete(self, request, pk):

        try:
            contact = self.get_object(pk)
            contact.delete()
            return JsonResponse({'Status': True, 'Ваш контакт': f'с id{pk} удален'})
        except:
            return JsonResponse({'Status': False, 'Description': 'Something went wrong'})

    @extend_schema(
        description='Change contact. Auth only, by id',
        responses=ContactSerializer,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Change some info in contact. Use id contact for it',
                description='change anything',
                value={
                    "street": "Xyz street"
                }
            )
        ]
    )
    def partial_update(self, request, pk):
        contact = self.get_object(pk)
        serializer = ContactSerializer(contact, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"Status": True, "New data": str(serializer.data)})

        return JsonResponse({"Status": False, "Errors": str(serializer.errors)})


class SellerViewSet(ViewSet):
    """
    Viewset for working with sellers orders and prices
    """

    permission_classes = [IsAuthenticatedAndShop]

    @extend_schema(
        description='See orders in shop',
        responses=OrderSerializer,
    )
    def list(self, request, *args, **kwargs):

        order = Order.objects.filter(
            orders__product_info__shop__user_id=request.user.id).exclude(state='BASKET').prefetch_related(
            'orders__product_info__product__category',
            'orders__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('orders__quantity') * F('orders__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Upload/update positions in your price-list',
        operation_id='upload_file',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
    )
    def create(self, request, *args, **kwargs):
        try:
            file = request.data['file']
            user_id = request.user.id
            data = yaml.load(file, SafeLoader)
            import_yaml.delay(user_id, data)
            return JsonResponse({"Status": True, "Price is update": data['shop']})
        except KeyError:
            raise ParseError('Request has no resource file attached')


class SellersShopsViewSet(ViewSet):
    """
    Viewset for working with sellers shops
    """

    permission_classes = [IsAuthenticatedAndShop]

    @extend_schema(
        description='Get info about shop',
        responses=ShopSerializer,
    )
    def list(self, request, *args, **kwargs):

        try:
            shop = request.user.shop
            serializer = ShopSerializer(shop)
            return JsonResponse({"Status": True, "Shop": serializer.data})

        except ObjectDoesNotExist:
            return JsonResponse({"Status": False, "Description": "That's user dont have a shop"})

    @extend_schema(
        description='Change shop status',
        responses=ShopSerializer,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Change status to False',
                description=f"It's mean that shop dont work",
                value={
                    "state": False
                }
            ),
        ]
    )
    def partial_update(self, request, pk=None, *args, **kwargs):

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=state)
                return JsonResponse({'Status': True, 'State': state})
            except ValidationError as error:
                return JsonResponse({"Status": False, "Errors": str(error)})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ReadOnlyModelViewSet):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class ShopView(ReadOnlyModelViewSet):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]


class ProductInfoView(ReadOnlyModelViewSet):
    """
    Класс для поиска товаров с возможностью поиска по имени
    """
    queryset = ProductInfo.objects.all().select_related('shop', 'product__category'). \
        prefetch_related('product_parameters__parameter').distinct()
    serializer_class = ProductInfoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name", "product__name", ]


class ShoppingCartViewSet(ViewSet):
    """
    Viewset for working with buyer basket
    """

    permission_classes = [IsAuthenticated]

    # Method for get obj from SC by id, used in another class methods
    def get_object(self, request, pk):

        try:
            return OrderItem.objects.filter(order__user=request.user.id, id=pk, order__state='BASKET').annotate(
                total_sum_position=Sum(F('quantity') * F('product_info__price')))
        except ObjectDoesNotExist:
            return JsonResponse({"Status": False, "Errors": f"u dont have item with id{pk}"})

    @extend_schema(
        description='Get your shopping cart',
        responses=OrderItemSerializerGet
    )
    def list(self, request, *args, **kwargs):

        queryset = OrderItem.objects.filter(order__user=request.user.id, order__state='BASKET').annotate(
            total_sum_position=Sum(F('quantity') * F('product_info__price')))
        serializer = OrderItemSerializerGet(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Add position to shop-cart',
        responses=OrderItemSerializerPost,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Add new item in SC',
                description='For that action you are need to know: ID-product_info and paste desired quantity',
                value={
                    "product_info_id": 37,
                    "quantity": 10
                }
            ),
        ]
    )
    def create(self, request, *args, **kwargs):

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
                return JsonResponse({"Status": True, "Description": serializer.data})

        except IntegrityError as errors:
            return JsonResponse({"Status": False, "Errors": str(errors)})

        return JsonResponse({'Status': False, 'Errors': serializer.errors})

    @extend_schema(
        description='Get info about product by id',
        responses=OrderItemSerializerGet
    )
    def retrieve(self, request, pk, *args, **kwargs):

        product = self.get_object(request, pk).distinct()
        if product:
            serializer = OrderItemSerializerGet(product, many=True)
            return JsonResponse({"Status": True, "Description": serializer.data})
        else:
            return JsonResponse({"Status": False, "Description": f"Позиции с id{pk} в корзине нет"})

    @extend_schema(
        description='Change quantity for item in SC',
        responses=OrderItemSerializerPatch,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Change quantity',
                description='Change for available quantity',
                value={
                    "quantity": 2
                }
            ),
        ]
    )
    def partial_update(self, request, pk, *args, **kwargs):

        item = self.get_object(request, pk).first()

        try:
            available_qnt = ProductInfo.objects.get(product__name=item.product_info.product.name).quantity
        except AttributeError as er:
            return JsonResponse({"Status": False, "Errors": str(er)})

        try:
            if int(request.data.get('quantity')) <= available_qnt:
                try:
                    serializer = OrderItemSerializerPatch(item, data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({"Status": True, "Description": serializer.data})
                except IntegrityError as er:
                    return JsonResponse({"Status": False, "Errors": str(er)})
            else:
                return JsonResponse({"Status": False, "Error": f'Available qnty {available_qnt} '
                                                               f'less then request {request.data["quantity"]}'})
        except ValueError as ve:
            return JsonResponse({"Status": False, "Errors": str(ve)})

    @extend_schema(description='Delete position by id')
    def destroy(self, request, pk, *args, **kwargs):

        info = self.get_object(request, pk)
        info.delete()
        return JsonResponse({'Status': True, 'Позиция': f'с id{pk} удалена'})


class OrderViewSet(ViewSet):
    """
    Класс для получения и размешения заказов пользователями
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description='Get my orders',
        responses=OrderSerializer
    )
    def list(self, request, *args, **kwargs):

        order = Order.objects.filter(user_id=request.user.id).exclude(state='BASKET').annotate(
            total_sum=Sum(F('orders__quantity') * F('orders__product_info__price')))

        try:
            serializer = OrderSerializer(order, many=True)
            return Response(serializer.data)
        except IntegrityError as er:
            return Response(str(er))

    @extend_schema(
        description='Change status from "Shopping cart" to "Order"',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example 1',
                summary='Change status of order from BASKET to NEW',
                description="Indicate ID's order and contact for success",
                value={
                    "contact_id": "10"
                }
            ),
        ]
    )
    def partial_update(self, request, pk, *args, **kwargs):

        if {'contact_id'}.issubset(request.data):
            try:
                Order.objects.filter(user_id=request.user.id, pk=pk).update(
                    contact_id=request.data['contact_id'], state='NEW')
                info_postman.new_order.delay(request.user.id, request.data)
                return JsonResponse({'Status': True, 'Description': f'Order with {request.data} change status to NEW'})
            except IntegrityError as error:
                return JsonResponse({'Status': False, 'Errors': error})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
