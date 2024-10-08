# Generated by Django 4.2.1 on 2023-07-30 19:40

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0033_workerrecord_id_alter_workerrecord_timestamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workerrecord",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
