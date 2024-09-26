# Generated by Django 4.2.1 on 2023-06-12 03:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0004_alter_site_workers"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="workersite",
            constraint=models.UniqueConstraint(
                fields=("worker", "site"), name="unique_worker_site"
            ),
        ),
    ]
