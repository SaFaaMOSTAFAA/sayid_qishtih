from django.shortcuts import render

from .models import Product, Category, Client_review
from .serializer import ProductSerializer, CategorySerializer, ClientReviewSerializer
from rest_framework.viewsets import ModelViewSet

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ClientReviewViewSet(ModelViewSet):
    queryset = Client_review.objects.all()
    serializer_class = ClientReviewSerializer
