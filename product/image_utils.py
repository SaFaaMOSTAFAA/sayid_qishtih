from django.db import transaction
from rest_framework import serializers

from .models import ProductImage

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_PRODUCT_IMAGES = 5
MAX_PRODUCT_IMAGES_ERROR = "A product can have a maximum of 5 images."
INVALID_REMOVE_IMAGE_IDS_ERROR = "One or more product images are invalid."


def validate_image_file(value):
    if value is None:
        return value

    content_type = getattr(value, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise serializers.ValidationError("Only JPEG, PNG, and WebP images are allowed.")

    size = getattr(value, "size", 0)
    if size and size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("Image size must not exceed 5 MB.")

    return value


def validate_uploaded_product_images(uploaded_images):
    if len(uploaded_images) > MAX_PRODUCT_IMAGES:
        raise serializers.ValidationError({"images": [MAX_PRODUCT_IMAGES_ERROR]})

    errors = []
    for uploaded_image in uploaded_images:
        try:
            validate_image_file(uploaded_image)
        except serializers.ValidationError as exc:
            errors.append(exc.detail)

    if errors:
        raise serializers.ValidationError({"images": errors})


def parse_remove_image_ids(values):
    remove_image_ids = []
    seen = set()
    for value in values:
        try:
            image_id = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError({"remove_image_ids": [INVALID_REMOVE_IMAGE_IDS_ERROR]})

        if image_id not in seen:
            seen.add(image_id)
            remove_image_ids.append(image_id)

    return remove_image_ids


def get_remove_image_ids(request):
    if hasattr(request.data, "getlist"):
        values = request.data.getlist("remove_image_ids")
    else:
        raw_value = request.data.get("remove_image_ids", [])
        values = raw_value if isinstance(raw_value, list) else [raw_value]

    return parse_remove_image_ids(values)


def validate_product_image_update(product, uploaded_images, remove_image_ids):
    matching_remove_count = ProductImage.objects.filter(product=product, id__in=remove_image_ids).count()
    if matching_remove_count != len(remove_image_ids):
        raise serializers.ValidationError({"remove_image_ids": [INVALID_REMOVE_IMAGE_IDS_ERROR]})

    final_count = product.images.count() - matching_remove_count + len(uploaded_images)
    if final_count > MAX_PRODUCT_IMAGES:
        raise serializers.ValidationError({"images": [MAX_PRODUCT_IMAGES_ERROR]})
    if final_count < 0:
        raise serializers.ValidationError({"remove_image_ids": [INVALID_REMOVE_IMAGE_IDS_ERROR]})


def create_product_images(product, uploaded_images):
    start_order = product.images.count()
    for offset, uploaded_image in enumerate(uploaded_images):
        ProductImage.objects.create(
            product=product,
            image=uploaded_image,
            display_order=start_order + offset,
        )


def normalize_product_image_order(product):
    for index, image in enumerate(product.images.order_by("display_order", "id")):
        if image.display_order != index:
            image.display_order = index
            image.save(update_fields=["display_order"])


def apply_product_image_update(product, uploaded_images, remove_image_ids):
    with transaction.atomic():
        if remove_image_ids:
            ProductImage.objects.filter(product=product, id__in=remove_image_ids).delete()
        create_product_images(product, uploaded_images)
        normalize_product_image_order(product)
