from rest_framework import serializers

from .models import User, Category, Shop, ProductInfo, Product, ProductParameter, OrderItem, Order, Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts', 'type')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class ProductInfoOrderItemGet(ProductInfoSerializer):
    class Meta:
        model = ProductInfo
        fields = ('name',)


class OrderItemSerializerGet(serializers.ModelSerializer):
    product_info = ProductInfoOrderItemGet()
    total_sum_position = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product_info', 'quantity', 'total_sum_position')
        read_only_fields = ('id', 'order')


class OrderItemSerializerPost(serializers.ModelSerializer):

    def create(self, validated_data):
        return OrderItem.objects.create(**validated_data)

    class Meta:
        model = OrderItem
        fields = ('id', 'quantity', 'order', 'product_info')
        read_only_fields = ('id',)


class OrderItemSerializerPatch(OrderItemSerializerGet):
    class Meta:
        model = OrderItem
        fields = ('id', 'quantity')
        read_only_fields = ('id',)


class UserOrderGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class OrderSerializer(serializers.ModelSerializer):
    total_sum = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ('id', 'user', 'total_sum')
        read_only_fields = ('id',)
