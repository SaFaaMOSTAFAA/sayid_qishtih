from django.db import migrations


def backfill_display_order_and_availability(apps, schema_editor):
    Category = apps.get_model("product", "Category")
    Product = apps.get_model("product", "Product")

    for index, category in enumerate(Category.objects.order_by("id")):
        Category.objects.filter(pk=category.pk).update(display_order=index)

    for index, product in enumerate(Product.objects.order_by("id")):
        updates = {"display_order": index}
        if product.quantity == 0:
            updates["is_available"] = False
        Product.objects.filter(pk=product.pk).update(**updates)


def reverse_backfill_display_order_and_availability(apps, schema_editor):
    Category = apps.get_model("product", "Category")
    Product = apps.get_model("product", "Product")

    Category.objects.update(display_order=0)
    Product.objects.update(display_order=0)


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0004_alter_client_review_options_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_display_order_and_availability,
            reverse_backfill_display_order_and_availability,
        ),
    ]
