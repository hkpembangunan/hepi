# Generated by Django 4.2.1 on 2023-06-13 05:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0008_alter_site_workers"),
    ]

    operations = [
        migrations.AddField(
            model_name="helmet",
            name="identifier",
            field=models.CharField(
                blank=True, default=None, max_length=50, null=True, unique=True
            ),
        ),
    ]
