import pytest
import uuid
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from model_bakery import baker
from EShops_API.celery import app


# Password for test-user
@pytest.fixture
def test_password():
    return 'Hello-World!'


# Email for test-user
@pytest.fixture
def test_email():
    return 'tes12t@test.com'


@pytest.fixture
def type_user_shop():
    return 'SHOP'


# Create test user
@pytest.fixture
def create_user(db, django_user_model, test_password, test_email):
    def make_user(**kwargs):
        kwargs['password'] = test_password
        kwargs['email'] = test_email
        kwargs['is_active'] = True
        if 'username' not in kwargs:
            kwargs['username'] = str(uuid.uuid4())
        return django_user_model.objects.create_user(**kwargs)

    return make_user


# Create test user with type SHOP
@pytest.fixture
def create_user_shop(db, django_user_model, test_password, test_email, type_user_shop):
    def make_user_shop(**kwargs):
        kwargs['password'] = test_password
        kwargs['email'] = test_email
        kwargs['is_active'] = True
        kwargs['type'] = type_user_shop
        if 'username' not in kwargs:
            kwargs['username'] = str(uuid.uuid4())
        return django_user_model.objects.create_user(**kwargs)

    return make_user_shop


# Create auth-token for test user
@pytest.fixture
def get_or_create_token(db, create_user):
    user = create_user()
    token, _ = Token.objects.get_or_create(user=user)
    return token


# Create auth-token for test user-shop
@pytest.fixture
def get_or_create_token_shop(db, create_user_shop):
    user = create_user_shop()
    token, _ = Token.objects.get_or_create(user=user)
    return token


# Create APIClient instance
@pytest.fixture
def client():
    return APIClient()


# Fixture for make a celery locally
@pytest.fixture(scope='module')
def celery_app(request):
    app.conf.update(CELERY_ALWAYS_EAGER=True)
    return app


# Create random shops
@pytest.fixture
def shops_factory():
    def factory(**kwargs):
        return baker.make("Shop", **kwargs)

    return factory


# Create random products
@pytest.fixture
def products_factory():
    def factory(**kwargs):
        return baker.make("Product", make_m2m=True, **kwargs)

    return factory


# Create random products
@pytest.fixture
def category_factory():
    def factory(**kwargs):
        return baker.make("Category", make_m2m=True, **kwargs)

    return factory


# Create random info for products
@pytest.fixture
def product_info_factory():
    def factory(**kwargs):
        return baker.make("ProductInfo", make_m2m=True, **kwargs)

    return factory

# Create OrderItems
@pytest.fixture
def order_items_factory():
    def factory(**kwargs):
        return baker.make("OrderItem", make_m2m=True, **kwargs)

    return factory

# Create random Order
@pytest.fixture
def order_factory():
    def factory(**kwargs):
        return baker.make("Order", make_m2m=True, **kwargs)

    return factory
