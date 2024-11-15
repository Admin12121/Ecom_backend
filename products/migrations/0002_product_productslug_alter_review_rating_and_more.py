# Generated by Django 4.2.11 on 2024-07-02 13:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="productslug",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="review",
            name="rating",
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["id", "product_name"], name="products_pr_id_5eaa13_idx"
            ),
        ),
    ]
