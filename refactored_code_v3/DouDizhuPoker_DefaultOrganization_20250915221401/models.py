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

# Rank value mappings
RANK_LABELS = {
    3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
    11: 'J', 12: 'Q', 13: 'K', 14: 'A', 15: '2', 16: 'SJ', 17: 'BJ'
}

# Suit constants and ordering
SUITS = ['♠', '♥', '♣', '♦']
SUIT_ORDER = {suit: index for index, suit in enumerate(SUITS)}

# Deck dealing constants
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
            bool: True if rank >= 16 (joker), False otherwise
        """
        return self.rank >= SMALL_JOKER_RANK

    def __repr__(self) -> str:
        """
        Return a technical representation of the card.
        
        Returns:
            str: String in format "Card(rank,suit)"
        """
        return f"Card({self.rank},{self.suit})"

    def display(self) -> str:
        """
        Return a human-readable display string for the card.
        
        For jokers, returns only the rank label (e.g., 'SJ', 'BJ').
        For regular cards, returns rank label followed by suit symbol.
        
        Returns:
            str: Display string for the card
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
    
    Composition: 13 ranks × 4 suits (52 cards) + 2 jokers = 54 cards total.
    Ranks: 3-10 (numeric), J, Q, K, A, 2 (face cards), plus small and big jokers.
    """

    def __init__(self) -> None:
        """Initialize a full, unshuffled Dou Dizhu deck."""
        self.cards: List[Card] = []
        self._populate_deck()

    def _populate_deck(self) -> None:
        """
        Populate the deck with all 54 cards.
        
        Adds regular cards (ranks 3-15) in all four suits,
        then adds the two jokers.
        """
        # Add regular cards: ranks 3 through 2 (represented as 15)
        for rank in range(MIN_REGULAR_RANK, MAX_REGULAR_RANK + 1):
            for suit in SUITS:
                self.cards.append(Card(rank, suit))
        
        # Add jokers
        self.cards.append(Card(SMALL_JOKER_RANK, JOKER_SUIT))
        self.cards.append(Card(BIG_JOKER_RANK, JOKER_SUIT))
        
        logger.debug(f"Deck populated with {len(self.cards)} cards")

    def shuffle(self) -> None:
        """
        Shuffle the deck in-place using random permutation.
        """
        random.shuffle(self.cards)
        logger.debug("Deck shuffled")

    def deal(self) -> Tuple[List[List[Card]], List[Card]]:
        """
        Deal cards to three players and create a bottom (landlord) pile.
        
        Each player receives 17 cards, and 3 cards form the bottom pile.
        The deck is shuffled before dealing.
        
        Returns:
            Tuple containing:
                - hands (List[List[Card]]): Three lists of 17 cards each for players
                - bottom (List[Card]): 3 cards for the landlord's bottom pile
        """
        self.shuffle()
        
        # Deal 17 cards to each of 3 players
        hands = [
            self.cards[i * CARDS_PER_PLAYER:(i + 1) * CARDS_PER_PLAYER]
            for i in range(NUM_PLAYERS)
        ]
        
        # Remaining 3 cards form the bottom pile
        bottom = self.cards[CARDS_PER_PLAYER * NUM_PLAYERS:]
        
        logger.info(f"Dealt {len(hands)} hands of {CARDS_PER_PLAYER} cards, "
                   f"with {len(bottom)} bottom cards")
        
        return hands, bottom


def sort_cards(cards: List[Card]) -> List[Card]:
    """
    Sort a list of cards by rank then suit in ascending order.
    
    Creates and returns a new sorted list without modifying the input.
    Sorting order: lower ranks first, then by suit order (♠, ♥, ♣, ♦).
    
    Args:
        cards (List[Card]): The cards to sort
        
    Returns:
        List[Card]: A new list of cards sorted by rank then suit
    """
    return sorted(cards, key=lambda card: card.sort_key())