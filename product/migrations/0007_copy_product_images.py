from django.db import migrations


def copy_product_images(apps, schema_editor):
    Product = apps.get_model("product", "Product")
    ProductImage = apps.get_model("product", "ProductImage")

    for product in Product.objects.exclude(image="").exclude(image__isnull=True).iterator():
        image_name = product.image.name
        if not image_name:
            continue
        ProductImage.objects.get_or_create(
            product_id=product.id,
            image=image_name,
            defaults={"display_order": 0},
        )


def reverse_copy_product_images(apps, schema_editor):
    Product = apps.get_model("product", "Product")
    ProductImage = apps.get_model("product", "ProductImage")

    for product in Product.objects.filter(image="").iterator():
        first_image = ProductImage.objects.filter(product_id=product.id).order_by("display_order", "id").first()
        if first_image:
            Product.objects.filter(pk=product.pk).update(image=first_image.image.name)


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0006_productimage"),
    ]

    operations = [
        migrations.RunPython(copy_product_images, reverse_copy_product_images),
    ]
