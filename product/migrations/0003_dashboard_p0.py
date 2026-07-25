import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0002_normalize_client_review"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["display_order", "id"],
                "verbose_name": "Category",
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.AlterModelOptions(
            name="product",
            options={
                "ordering": ["display_order", "-created_at"],
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
            },
        ),
        migrations.AddField(
            model_name="category",
            name="display_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="product",
            name="display_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="product",
            name="is_available",
            field=models.BooleanField(
                default=True, help_text="False means Out of Stock"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_visible",
            field=models.BooleanField(
                default=True, help_text="Hide/show product on the storefront"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="quantity",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="product.category",
            ),
        ),
        migrations.CreateModel(
            name="Offer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("title_ar", models.CharField(blank=True, max_length=255, null=True)),
                ("description", models.TextField(blank=True)),
                ("description_ar", models.TextField(blank=True, null=True)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="offers/"),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Offer",
                "verbose_name_plural": "Offers",
                "ordering": ["-created_at"],
            },
        ),
    ]
