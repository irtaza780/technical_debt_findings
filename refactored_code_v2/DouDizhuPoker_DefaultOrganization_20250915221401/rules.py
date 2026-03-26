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
JOKER_SMALL_RANK = 16
JOKER_BIG_RANK = 17

# Minimum lengths for sequences
MIN_STRAIGHT_LENGTH = 5
MIN_PAIR_SEQUENCE_LENGTH = 3
MIN_TRIPLE_SEQUENCE_LENGTH = 2
MIN_AIRPLANE_SINGLE_LENGTH = 2
MIN_AIRPLANE_PAIR_LENGTH = 2

# Card counts for combinations
SINGLE_CARD_COUNT = 1
PAIR_CARD_COUNT = 2
TRIPLE_CARD_COUNT = 3
ROCKET_CARD_COUNT = 2
FOUR_CARD_COUNT = 4
FOUR_TWO_SINGLE_CARD_COUNT = 6
FOUR_TWO_PAIR_CARD_COUNT = 8
AIRPLANE_SINGLE_DIVISOR = 4
AIRPLANE_PAIR_DIVISOR = 5


@dataclass
class Combination:
    """
    Represents a Dou Dizhu card combination.

    Attributes:
        type: Combination type string (e.g., SINGLE, PAIR, BOMB).
        main_rank: Primary comparison rank (highest in straight, rank of triple, bomb rank).
        length: For sequences, number of groups (straight length, pair count, triple count).
        cards: List of Card objects composing the combination.
        extra: Optional dictionary for additional metadata (e.g., triple ranks in airplane).
    """
    type: str
    main_rank: int
    length: int
    cards: List[Card]
    extra: Optional[Dict] = None


def _extract_ranks(cards: List[Card]) -> List[int]:
    """Extract and return ranks from a list of cards."""
    return [card.rank for card in cards]


def _is_consecutive(ranks: List[int]) -> bool:
    """Check if ranks form a consecutive sequence."""
    return all(second == first + 1 for first, second in zip(ranks, ranks[1:]))


def _valid_sequence_ranks(ranks: List[int]) -> bool:
    """Verify all ranks are valid for sequences (no 2s or jokers)."""
    return all(MIN_SEQ_RANK <= rank <= MAX_SEQ_RANK for rank in ranks)


def _group_cards_by_rank(cards: List[Card]) -> Dict[int, List[Card]]:
    """Group cards by their rank."""
    grouped = {}
    for card in cards:
        grouped.setdefault(card.rank, []).append(card)
    return grouped


def _get_rank_counts(ranks: List[int]) -> List[int]:
    """Get sorted counts of each rank (descending)."""
    return sorted((count for count in Counter(ranks).values()), reverse=True)


def _find_consecutive_run(values: List[int], target_length: int) -> Optional[List[int]]:
    """
    Find a consecutive run of exact length from sorted values.

    Args:
        values: Sorted list of integers.
        target_length: Desired length of consecutive run.

    Returns:
        First consecutive run of target_length, or None if not found.
    """
    if len(values) < target_length:
        return None

    for start_idx in range(len(values) - target_length + 1):
        window = values[start_idx:start_idx + target_length]
        if _is_consecutive(window):
            return window

    return None


