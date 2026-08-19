from django.contrib import admin
from .models import Category, Client_review, Offer, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'display_order')
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'category', 'price', 'quantity', 'is_available', 'is_visible', 'display_order', 'image')
    list_filter = ('category', 'is_available', 'is_visible')
    search_fields = ('name', 'description', 'name_ar', 'description_ar')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'start_date', 'end_date', 'created_at')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title', 'title_ar', 'description', 'description_ar')
    

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
