from product.models import Category, Product, Client_review
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ClientReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client_review
        fields = '__all__'