def _identify_single(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """Identify a single card combination."""
    if len(cards) == 1:
        return Combination(SINGLE, ranks[0], 1, list(cards))
    return None


def _identify_pair_or_rocket(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """Identify a pair or rocket combination."""
    if len(cards) != PAIR_CARD_COUNT:
        return None

    if ranks[0] == JOKER_SMALL_RANK and ranks[1] == JOKER_BIG_RANK:
        return Combination(ROCKET, JOKER_BIG_RANK, PAIR_CARD_COUNT, list(cards))

    if ranks[0] == ranks[1]:
        return Combination(PAIR, ranks[0], 1, list(cards))

    return None


def _identify_triple(cards: List[Card], ranks: List[int], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a triple combination."""
    if len(cards) == TRIPLE_CARD_COUNT and len(grouped) == 1:
        return Combination(TRIPLE, ranks[0], 1, list(cards))
    return None


def _identify_bomb_or_triple_single(cards: List[Card], ranks: List[int], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a bomb or triple with single combination."""
    if len(cards) != FOUR_CARD_COUNT:
        return None

    counts = _get_rank_counts(ranks)

    if len(grouped) == 1:
        return Combination(BOMB, ranks[0], 1, list(cards))

    if TRIPLE_CARD_COUNT in counts and 1 in counts and len(grouped) == 2:
        triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
        return Combination(TRIPLE_SINGLE, triple_rank, 1, list(cards))

    return None


def _identify_straight(cards: List[Card], ranks: List[int], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a straight combination."""
    if len(grouped) != len(cards) or len(cards) < MIN_STRAIGHT_LENGTH:
        return None

    if _valid_sequence_ranks(ranks) and _is_consecutive(ranks):
        return Combination(STRAIGHT, max(ranks), len(cards), list(cards))

    return None


def _identify_triple_pair(cards: List[Card], ranks: List[int], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a triple with pair combination."""
    if len(cards) != 5:
        return None

    counts = _get_rank_counts(ranks)

    if TRIPLE_CARD_COUNT in counts and PAIR_CARD_COUNT in counts and len(grouped) == 2:
        triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
        return Combination(TRIPLE_PAIR, triple_rank, 1, list(cards))

    return None


def _identify_pair_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a pair sequence combination."""
    if len(cards) % PAIR_CARD_COUNT != 0:
        return None

    pair_ranks = [rank for rank, card_list in grouped.items() if len(card_list) == PAIR_CARD_COUNT]

    if len(pair_ranks) * PAIR_CARD_COUNT != len(cards) or len(pair_ranks) < MIN_PAIR_SEQUENCE_LENGTH:
        return None

    sorted_pair_ranks = sorted(pair_ranks)

    if _valid_sequence_ranks(sorted_pair_ranks) and _is_consecutive(sorted_pair_ranks):
        return Combination(PAIR_SEQUENCE, max(sorted_pair_ranks), len(pair_ranks), list(cards))

    return None


def _identify_triple_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a triple sequence combination."""
    if len(cards) % TRIPLE_CARD_COUNT != 0:
        return None

    triple_ranks = [rank for rank, card_list in grouped.items() if len(card_list) == TRIPLE_CARD_COUNT]

    if len(triple_ranks) * TRIPLE_CARD_COUNT != len(cards) or len(triple_ranks) < MIN_TRIPLE_SEQUENCE_LENGTH:
        return None

    sorted_triple_ranks = sorted(triple_ranks)

    if _valid_sequence_ranks(sorted_triple_ranks) and _is_consecutive(sorted_triple_ranks):
        return Combination(TRIPLE_SEQUENCE, max(sorted_triple_ranks), len(triple_ranks), list(cards))

    return None


def _identify_four_with_singles(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a four-of-a-kind with two singles combination."""
    if len(cards) != FOUR_TWO_SINGLE_CARD_COUNT:
        return None

    four_ranks = [rank for rank, card_list in grouped.items() if len(card_list) == FOUR_CARD_COUNT]

    if len(four_ranks) != 1:
        return None

    single_count = sum(1 for rank, card_list in grouped.items() if len(card_list) == 1)

    if single_count == 2:
        return Combination(FOUR_TWO_SINGLE, four_ranks[0], 1, list(cards))

    return None


def _identify_four_with_pairs(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify a four-of-a-kind with two pairs combination."""
    if len(cards) != FOUR_TWO_PAIR_CARD_COUNT:
        return None

    four_ranks = [rank for rank, card_list in grouped.items() if len(card_list) == FOUR_CARD_COUNT]

    if len(four_ranks) != 1:
        return None

    pair_count = sum(1 for rank, card_list in grouped.items() if len(card_list) == PAIR_CARD_COUNT)

    if pair_count == 2:
        return Combination(FOUR_TWO_PAIR, four_ranks[0], 1, list(cards))

    return None


def _identify_airplane_single(cards: List[Card], grouped: Dict[int, List[Card]], rank_counts: Counter) -> Optional[Combination]:
    """Identify an airplane with single wings combination."""
    if len(cards) % AIRPLANE_SINGLE_DIVISOR != 0 or len(cards) < 8:
        return None

    triple_count = len(cards) // AIRPLANE_SINGLE_DIVISOR

    triple_ranks = [rank for rank, card_list in grouped.items() if len(card_list) >= TRIPLE_CARD_COUNT]
    valid_triple_ranks = sorted([r for r in triple_ranks if MIN_SEQ_RANK <= r <= MAX_SEQ_RANK])

    consecutive_run = _find_consecutive_run(valid_triple_ranks, triple_count)

    if not consecutive_run:
        return None

    # Calculate available singles excluding triple run ranks
    leftover_counts = rank_counts.copy()
    for triple_rank in consecutive_run:
        leftover_counts[triple_rank] -= TRIPLE_CARD_COUNT

    available_singles = sum(count for rank, count in leftover_counts.items() if rank not in consecutive_run and count > 0)

    if available_singles >= triple_count:
        return Combination(TRIPLE_SEQUENCE_SINGLE, max(consecutive_run), triple_count, list(cards), extra={'triples': consecutive_run})

    return None


def _identify_airplane_pair(cards: List[Card], grouped: Dict[int, List[Card]], rank_counts: Counter) -> Optional[Combination]:
    """Identify an airplane with pair wings combination."""
    if len(cards) % AIRPLANE_PAIR_DIVISOR != 0 or len(cards) < 10:
        return None

    triple_count = len(cards) // AIRPLANE_PAIR_DIVISOR

    triple_ranks = [rank for rank, card_list in grouped.items() if len(card_list) >= TRIPLE_CARD_COUNT]
    valid_triple_ranks = sorted([r for r in triple_ranks if MIN_SEQ_RANK <= r <= MAX_SEQ_RANK])

    consecutive_run = _find_consecutive_run(valid_triple_ranks, triple_count)

    if not consecutive_run:
        return None

    # Calculate available pairs excluding triple run ranks
    leftover_counts = rank_counts.copy()
    for triple_rank in consecutive_run:
        leftover_counts[triple_rank] -= TRIPLE_CARD_COUNT

    available_pairs = sum(count // PAIR_CARD_COUNT for rank, count in leftover_counts.items() if rank not in consecutive_run)

    if available_pairs >= triple_count:
        return Combination(TRIPLE_SEQUENCE_PAIR, max(consecutive_run), triple_count, list(cards), extra={'triples': consecutive_run})

    return None


def identify_combination(cards: List[Card]) -> Optional[Combination]:
    """
    Identify the combination type of given cards according to Dou Dizhu rules.

    Args:
        cards: List of Card objects to identify.

    Returns:
        Combination object if valid combination found, None otherwise.
    """
    if not cards:
        return None

    ranks = sorted(_extract_ranks(cards))
    grouped = _group_cards_by_rank(cards)
    rank_counts = Counter(ranks)

    # Try simple combinations first
    result = _identify_single(cards, ranks)
    if result:
        return result

    result = _identify_pair_or_rocket(cards, ranks)
    if result:
        return result

    result = _identify_triple(cards, ranks, grouped)
    if result:
        return result

    result = _identify_bomb_or_triple_single(cards, ranks, grouped)
    if result:
        return result

    # Try sequence combinations
    result = _identify_straight(cards, ranks, grouped)
    if result:
        return result

    result = _identify_triple_pair(cards, ranks, grouped)
    if result:
        return result

    result = _identify_pair_sequence(cards, grouped)
    if result:
        return result

    result = _identify_triple_sequence(cards, grouped)
    if result:
        return result

    result = _identify_four_with_singles(cards, grouped)
    if result:
        return result

    result = _identify_four_with_pairs(cards, grouped)
    if result:
        return result

    result = _identify_airplane_single(cards, grouped, rank_counts)
    if result:
        return result

    result = _identify_airplane_pair(cards, grouped, rank_counts)
    if result:
        return result

    return None


def _can_beat_with_same_type(new_comb: Combination, prev_comb: Combination) -> bool:
    """
    Determine if new combination beats previous combination of same type.

    Args:
        new_comb: New combination to play.
        prev_comb: Previous combination to beat.

    Returns:
        True if new_comb beats prev_comb, False otherwise.
    """
    # Sequence types require matching length
    if new