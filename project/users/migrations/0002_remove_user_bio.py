# Generated by Django 5.2.4 on 2025-07-11 22:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='bio',
        ),
    ]
