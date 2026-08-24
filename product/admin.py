from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .image_utils import MAX_PRODUCT_IMAGES
from .models import Category, Client_review, Offer, Product, ProductImage


class ProductImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(active_forms) > MAX_PRODUCT_IMAGES:
            raise ValidationError(f"A product can have a maximum of {MAX_PRODUCT_IMAGES} images.")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageInlineFormSet
    extra = 0
    max_num = MAX_PRODUCT_IMAGES
    fields = ("image", "display_order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'display_order')
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'category', 'price', 'quantity', 'is_available', 'is_visible', 'display_order')
    list_filter = ('category', 'is_available', 'is_visible')
    search_fields = ('name', 'description', 'name_ar', 'description_ar')
    inlines = (ProductImageInline,)


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
