from .models import Board, Card

def create_board_with_initial_cards(user):
    """
    Create a board for the user with default cards.
    """
    board = Board.objects.create(user=user)
    default_cards = Card.objects.filter(is_default=True)
    board.cards.set(default_cards)
    return board
