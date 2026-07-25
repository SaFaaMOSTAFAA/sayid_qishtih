from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["display_order", "id"]


class Product(models.Model):
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    description_ar = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True, related_name="products"
    )
    quantity = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True, help_text="Hide/show product on the storefront")
    is_available = models.BooleanField(
        default=True, help_text="False means Out of Stock"
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["display_order", "-created_at"]


class Offer(models.Model):
    title = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="offers/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_currently_active(self) -> bool:
        if not self.is_active:
            return False
        today = timezone.localdate()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True

    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-created_at"]


class Client_review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_reviews",
    )
    review = models.TextField()
    review_ar = models.TextField(null=True, blank=True)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = "Client Review"
        verbose_name_plural = "Client Reviews"
