from django.contrib import admin
from .models import Category, Product, Client_review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar')
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'category', 'price', 'image')
    list_filter = ('category',)
    search_fields = ('name', 'description', 'name_ar', 'description_ar')
    

@admin.register(Client_review)
class ClientReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'review_ar', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'review',
        'review_ar',
    )
