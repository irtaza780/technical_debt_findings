import logging
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Optional

from models import Card

logger = logging.getLogger(__name__)

# Combination types
SINGLE = "SINGLE"
PAIR = "PAIR"
TRIPLE = "TRIPLE"
TRIPLE_SINGLE = "TRIPLE_SINGLE"
TRIPLE_PAIR = "TRIPLE_PAIR"
STRAIGHT = "STRAIGHT"
PAIR_SEQUENCE = "PAIR_SEQUENCE"
TRIPLE_SEQUENCE = "TRIPLE_SEQUENCE"
TRIPLE_SEQUENCE_SINGLE = "TRIPLE_SEQUENCE_SINGLE"
TRIPLE_SEQUENCE_PAIR = "TRIPLE_SEQUENCE_PAIR"
BOMB = "BOMB"
ROCKET = "ROCKET"
FOUR_TWO_SINGLE = "FOUR_TWO_SINGLE"
FOUR_TWO_PAIR = "FOUR_TWO_PAIR"

VALID_TYPES = {
    SINGLE, PAIR, TRIPLE, TRIPLE_SINGLE, TRIPLE_PAIR, STRAIGHT,
    PAIR_SEQUENCE, TRIPLE_SEQUENCE, TRIPLE_SEQUENCE_SINGLE, TRIPLE_SEQUENCE_PAIR,
    BOMB, ROCKET, FOUR_TWO_SINGLE, FOUR_TWO_PAIR
}

# Rank boundaries for sequences
MIN_SEQ_RANK = 3
MAX_SEQ_RANK = 14
RANK_TWO = 15
RANK_SMALL_JOKER = 16
RANK_BIG_JOKER = 17

# Minimum lengths for sequences
MIN_STRAIGHT_LENGTH = 5
MIN_PAIR_SEQUENCE_LENGTH = 3
MIN_TRIPLE_SEQUENCE_LENGTH = 2

# Card count constants
SINGLE_CARD_COUNT = 1
PAIR_CARD_COUNT = 2
TRIPLE_CARD_COUNT = 3
FOUR_CARD_COUNT = 4
ROCKET_CARD_COUNT = 2
TRIPLE_SINGLE_CARD_COUNT = 4
TRIPLE_PAIR_CARD_COUNT = 5
FOUR_TWO_SINGLE_CARD_COUNT = 6
FOUR_TWO_PAIR_CARD_COUNT = 8

# Divisibility constants for complex combinations
PAIR_SEQUENCE_DIVISOR = 2
TRIPLE_SEQUENCE_DIVISOR = 3
TRIPLE_SEQUENCE_SINGLE_DIVISOR = 4
TRIPLE_SEQUENCE_PAIR_DIVISOR = 5

MIN_TRIPLE_SEQUENCE_SINGLE_LENGTH = 8
MIN_TRIPLE_SEQUENCE_PAIR_LENGTH = 10


@dataclass
class Combination:
    """
    Represents a Dou Dizhu card combination.

    Attributes:
        type: The combination type (e.g., SINGLE, PAIR, BOMB, STRAIGHT).
        main_rank: The primary rank used for comparison (e.g., highest rank in straight,
                   rank of triple in triple combinations, rank of bomb).
        length: For sequences, the number of groups (e.g., number of cards in straight,
                number of pairs in pair sequence, number of triples in triple sequence).
        cards: The list of Card objects composing this combination.
        extra: Optional dictionary containing additional metadata (e.g., triple ranks in airplane).
    """
    type: str
    main_rank: int
    length: int
    cards: List[Card]
    extra: Optional[Dict] = None


def _extract_ranks(cards: List[Card]) -> List[int]:
    """
    Extract and return the ranks from a list of cards.

    Args:
        cards: List of Card objects.

    Returns:
        List of integer ranks.
    """
    return [c.rank for c in cards]


def _is_consecutive(ranks: List[int]) -> bool:
    """
    Check if a sorted list of ranks forms a consecutive sequence.

    Args:
        ranks: Sorted list of integer ranks.

    Returns:
        True if ranks are consecutive, False otherwise.
    """
    return all(b == a + 1 for a, b in zip(ranks, ranks[1:]))


def _valid_sequence_ranks(ranks: List[int]) -> bool:
    """
    Validate that all ranks are within the allowed range for sequences.

    Sequences cannot include 2s or jokers (ranks >= 15).

    Args:
        ranks: List of integer ranks to validate.

    Returns:
        True if all ranks are between MIN_SEQ_RANK and MAX_SEQ_RANK, False otherwise.
    """
    return all(MIN_SEQ_RANK <= r <= MAX_SEQ_RANK for r in ranks)


