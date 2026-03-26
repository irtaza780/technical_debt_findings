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
    
    Suits are cosmetic and only affect display/sorting; only rank matters for game rules.
    Jokers use suit 'J' with ranks 16 (small joker) and 17 (big joker).
    
    Attributes:
        rank (int): Card rank (3-15 for regular cards, 16-17 for jokers)
        suit (str): Card suit ('♠', '♥', '♣', '♦', or 'J' for jokers)
    """
    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str) -> None:
        """
        Initialize a card with the given rank and suit.
        
        Args:
            rank (int): The card's rank value
            suit (str): The card's suit symbol
        """
        self.rank = rank
        self.suit = suit

    @property
    def is_joker(self) -> bool:
        """
        Check if this card is a joker.
        
        Returns:
            bool: True if rank >= 16 (joker), False otherwise
        """
        return self.rank >= SMALL_JOKER_RANK

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"Card({self.rank},{self.suit})"

    def display(self) -> str:
        """
        Return a human-readable display string for this card.
        
        For jokers, returns only the rank label (e.g., 'SJ', 'BJ').
        For regular cards, returns rank label + suit symbol (e.g., '3♠', 'K♥').
        
        Returns:
            str: The formatted card display string
        """
        if self.is_joker:
            return RANK_LABELS[self.rank]
        return f"{RANK_LABELS[self.rank]}{self.suit}"

    def sort_key(self) -> Tuple[int, int]:
        """
        Generate a sort key for ordering cards.
        
        Cards are sorted primarily by rank (ascending), then by suit order.
        This ensures consistent, predictable card ordering.
        
        Returns:
            Tuple[int, int]: A tuple of (rank, suit_order) for sorting
        """
        suit_index = SUIT_ORDER.get(self.suit, 0)
        return (self.rank, suit_index)


class Deck:
    """
    A standard Dou Dizhu deck containing 54 cards.
    
    Composition:
        - 52 regular cards: ranks 3-15 (3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A, 2)
        - 2 jokers: small joker (rank 16) and big joker (rank 17)
    """

    def __init__(self) -> None:
        """Initialize a new deck with all 54 cards."""
        self.cards: List[Card] = []
        self._populate_regular_cards()
        self._populate_jokers()

    def _populate_regular_cards(self) -> None:
        """
        Populate the deck with regular cards (ranks 3-15).
        
        Creates one card for each rank in each suit.
        """
        for rank in range(MIN_REGULAR_RANK, MAX_REGULAR_RANK + 1):
            for suit in SUITS:
                self.cards.append(Card(rank, suit))

    def _populate_jokers(self) -> None:
        """
        Populate the deck with joker cards.
        
        Adds one small joker (rank 16) and one big joker (rank 17).
        """
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
        
        Distribution:
            - Each of 3 players receives 17 cards
            - 3 cards form the bottom (hidden) pile
        
        Returns:
            Tuple[List[List[Card]], List[Card]]: A tuple containing:
                - hands: List of 3 lists, each containing 17 cards for a player
                - bottom: List of 3 cards for the bottom pile
        
        Raises:
            ValueError: If deck does not contain exactly 54 cards
        """
        if len(self.cards) != TOTAL_DECK_SIZE:
            error_msg = f"Deck must have {TOTAL_DECK_SIZE} cards, got {len(self.cards)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.shuffle()
        
        # Deal cards to each player
        hands = [
            self.cards[i * CARDS_PER_PLAYER:(i + 1) * CARDS_PER_PLAYER]
            for i in range(NUM_PLAYERS)
        ]
        
        # Remaining cards form the bottom pile
        bottom = self.cards[CARDS_PER_PLAYER * NUM_PLAYERS:]
        
        logger.info(f"Dealt {NUM_PLAYERS} hands of {CARDS_PER_PLAYER} cards each, "
                   f"with {len(bottom)} cards in bottom pile")
        return hands, bottom


def sort_cards(cards: List[Card]) -> List[Card]:
    """
    Sort a list of cards by rank then suit in ascending order.
    
    Creates and returns a new sorted list without modifying the input.
    
    Args:
        cards (List[Card]): The list of cards to sort
    
    Returns:
        List[Card]: A new list of cards sorted by rank then suit
    """
    return sorted(cards, key=lambda card: card.sort_key())