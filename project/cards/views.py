from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Card
from .serializers import CategorySerializer, CardSerializer, BoardSerializer
from .utils import create_board_with_initial_cards
from .permissions import IsAdminOrCreateOnly

from rest_framework.pagination import LimitOffsetPagination

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
    """
    Get the user's board with selected cards + categories of these cards.
    """
    if not hasattr(request.user, 'board'):
        board = create_board_with_initial_cards(request.user)
    else:
        board = request.user.board

    cards = board.cards.all()
    categories = Category.objects.filter(cards__in=cards).distinct()

    return Response({
        "cards": CardSerializer(cards, many=True).data,
        "categories": CategorySerializer(categories, many=True).data
    }, status=status.HTTP_200_OK)
