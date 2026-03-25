import logging
import random
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Card rank constants
MIN_REGULAR_RANK = 3
MAX_REGULAR_RANK = 15
SMALL_JOKER_RANK = 16
BIG_JOKER_RANK = 17
JOKER_SUIT = 'J'

# Rank display labels
RANK_LABELS = {
    3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
    11: 'J', 12: 'Q', 13: 'K', 14: 'A', 15: '2', 16: 'SJ', 17: 'BJ'
}

# Suit constants and ordering
SUITS = ['♠', '♥', '♣', '♦']
SUIT_ORDER = {suit: index for index, suit in enumerate(SUITS)}

# Deck constants
CARDS_PER_PLAYER = 17
NUM_PLAYERS = 3
BOTTOM_CARD_COUNT = 3
TOTAL_DECK_SIZE = CARDS_PER_PLAYER * NUM_PLAYERS + BOTTOM_CARD_COUNT


class Card:
    """
    Represents a single playing card in Dou Dizhu.
    
    In Dou Dizhu, suits are cosmetic and only rank matters for game rules.
    Jokers use suit 'J' with ranks 16 (small joker) and 17 (big joker).
    
    Attributes:
        rank (int): Card rank (3-15 for regular cards, 16-17 for jokers)
        suit (str): Card suit (♠, ♥, ♣, ♦, or J for jokers)
    """
    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str) -> None:
        """
        Initialize a Card.
        
        Args:
            rank (int): The rank value of the card
            suit (str): The suit symbol of the card
        """
        self.rank = rank
        self.suit = suit

    @property
    def is_joker(self) -> bool:
        """
        Check if this card is a joker.
        
        Returns:
            bool: True if rank is 16 or 17 (joker ranks), False otherwise
        """
        return self.rank >= SMALL_JOKER_RANK

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"Card({self.rank},{self.suit})"

    def display(self) -> str:
        """
        Return a human-readable display string for the card.
        
        Returns:
            str: Formatted card display (e.g., "3♠", "SJ" for small joker)
        """
        if self.is_joker:
            return RANK_LABELS[self.rank]
        return f"{RANK_LABELS[self.rank]}{self.suit}"

    def sort_key(self) -> Tuple[int, int]:
        """
        Generate a sort key for ordering cards.
        
        Cards are sorted primarily by rank (ascending), then by suit order.
        This ensures consistent ordering for hand display and comparison.
        
        Returns:
            Tuple[int, int]: (rank, suit_order) for sorting
        """
        suit_index = SUIT_ORDER.get(self.suit, 0)
        return (self.rank, suit_index)


class Deck:
    """
    A standard Dou Dizhu deck containing 54 cards.
    
    The deck consists of:
    - 52 regular cards: ranks 3-15 (where 15 represents 2) in 4 suits
    - 2 jokers: small joker (rank 16) and big joker (rank 17)
    
    Attributes:
        cards (List[Card]): The list of cards in the deck
    """

    def __init__(self) -> None:
        """Initialize a full Dou Dizhu deck with all 54 cards."""
        self.cards: List[Card] = []
        self._add_regular_cards()
        self._add_jokers()

    def _add_regular_cards(self) -> None:
        """
        Add all regular cards (ranks 3-15) in all four suits to the deck.
        
        Rank 15 represents the card "2" in Dou Dizhu.
        """
        for rank in range(MIN_REGULAR_RANK, MAX_REGULAR_RANK + 1):
            for suit in SUITS:
                self.cards.append(Card(rank, suit))

    def _add_jokers(self) -> None:
        """Add the two jokers (small and big) to the deck."""
        self.cards.append(Card(SMALL_JOKER_RANK, JOKER_SUIT))
        self.cards.append(Card(BIG_JOKER_RANK, JOKER_SUIT))

    def shuffle(self) -> None:
        """
        Shuffle the deck in-place using random permutation.
        """
        random.shuffle(self.cards)
        logger.debug("Deck shuffled")

    def deal(self) -> Tuple[List[List[Card]], List[Card]]:
        """
        Deal cards to three players and create a bottom (hidden) pile.
        
        Each player receives 17 cards, and 3 cards form the bottom pile.
        The deck is shuffled before dealing.
        
        Returns:
            Tuple[List[List[Card]], List[Card]]: A tuple containing:
                - hands: List of 3 hands, each containing 17 cards
                - bottom: List of 3 bottom cards
        """
        self.shuffle()
        hands = self._distribute_cards_to_players()
        bottom = self._extract_bottom_cards()
        logger.info(f"Dealt cards to {NUM_PLAYERS} players with {BOTTOM_CARD_COUNT} bottom cards")
        return hands, bottom

    def _distribute_cards_to_players(self) -> List[List[Card]]:
        """
        Distribute cards equally among players.
        
        Returns:
            List[List[Card]]: List of player hands, each with CARDS_PER_PLAYER cards
        """
        hands = [
            self.cards[i * CARDS_PER_PLAYER:(i + 1) * CARDS_PER_PLAYER]
            for i in range(NUM_PLAYERS)
        ]
        return hands

    def _extract_bottom_cards(self) -> List[Card]:
        """
        Extract the bottom (hidden) cards from the deck.
        
        Returns:
            List[Card]: The remaining cards after player distribution
        """
        return self.cards[CARDS_PER_PLAYER * NUM_PLAYERS:]


def sort_cards(cards: List[Card]) -> List[Card]:
    """
    Sort a list of cards by rank then suit in ascending order.
    
    This function creates a new sorted list without modifying the original.
    Cards are sorted primarily by rank (3 is lowest, Big Joker is highest),
    then by suit order for consistent display.
    
    Args:
        cards (List[Card]): The cards to sort
        
    Returns:
        List[Card]: A new list of cards sorted by rank then suit
    """
    return sorted(cards, key=lambda card: card.sort_key())