def _group_cards_by_rank(cards: List[Card]) -> Dict[int, List[Card]]:
    """
    Group cards by their rank.

    Args:
        cards: List of Card objects.

    Returns:
        Dictionary mapping rank to list of cards with that rank.
    """
    grouped = {}
    for card in cards:
        grouped.setdefault(card.rank, []).append(card)
    return grouped


def _find_consecutive_run(values: List[int], target_length: int) -> Optional[List[int]]:
    """
    Find the first consecutive run of exact length from a sorted list of values.

    Args:
        values: Sorted list of integer values.
        target_length: The desired length of the consecutive run.

    Returns:
        A list of consecutive values of target_length, or None if not found.
    """
    if len(values) < target_length:
        return None

    # Sliding window to find consecutive run
    for i in range(len(values) - target_length + 1):
        window = values[i:i + target_length]
        if _is_consecutive(window):
            return window

    return None


def _identify_single(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """
    Identify a single card combination.

    Args:
        cards: List containing exactly one card.
        ranks: Sorted ranks of the cards.

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != SINGLE_CARD_COUNT:
        return None
    return Combination(SINGLE, ranks[0], 1, list(cards))


def _identify_pair_or_rocket(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """
    Identify a pair or rocket combination from two cards.

    Args:
        cards: List containing exactly two cards.
        ranks: Sorted ranks of the cards.

    Returns:
        Combination object (PAIR or ROCKET) if valid, None otherwise.
    """
    if len(cards) != PAIR_CARD_COUNT:
        return None

    # Rocket: both jokers
    if ranks[0] == RANK_SMALL_JOKER and ranks[1] == RANK_BIG_JOKER:
        return Combination(ROCKET, RANK_BIG_JOKER, PAIR_CARD_COUNT, list(cards))

    # Pair: same rank
    if ranks[0] == ranks[1]:
        return Combination(PAIR, ranks[0], 1, list(cards))

    return None


def _identify_triple(cards: List[Card], ranks: List[int],
                     grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a triple combination from three cards.

    Args:
        cards: List containing exactly three cards.
        ranks: Sorted ranks of the cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != TRIPLE_CARD_COUNT:
        return None

    if len(grouped) == 1:
        return Combination(TRIPLE, ranks[0], 1, list(cards))

    return None


def _identify_four_card_combination(cards: List[Card], ranks: List[int],
                                     grouped: Dict[int, List[Card]],
                                     counts: List[int]) -> Optional[Combination]:
    """
    Identify four-card combinations: bomb or triple with single.

    Args:
        cards: List containing exactly four cards.
        ranks: Sorted ranks of the cards.
        grouped: Cards grouped by rank.
        counts: Sorted counts of cards per rank (descending).

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != FOUR_CARD_COUNT:
        return None

    # Bomb: four of a kind
    if len(grouped) == 1:
        return Combination(BOMB, ranks[0], 1, list(cards))

    # Triple with single
    if TRIPLE_CARD_COUNT in counts and SINGLE_CARD_COUNT in counts and len(grouped) == 2:
        triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
        return Combination(TRIPLE_SINGLE, triple_rank, 1, list(cards))

    return None


def _identify_triple_pair(cards: List[Card], grouped: Dict[int, List[Card]],
                          counts: List[int]) -> Optional[Combination]:
    """
    Identify a triple with pair combination (5 cards).

    Args:
        cards: List containing exactly five cards.
        grouped: Cards grouped by rank.
        counts: Sorted counts of cards per rank (descending).

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != TRIPLE_PAIR_CARD_COUNT:
        return None

    if TRIPLE_CARD_COUNT in counts and PAIR_CARD_COUNT in counts and len(grouped) == 2:
        triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
        return Combination(TRIPLE_PAIR, triple_rank, 1, list(cards))

    return None


def _identify_straight(cards: List[Card], ranks: List[int],
                       grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a straight combination (sequence of singles).

    Args:
        cards: List of cards.
        ranks: Sorted ranks of the cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    # All distinct ranks, minimum length, consecutive, valid sequence ranks
    if len(grouped) == len(cards) and len(cards) >= MIN_STRAIGHT_LENGTH:
        if _valid_sequence_ranks(ranks) and _is_consecutive(ranks):
            return Combination(STRAIGHT, max(ranks), len(cards), list(cards))

    return None


def _identify_pair_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a pair sequence combination (sequence of pairs).

    Args:
        cards: List of cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    # Must have even number of cards
    if len(cards) % PAIR_SEQUENCE_DIVISOR != 0:
        return None

    # Find all ranks with exactly 2 cards
    pair_ranks = [r for r, cs in grouped.items() if len(cs) == PAIR_CARD_COUNT]

    # All cards must be pairs, minimum 3 pairs
    if len(pair_ranks) * PAIR_CARD_COUNT == len(cards) and len(pair_ranks) >= MIN_PAIR_SEQUENCE_LENGTH:
        sorted_pair_ranks = sorted(pair_ranks)
        if _valid_sequence_ranks(sorted_pair_ranks) and _is_consecutive(sorted_pair_ranks):
            return Combination(PAIR_SEQUENCE, max(sorted_pair_ranks), len(pair_ranks), list(cards))

    return None


def _identify_triple_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a triple sequence combination (sequence of triples without wings).

    Args:
        cards: List of cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    # Must have card count divisible by 3
    if len(cards) % TRIPLE_SEQUENCE_DIVISOR != 0:
        return None

    # Find all ranks with exactly 3 cards
    triple_ranks = [r for r, cs in grouped.items() if len(cs) == TRIPLE_CARD_COUNT]

    # All cards must be triples, minimum 2 triples
    if len(triple_ranks) * TRIPLE_CARD_COUNT == len(cards) and len(triple_ranks) >= MIN_TRIPLE_SEQUENCE_LENGTH:
        sorted_triple_ranks = sorted(triple_ranks)
        if _valid_sequence_ranks(sorted_triple_ranks) and _is_consecutive(sorted_triple_ranks):
            return Combination(TRIPLE_SEQUENCE, max(sorted_triple_ranks), len(triple_ranks), list(cards))

    return None


def _identify_four_with_singles(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a four-of-a-kind with two single cards combination.

    Args:
        cards: List containing exactly six cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != FOUR_TWO_SINGLE_CARD_COUNT:
        return None

    four_ranks = [r for r, cs in grouped.items() if len(cs) == FOUR_CARD_COUNT]

    if len(four_ranks) == 1:
        single_count = sum(1 for r, cs in grouped.items() if len(cs) == SINGLE_CARD_COUNT)
        if single_count == 2:
            return Combination(FOUR_TWO_SINGLE, four_ranks[0], 1, list(cards))

    return None


def _identify_four_with_pairs(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """
    Identify a four-of-a-kind with two pair cards combination.

    Args:
        cards: List containing exactly eight cards.
        grouped: Cards grouped by rank.

    Returns:
        Combination object if valid, None otherwise.
    """
    if len(cards) != FOUR_TWO_PAIR_CARD_COUNT:
        return None

    four_ranks = [r for r, cs in grouped.items() if len(cs) == FOUR_CARD_COUNT]

    if len(four_ranks) == 1:
        pair_count = sum(1 for r, cs in grouped.items() if len(cs) == PAIR_CARD_COUNT)
        if pair_count == 2:
            return Combination(FOUR_TWO_PAIR, four_ranks[0], 1, list(cards))

    return None


def _identify_triple_sequence_with_singles(cards: List[Card], grouped: Dict[int, List[Card]],
                                           count_map: Counter) -> Optional[Combination]:
    """
    Identify a triple sequence with single wings (airplane with singles).

    Args:
        cards: List of cards.
        grouped: Cards grouped by rank.
        count_map: Counter of card ranks.

    Returns:
        Combination object if valid, None otherwise.
    """
    # Card count must be divisible by 4 and at least 8
    if len(cards) % TRIPLE_SEQUENCE_SINGLE_DIVISOR != 0 or len(cards) < MIN_TRIPLE_SEQUENCE_SINGLE_LENGTH:
        return None

    num_triples = len(cards) // TRIPLE_SEQUENCE_SINGLE_DIVISOR

    # Find ranks with at least 3 cards (potential triples)
    triple_candidates = [r for r, cs in grouped.items() if len(cs) >= TRIPLE_CARD_COUNT]

    # Filter to valid sequence ranks and find consecutive run
    valid_candidates = sorted([r for r in triple_candidates if MIN_SEQ_RANK <= r <= MAX_SEQ_RANK])
    triple_run = _find_consecutive_run(valid_candidates, num_triples)

    if not triple_run:
        return None

    # Calculate remaining cards after removing triples
    remaining_counts = count_map.copy()
    for triple_rank in triple_run:
        remaining_counts[triple_rank] -= TRIPLE_CARD_COUNT