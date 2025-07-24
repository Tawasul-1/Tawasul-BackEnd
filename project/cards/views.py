import random
import os
import joblib
from datetime import datetime
from django.db import models
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from users.models import User

from .models import Category, Card, Interaction, Board
from .serializers import AddCardToBoardSerializer, CategorySerializer, CardSerializer, BoardSerializer, InteractionSerializer, RemoveCardFromBoardSerializer, StatsSerializer, TestCardSerializer, VerifyPinSerializer
from .utils import create_board_with_initial_cards
from .permissions import IsAdminOrCreateOnly
from users.permissions import IsPremiumUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



@swagger_auto_schema(
    method='post',
    request_body=VerifyPinSerializer,
    responses={200: openapi.Response("Verification result", examples={
        "application/json": {"status": True}
    })}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_pin(request):
    """
    Verify the PIN and just respond true/false. No session.
    """
    pin = request.data.get("pin")
    if pin == "2617":
        return Response({"status": True, "message": "PIN verified."})
    return Response({"status": False, "message": "Invalid PIN."}, status=400)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrCreateOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name_en', 'name_ar']


class CardViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage cards.
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [IsAdminOrCreateOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title_en', 'title_ar']
    filterset_fields = ['category']

    def get_queryset(self):
        """
        Return cards visible to the current user.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Card.objects.all()
        return Card.objects.filter(
            models.Q(owner=user) | models.Q(owner__isnull=True)
        )

    def perform_create(self, serializer):
        """
        Handle card creation and assign to boards if needed.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            card = serializer.save()
            if self.request.data.get("is_default") in [True, "true", "True"]:
                for board in Board.objects.all():
                    board.cards.add(card)
                    board.save()
            return
        if IsPremiumUser().has_permission(self.request, self):
            card = serializer.save(owner=user)
            board = user.board
            board.cards.add(card)
            return
        raise PermissionDenied("You do not have permission to create a card.")


class UserBoardView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the current user's board.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not hasattr(self.request.user, 'board'):
            return create_board_with_initial_cards(self.request.user)
        return self.request.user.board

@swagger_auto_schema(
    method='post',
    request_body=AddCardToBoardSerializer,
    responses={200: "Card added successfully."}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_card_to_board(request):
    """
    Add a card to the current user's board by card ID.
    Only allowed for premium users.
    """
    if not IsPremiumUser().has_permission(request, None):
        raise PermissionDenied("You must be a premium user to add cards to your board.")

    card_id = request.data.get('id')
    if not card_id:
        return Response({"status": False, "error": "Please provide card ID."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.objects.get(id=card_id)
    except Card.DoesNotExist:
        return Response({"status": False, "error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

    board = getattr(request.user, 'board', None)
    if not board:
        board = create_board_with_initial_cards(request.user)

    board.cards.add(card)
    return Response({"status": True, "message": f"Card '{card.title_en}' added to board."}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    request_body=RemoveCardFromBoardSerializer,
    responses={200: "Card removed successfully."}
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_card_from_board(request):
    """
    Remove a card from the current user's board by card ID.
    Only allowed for premium users.
    """
    if not IsPremiumUser().has_permission(request, None):
        raise PermissionDenied("You must be a premium user to remove cards from your board.")

    card_id = request.data.get('id')
    if not card_id:
        return Response({"status": False, "error": "Please provide card ID."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.objects.get(id=card_id)
    except Card.DoesNotExist:
        return Response({"status": False, "error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

    board = getattr(request.user, 'board', None)
    if not board:
        board = create_board_with_initial_cards(request.user)

    board.cards.remove(card)
    return Response({"status": True, "message": f"Card '{card.title_en}' removed from board."}, status=status.HTTP_200_OK)


@swagger_auto_schema(method='get', responses={200: CardSerializer(many=True)})
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def board_with_categories(request):
    """
    Return the current user's board cards and their categories, sorted by prediction if model exists.
    """
    request.session.pop('pin_verified', None)
    user = request.user
    board = getattr(user, 'board', None) or create_board_with_initial_cards(user)
    cards = list(board.cards.all())
    if not cards:
        return Response({"cards": [], "categories": []}, status=200)
    current_hour = datetime.now().hour
    bundle_path = os.path.join(settings.BASE_DIR, 'cards', 'ml_models', 'click_model.pkl')
    if not os.path.exists(bundle_path):
        categories = Category.objects.filter(cards__in=cards).distinct()
        return Response({
                "debug_cards": CardSerializer(cards, many=True).data,

            "hour_used": current_hour,
            "cards": CardSerializer(cards, many=True).data,
            "categories": CategorySerializer(categories, many=True).data
        }, status=200)
    bundle = joblib.load(bundle_path)
    model = bundle['model']
    le_user = bundle['le_user']
    le_card = bundle['le_card']
    try:
        user_enc = le_user.transform([user.id])[0]
    except ValueError:
        user_enc = 0
        card_preds = []

    for card in cards:
        try:
            card_enc = le_card.transform([card.id])[0]
            features = [[user_enc, card_enc, current_hour]]
            pred = model.predict(features)[0]
        except ValueError:
            print(f"Card ID {card.id} not found in label encoder.")
            pred = 0
        card_preds.append((card, pred)) 

    if not card_preds:
        cards_sorted = cards
    else:
        cards_sorted = [c for c, _ in sorted(card_preds, key=lambda x: x[1], reverse=True)]
    categories = Category.objects.filter(cards__in=cards_sorted).distinct()
    return Response({
        "hour_used": current_hour,
        "cards": CardSerializer(cards_sorted, many=True).data,
        "categories": CategorySerializer(categories, many=True).data
    }, status=200)


@swagger_auto_schema(
    method='post',
    request_body=TestCardSerializer,
    responses={200: "Shuffled list of cards returned."}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_card(request):
    """
    Test a card by returning a shuffled list of cards from the same category
    at the specified difficulty level.
    """
    card_id = request.data.get('card_id')
    level = int(request.data.get('level', 1))
    if not card_id:
        return Response({"status": False, "error": "Please provide card_id."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target_card = Card.objects.get(id=card_id)
    except Card.DoesNotExist:
        return Response({"status": False, "error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)
    category_cards = list(
        Card.objects.filter(category=target_card.category)
        .exclude(id=target_card.id)
        .filter(models.Q(owner=request.user) | models.Q(owner__isnull=True))
    )
    total_cards = min(level + 1, len(category_cards) + 1)
    result_cards = [target_card]
    needed_distractors = total_cards - 1
    if needed_distractors > 0:
        if len(category_cards) <= needed_distractors:
            distractors = category_cards
        else:
            distractors = random.sample(category_cards, needed_distractors)
        result_cards.extend(distractors)
    random.shuffle(result_cards)
    return Response({"status": True, "cards": CardSerializer(result_cards, many=True).data}, status=status.HTTP_200_OK)


class InteractionViewSet(viewsets.ModelViewSet):
    """
    ViewSet to log and retrieve user interactions.
    """
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        return Interaction.objects.filter(user=self.request.user)

@swagger_auto_schema(method='get', responses={200: CardSerializer(many=True)})
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_stats(request):
    """
    Returns counts of users, categories, cards, and default board cards.
    """
    users_count = User.objects.count()
    categories_count = Category.objects.count()
    cards_count = Card.objects.count()
    default_board_cards_count = Board.objects.filter(cards__owner__isnull=True).values('cards').distinct().count()

    data = {
        'users_count': users_count,
        'categories_count': categories_count,
        'cards_count': cards_count,
        'default_board_cards_count': default_board_cards_count
    }

    serializer = StatsSerializer(data)
    return Response(serializer.data)