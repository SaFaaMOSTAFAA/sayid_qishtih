from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0007_copy_product_images"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="image",
        ),
    ]
