import json
import random
import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


def test_how_u_do():
    assert True


@pytest.mark.django_db
def test_shop_view(client, get_or_create_token, shops_factory):
    """
    In this test create a random quantity of shops and check length
    """
    qnt = random.randrange(1, 10)
    shops = shops_factory(_quantity=qnt)
    url = reverse('orders:shops-list')
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert len(response.data['results']) == qnt


@pytest.mark.django_db
def test_category_view(client, get_or_create_token, category_factory):
    """
    In this test create a random quantity of categories and check length
    """
    qnt = random.randrange(1, 10)
    category = category_factory(_quantity=qnt)
    url = reverse('orders:category-list')
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert len(response.data['results']) == qnt


@pytest.mark.parametrize(
    ["category_name", "product_name", "text", "length"],
    (
        (['Phones', 'Vegetables', 'Toys'], ['Iphone', 'Cucumber', 'Lego'], 'CUM', 1),
        (['Phones', 'Vegetables', 'Toyses'], ['Iphone', 'Cucumber', 'Lego'], 'Es', 3)
    )
)
@pytest.mark.django_db
def test_product_info_view(category_name, product_name, text, length, client, get_or_create_token, shops_factory,
                           category_factory, products_factory, product_info_factory):
    data = {"text": text}
    # make categories with names from our list
    category = category_factory(_quantity=3, name=iter(category_name))
    # make shops
    shops = shops_factory(_quantity=4)
    # make products with names from our list and set a category for each
    products = products_factory(_quantity=3, name=iter(product_name), category=iter(category))
    # make products_info list and set a shop and product for each
    products_info = product_info_factory(_quantity=3, shop=iter(shops), product=iter(products))
    url = reverse('orders:product_info')
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.generic(method="GET", path=url, data=json.dumps(data),
                              content_type='application/json')

    assert response.status_code == HTTP_200_OK
    assert len(response.data) == length


@pytest.mark.django_db
def test_user_info_view(client, get_or_create_token, test_email):
    """
    In this test check available info about user(API Client)
    """
    url = reverse('orders:user-user-info')
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert response.data['email'] == test_email


@pytest.mark.parametrize(
    "email , password, excepted_response_status",
    [
        ('admin@admin.ru', '', True),
        ('admin@', '', False),
        ('', 's', False),
        ('admin@admin.ru', 'Somebode-password-Good', True)
    ]
)
@pytest.mark.django_db
def test_change_user_info(celery_app, email, password, excepted_response_status, client, get_or_create_token):
    """
    In this test check how workin email and password validators in view
    """
    data = {
        "email": email,
        "password": password
    }
    url = reverse('orders:user-change-user-info')
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.post(url, data=data)

    assert response.status_code == HTTP_200_OK
    assert response.json()['Status'] == excepted_response_status


@pytest.mark.django_db
def test_shop_info_true(client, get_or_create_token_shop, shops_factory):
    """
    In this test we get a user.id for shop, excepted status True
    """
    url = reverse('orders:partner-shop-info')
    token = get_or_create_token_shop
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    shop = shops_factory(_quantity=1, user=token.user)
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert response.json()['Status'] == True


@pytest.mark.django_db
def test_shop_info_false(client, get_or_create_token_shop, shops_factory):
    """
    In this test we didn't get a user.id for shop, excepted status False
    """
    shop = shops_factory(_quantity=1)
    url = reverse('orders:partner-shop-info')
    token = get_or_create_token_shop
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert response.json()['Status'] == False


@pytest.mark.parametrize(
    "state, excepted_status",
    [
        (True, True),
        (False, True),
        ('asd', False)
    ]

)
@pytest.mark.django_db
def test_change_shop_status(state, excepted_status, client, get_or_create_token_shop, shops_factory):
    """
    In this test we change status of shop and check results
    """
    data = {
        "state": state
    }
    url = reverse('orders:partner-change-shop-status')
    token = get_or_create_token_shop
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    shop = shops_factory(_quantity=1, user=token.user)
    response = client.post(url, data=data)

    assert response.status_code == HTTP_200_OK
    assert response.json()['Status'] == excepted_status


@pytest.mark.parametrize(
    ["category_name", "product_name", "quantity", "price", "price_rrc"],
    (
        (['Phones', 'Vegetables', 'Toys'], ['Iphone', 'Cucumber', 'Lego'], 4,
         random.randrange(200, 500), random.randrange(500, 600)),
        (['Phones', 'Vegetables', 'Toyses'], ['Iphone', 'Cucumber', 'Lego'], 7,
         random.randrange(50, 100), random.randrange(200, 250))
    )
)
@pytest.mark.django_db
def test_basket(category_name, product_name, quantity, price, price_rrc, client, get_or_create_token, category_factory,
                order_items_factory, order_factory, product_info_factory, products_factory, shops_factory):
    token = get_or_create_token
    # make categories with names from our list
    category = category_factory(_quantity=3, name=iter(category_name))
    # make shops
    shops = shops_factory(_quantity=4)
    # make products with names from our list and set a category for each
    products = products_factory(_quantity=3, name=iter(product_name), category=iter(category))
    # make products_info list and set a shop and product for each
    products_info = product_info_factory(_quantity=3, shop=iter(shops), product=iter(products), price=price,
                                         price_rrc=price_rrc)
    # create order
    order = order_factory(_quantity=3, user=token.user, state='BASKET')
    # create ordered items
    order_items = order_items_factory(_quantity=3, order=iter(order), product_info=iter(products_info),
                                      quantity=quantity)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    url = reverse("orders:shopping_cart-basket")
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert len(response.data) == 3


@pytest.mark.parametrize(
    ["category_name", "product_name", "quantity", "price", "price_rrc", "product_info_id", "order_id"],
    (
        (['Phones', 'Vegetables', 'Toys'], ['Iphone', 'Cucumber', 'Lego'], 4,
         random.randrange(200, 500), random.randrange(500, 600), 2, 1),
        (['Phones', 'Vegetables', 'Toyses'], ['Iphone', 'Cucumber', 'Lego'], 7,
         random.randrange(50, 100), random.randrange(200, 250), 5, 1)
    )
)
@pytest.mark.django_db
def test_add_position(category_name, product_name, quantity, price, price_rrc, product_info_id, order_id, client,
                      get_or_create_token, order_factory, category_factory, shops_factory, products_factory,
                      product_info_factory):
    token = get_or_create_token
    # create order
    order = order_factory(_quantity=1, user=token.user, state='BASKET')
    category = category_factory(_quantity=3, name=iter(category_name))
    # make shops
    shops = shops_factory(_quantity=4)
    # make products with names from our list and set a category for each
    products = products_factory(_quantity=3, name=iter(product_name), category=iter(category))
    # make products_info list and set a shop and product for each
    products_info = product_info_factory(_quantity=3, shop=iter(shops), product=iter(products), price=price,
                                         price_rrc=price_rrc)
    print(products_info)

    data = {
        "order": order_id,
        "product_info_id": product_info_id,
        "quantity": quantity
    }
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    url = reverse("orders:shopping_cart-add-position")
    response = client.post(url, data=data)

    print(response.json())

    assert response.status_code == HTTP_200_OK
    assert response.json()["Status"] == True
    assert response.json()["Description"]["product_info"] == product_info_id
