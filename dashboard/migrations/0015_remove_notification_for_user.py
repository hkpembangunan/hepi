# Generated by Django 4.2.1 on 2023-06-26 08:03

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0014_alter_notification_next_action"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="for_user",
        ),
    ]
