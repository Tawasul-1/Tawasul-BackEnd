from .views import  InteractionViewSet, get_default_cards, get_stats
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet ,basename='category')
router.register(r'cards', views.CardViewSet, basename='cards')
router.register(r'interactions', InteractionViewSet, basename='interactions')


urlpatterns = [
    path('', include(router.urls)),
    path('board/', views.UserBoardView.as_view(), name='user-board'),
    path('board/with-categories/', views.board_with_categories, name='board-with-categories'),
    path('board/add/', views.add_card_to_board, name='add-card-to-board'),
    path('board/remove/', views.remove_card_from_board, name='remove-card-from-board'),
    path('board/test/', views.test_card, name='test-card'),
    path('verify-pin/', views.verify_pin, name='verify-pin'),
    path('stats/', get_stats, name='get_stats'),
    path('default/', get_default_cards, name='default-cards'),
]
