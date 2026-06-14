from django.contrib import admin
from .models import Category, Product, Client_review

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Client_review)
