# Generated by Django 5.2.4 on 2025-07-10 11:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=255)),
                ('name_ar', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='cards/')),
                ('title_en', models.CharField(max_length=255)),
                ('title_ar', models.CharField(max_length=255)),
                ('audio_en', models.FileField(blank=True, null=True, upload_to='audio/')),
                ('audio_ar', models.FileField(blank=True, null=True, upload_to='audio/')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='cards.category')),
            ],
        ),
    ]
