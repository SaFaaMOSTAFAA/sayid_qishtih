from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)

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
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True, db_index=True)
    is_available = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["display_order", "id"]


class Offer(models.Model):
    title = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    start_date = models.DateField(blank=True, null=True, db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_currently_active(self):
        return self.is_currently_active_for_date(timezone.localdate())

    def is_currently_active_for_date(self, date):
        starts_ok = self.start_date is None or self.start_date <= date
        ends_ok = self.end_date is None or self.end_date >= date
        return self.is_active and starts_ok and ends_ok

    @classmethod
    def currently_active_filter(cls, date=None):
        date = date or timezone.localdate()
        return (
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=date),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=date),
            models.Q(is_active=True),
        )

    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-created_at", "-id"]


class Client_review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_reviews",
    )
    review = models.TextField()
    review_ar = models.TextField(null=True, blank=True)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = "Client Review"
        verbose_name_plural = "Client Reviews"
        ordering = ["-created_at", "-id"]
