from django.contrib import admin
from .models import Card, Category

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title_en', 'title_ar')
    search_fields = ('title_en', 'title_ar')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_en', 'name_ar')
    search_fields = ('name_en', 'name_ar')