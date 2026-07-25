from django.contrib.auth import get_user_model
from rest_framework import serializers

from product.models import Category, Client_review, Offer, Product

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "name_ar", "display_order")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_ar",
            "description",
            "description_ar",
            "price",
            "image",
            "category",
            "quantity",
            "is_visible",
            "is_available",
            "display_order",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        quantity = attrs.get("quantity")
        if quantity is None and self.instance is not None:
            quantity = self.instance.quantity

        if quantity is not None and quantity == 0:
            attrs["is_available"] = False
        return attrs


class OfferSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Offer
        fields = (
            "id",
            "title",
            "title_ar",
            "description",
            "description_ar",
            "image",
            "is_active",
            "start_date",
            "end_date",
            "is_currently_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "is_currently_active")

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be on or after start date."}
            )
        return attrs


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "full_name")


class ClientReviewSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Client_review
        fields = ("id", "user", "review", "review_ar", "rating", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class DashboardStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    available_products = serializers.IntegerField()
    unavailable_products = serializers.IntegerField()
    current_offers = serializers.IntegerField()
