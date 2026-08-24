from django.contrib.auth import get_user_model
from product.models import Category, Client_review, Offer, Product, ProductImage
from rest_framework import serializers

from .image_utils import MAX_PRODUCT_IMAGES, validate_image_file

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ImageRemovalMixin:
    def validate_image(self, value):
        return validate_image_file(value)

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


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "display_order")
        read_only_fields = fields


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_ar",
            "description",
            "description_ar",
            "price",
            "category",
            "quantity",
            "is_visible",
            "is_available",
            "display_order",
            "images",
            "created_at",
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


class ProductMultipartRequestSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    name_ar = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False)
    description_ar = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    category = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(required=False, min_value=0)
    is_visible = serializers.BooleanField(required=False)
    is_available = serializers.BooleanField(required=False)
    display_order = serializers.IntegerField(required=False, min_value=0)
    images = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        max_length=MAX_PRODUCT_IMAGES,
        help_text='Upload images by repeating the multipart field "images".',
    )
    remove_image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='Remove existing images by repeating the multipart field "remove_image_ids".',
    )
