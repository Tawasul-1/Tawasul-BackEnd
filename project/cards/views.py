import random
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from .models import Category, Card, Interaction
from .serializers import CategorySerializer, CardSerializer, BoardSerializer, InteractionSerializer
from .utils import create_board_with_initial_cards
from .permissions import IsAdminOrCreateOnly
from django.utils.timezone import now
import joblib
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Card
from .serializers import CardSerializer
import pandas as pd
from .utils import load_model
from datetime import datetime


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrCreateOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name_en', 'name_ar']


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [IsAdminOrCreateOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title_en', 'title_ar']
    filterset_fields = ['category']


class UserBoardView(generics.RetrieveUpdateAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not hasattr(self.request.user, 'board'):
            return create_board_with_initial_cards(self.request.user)
        return self.request.user.board


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_card_to_board(request):
    """
    Add a card to the current user's board by title_en or title_ar (partial match)
    """
    title = request.data.get('title')
    if not title:
        return Response({"status": False, "error": "Please provide card title."}, status=status.HTTP_400_BAD_REQUEST)

    card = Card.objects.filter(title_en__icontains=title).first()
    if not card:
        return Response({"status": False, "error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

    if not hasattr(request.user, 'board'):
        board = create_board_with_initial_cards(request.user)
    else:
        board = request.user.board

    board.cards.add(card)

    return Response({
        "status": True,
        "message": f"Card '{card.title_en}' added to board."
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_card_from_board(request):
    """
    Remove a card from the current user's board by title_en or title_ar (partial match)
    """
    title = request.data.get('title')
    if not title:
        return Response({"status": False, "error": "Please provide card title."}, status=status.HTTP_400_BAD_REQUEST)

    card = Card.objects.filter(title_en__icontains=title).first()
    if not card:
        return Response({"status": False, "error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

    if not hasattr(request.user, 'board'):
        board = create_board_with_initial_cards(request.user)
    else:
        board = request.user.board

    board.cards.remove(card)

    return Response({
        "status": True,
        "message": f"Card '{card.title_en}' removed from board."
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def board_with_categories(request):

    user = request.user


    board = getattr(user, 'board', None) or create_board_with_initial_cards(user)
    cards = list(board.cards.all())
    if not cards:
        return Response({"cards": [], "categories": []}, status=200)

    current_hour = datetime.now().hour

    
    bundle_path = os.path.join(settings.BASE_DIR, 'cards', 'ml_models', 'click_model.pkl')
    if not os.path.exists(bundle_path):
        
        categories = Category.objects.filter(cards__in=cards).distinct()
        return Response(
            {
                "hour_used": current_hour,
                "cards": CardSerializer(cards, many=True).data,
                "categories": CategorySerializer(categories, many=True).data
            }, status=200
        )

    bundle = joblib.load(bundle_path)
    model   = bundle['model']
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
        except ValueError:
            
            continue

        features = [[user_enc, card_enc, current_hour]]
        pred = model.predict(features)[0]
        print(f"[Prediction] Card: {card.title_en} | Encoded ID: {card_enc} | Hour: {current_hour} | Predicted Clicks: {pred:.2f}")
        card_preds.append((card, pred))

    if not card_preds:
        cards_sorted = cards
    else:
        cards_sorted = [c for c, _ in sorted(card_preds, key=lambda x: x[1], reverse=True)]

    
    categories = Category.objects.filter(cards__in=cards_sorted).distinct()

    return Response(
        {
            "hour_used": current_hour,
            "cards": CardSerializer(cards_sorted, many=True).data,
            "categories": CategorySerializer(categories, many=True).data
        }, status=200
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
        Card.objects.filter(category=target_card.category).exclude(id=target_card.id)
    )

    total_cards = min(level + 1, len(category_cards) + 1)  

    result_cards = [target_card]

    needed_distractors = total_cards - 1
    if needed_distractors > 0:
        if len(category_cards) < needed_distractors:
            distractors = category_cards  
        else:
            distractors = random.sample(category_cards, needed_distractors)
        result_cards.extend(distractors)

    random.shuffle(result_cards)

    return Response({
        "status": True,
        "cards": CardSerializer(result_cards, many=True).data
    }, status=status.HTTP_200_OK)

@permission_classes([permissions.IsAuthenticated])
class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    

    def get_queryset(self):
        return Interaction.objects.filter(user=self.request.user)





