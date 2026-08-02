from django.contrib.auth import get_user_model
from product.models import Category, Client_review, Offer, Product
from rest_framework import serializers

User = get_user_model()
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ImageRemovalMixin:
    def validate_image(self, value):
        if value is None:
            return value

        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise serializers.ValidationError("Only JPEG, PNG, and WebP images are allowed.")

        size = getattr(value, "size", 0)
        if size and size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Image size must not exceed 5 MB.")

        return value

    def _update_image(self, instance, validated_data):
        remove_image = validated_data.pop("remove_image", False)
        new_image = validated_data.get("image")
        old_image = instance.image

        if remove_image:
            if old_image:
                old_image.delete(save=False)
            instance.image = None
            validated_data.pop("image", None)
            return

        if new_image and old_image and old_image.name != new_image.name:
            old_image.delete(save=False)

    def create(self, validated_data):
        validated_data.pop("remove_image", None)
        return super().create(validated_data)


class ProductSerializer(ImageRemovalMixin, serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)

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
            "remove_image",
        )
        read_only_fields = ("id", "created_at")

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Ensure this value is greater than or equal to 0.")
        return value

    def validate(self, attrs):
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        if quantity == 0:
            attrs["is_available"] = False
        return attrs

    def update(self, instance, validated_data):
        self._update_image(instance, validated_data)
        return super().update(instance, validated_data)


class OfferSerializer(ImageRemovalMixin, serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)
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
            "remove_image",
        )
        read_only_fields = ("id", "is_currently_active", "created_at")

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be greater than or equal to start date."
            })
        return attrs

    def update(self, instance, validated_data):
        self._update_image(instance, validated_data)
        return super().update(instance, validated_data)


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "full_name", "is_staff")


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

    def validate_review(self, value):
        if not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value


class DashboardStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    available_products = serializers.IntegerField()
    unavailable_products = serializers.IntegerField()
    current_offers = serializers.IntegerField()
