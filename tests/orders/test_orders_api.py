import json
import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND


def test_how_u_do():
    assert True


@pytest.mark.django_db
def test_shop_view(client, get_or_create_token, shops_factory):
    """
    In this test create a random quantity of shops and check it by listview
    """
    shops = shops_factory(_quantity=5)
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    url = reverse('orders:shops-list')
    response = client.get(url)

    assert response.status_code == HTTP_200_OK
    assert len(response.data['results']) == 5


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
    token = get_or_create_token
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    url = reverse('orders:product_info')
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
