# Generated by Django 5.2.4 on 2025-07-15 19:24

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0003_alter_card_title_ar_alter_card_title_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(default=django.utils.timezone.now, upload_to='cards/'),
            preserve_default=False,
        ),
    ]
