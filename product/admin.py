from django.contrib import admin
from .models import Category, Product, Client_review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar')
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'category', 'price', 'image', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description', 'name_ar', 'description_ar')
    prepopulated_fields = {'slug': ('name',)}
    

@admin.register(Client_review)
class ClientReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'review', 'review_ar', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name', 'name_ar', 'review', 'review_ar')
