from django.contrib import admin
from .models import Card, Category, Interaction

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title_en', 'title_ar')
    search_fields = ('title_en', 'title_ar')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_en', 'name_ar')
    search_fields = ('name_en', 'name_ar')

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'card', 'hour_range_start', 'hour_range_end', 'click_count')
    search_fields = ('user__username', 'card__title_en')
    list_filter = ('hour_range_start', 'hour_range_end')
    