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

# Combination size constants
MIN_STRAIGHT_LENGTH = 5
MIN_PAIR_SEQUENCE_LENGTH = 3
MIN_TRIPLE_SEQUENCE_LENGTH = 2
FOUR_TWO_SINGLE_SIZE = 6
FOUR_TWO_PAIR_SIZE = 8
TRIPLE_SEQUENCE_SINGLE_MIN_SIZE = 8
TRIPLE_SEQUENCE_PAIR_MIN_SIZE = 10


@dataclass
class Combination:
    """
    Describes a Dou Dizhu combination.

    Attributes:
        type: Combination type string (e.g., SINGLE, PAIR, BOMB).
        main_rank: Primary comparison rank (e.g., highest in straight, rank of triple).
        length: For sequences, number of groups (e.g., straight length, pair-sequence length).
        cards: Cards composing the combination.
        extra: Optional dictionary with additional details (e.g., triple ranks in airplane).
    """
    type: str
    main_rank: int
    length: int
    cards: List[Card]
    extra: Optional[Dict] = None


def _extract_ranks(cards: List[Card]) -> List[int]:
    """Extract and return ranks from a list of cards."""
    return [c.rank for c in cards]


def _is_consecutive(ranks: List[int]) -> bool:
    """Check if ranks form a consecutive sequence."""
    return all(b == a + 1 for a, b in zip(ranks, ranks[1:]))


def _valid_sequence_ranks(ranks: List[int]) -> bool:
    """Verify all ranks are valid for sequences (no 2 or jokers)."""
    return all(MIN_SEQ_RANK <= r <= MAX_SEQ_RANK for r in ranks)


def _group_cards_by_rank(cards: List[Card]) -> Dict[int, List[Card]]:
    """Group cards by their rank."""
    grouped = {}
    for card in cards:
        grouped.setdefault(card.rank, []).append(card)
    return grouped


def _get_count_distribution(grouped: Dict[int, List[Card]]) -> List[int]:
    """Get sorted count distribution of card groups (descending)."""
    return sorted((len(v) for v in grouped.values()), reverse=True)


def _find_consecutive_run(values: List[int], length: int) -> Optional[List[int]]:
    """
    Find a consecutive run of exact length from sorted values.

    Args:
        values: Sorted list of integers.
        length: Required length of consecutive run.

    Returns:
        First consecutive run of exact length, or None if not found.
    """
    if len(values) < length:
        return None

    for i in range(len(values) - length + 1):
        window = values[i:i + length]
        if _is_consecutive(window):
            return window

    return None


def _identify_single(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """Identify single card combination."""
    if len(cards) == 1:
        return Combination(SINGLE, ranks[0], 1, list(cards))
    return None


def _identify_pair_or_rocket(cards: List[Card], ranks: List[int]) -> Optional[Combination]:
    """Identify pair or rocket combination."""
    if len(cards) != 2:
        return None

    if ranks[0] == JOKER_SMALL_RANK and ranks[1] == JOKER_BIG_RANK:
        return Combination(ROCKET, JOKER_BIG_RANK, 2, list(cards))

    if ranks[0] == ranks[1]:
        return Combination(PAIR, ranks[0], 1, list(cards))

    return None


def _identify_triple(cards: List[Card], ranks: List[int],
                     grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify triple combination."""
    if len(cards) != 3:
        return None

    if len(grouped) == 1:
        return Combination(TRIPLE, ranks[0], 1, list(cards))

    return None


def _identify_bomb_or_triple_single(cards: List[Card], ranks: List[int],
                                     grouped: Dict[int, List[Card]],
                                     counts: List[int]) -> Optional[Combination]:
    """Identify bomb or triple with single combination."""
    if len(cards) != 4:
        return None

    if len(grouped) == 1:
        return Combination(BOMB, ranks[0], 1, list(cards))

    if 3 in counts and 1 in counts and len(grouped) == 2:
        triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
        return Combination(TRIPLE_SINGLE, triple_rank, 1, list(cards))

    return None


def _identify_triple_pair(cards: List[Card], grouped: Dict[int, List[Card]],
                          counts: List[int]) -> Optional[Combination]:
    """Identify triple with pair combination."""
    if len(cards) != 5 or 3 not in counts or 2 not in counts or len(grouped) != 2:
        return None

    triple_rank = max(grouped.keys(), key=lambda r: len(grouped[r]))
    return Combination(TRIPLE_PAIR, triple_rank, 1, list(cards))


def _identify_straight(cards: List[Card], ranks: List[int],
                       grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify straight combination."""
    if len(grouped) != len(cards) or len(cards) < MIN_STRAIGHT_LENGTH:
        return None

    if _valid_sequence_ranks(ranks) and _is_consecutive(ranks):
        return Combination(STRAIGHT, max(ranks), len(cards), list(cards))

    return None


def _identify_pair_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify pair sequence combination."""
    if len(cards) % 2 != 0:
        return None

    pair_ranks = [r for r, cs in grouped.items() if len(cs) == 2]

    if len(pair_ranks) * 2 != len(cards) or len(pair_ranks) < MIN_PAIR_SEQUENCE_LENGTH:
        return None

    sorted_pair_ranks = sorted(pair_ranks)
    if _valid_sequence_ranks(sorted_pair_ranks) and _is_consecutive(sorted_pair_ranks):
        return Combination(PAIR_SEQUENCE, max(sorted_pair_ranks), len(pair_ranks), list(cards))

    return None


def _identify_triple_sequence(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify triple sequence combination."""
    if len(cards) % 3 != 0:
        return None

    triple_ranks = [r for r, cs in grouped.items() if len(cs) == 3]

    if len(triple_ranks) * 3 != len(cards) or len(triple_ranks) < MIN_TRIPLE_SEQUENCE_LENGTH:
        return None

    sorted_triple_ranks = sorted(triple_ranks)
    if _valid_sequence_ranks(sorted_triple_ranks) and _is_consecutive(sorted_triple_ranks):
        return Combination(TRIPLE_SEQUENCE, max(sorted_triple_ranks), len(triple_ranks), list(cards))

    return None


def _identify_four_two_single(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify four with two singles combination."""
    if len(cards) != FOUR_TWO_SINGLE_SIZE:
        return None

    four_ranks = [r for r, cs in grouped.items() if len(cs) == 4]

    if len(four_ranks) != 1:
        return None

    single_count = sum(1 for r, cs in grouped.items() if len(cs) == 1)
    if single_count == 2:
        return Combination(FOUR_TWO_SINGLE, four_ranks[0], 1, list(cards))

    return None


def _identify_four_two_pair(cards: List[Card], grouped: Dict[int, List[Card]]) -> Optional[Combination]:
    """Identify four with two pairs combination."""
    if len(cards) != FOUR_TWO_PAIR_SIZE:
        return None

    four_ranks = [r for r, cs in grouped.items() if len(cs) == 4]

    if len(four_ranks) != 1:
        return None

    pair_count = sum(1 for r, cs in grouped.items() if len(cs) == 2)
    if pair_count == 2:
        return Combination(FOUR_TWO_PAIR, four_ranks[0], 1, list(cards))

    return None


def _identify_triple_sequence_single(cards: List[Card], grouped: Dict[int, List[Card]],
                                      count_map: Counter) -> Optional[Combination]:
    """Identify airplane with single wings combination."""
    if len(cards) % 4 != 0 or len(cards) < TRIPLE_SEQUENCE_SINGLE_MIN_SIZE:
        return None

    num_triples = len(cards) // 4
    triple_ranks = [r for r, cs in grouped.items() if len(cs) >= 3]
    valid_triple_ranks = sorted([r for r in triple_ranks if MIN_SEQ_RANK <= r <= MAX_SEQ_RANK])

    run = _find_consecutive_run(valid_triple_ranks, num_triples)
    if not run or len(run) != num_triples:
        return None

    # Calculate available singles excluding triple run ranks
    leftover_counts = count_map.copy()
    for triple_rank in run:
        leftover_counts[triple_rank] -= 3

    singles_available = sum(cnt for r, cnt in leftover_counts.items()
                           if r not in run and cnt > 0)

    if singles_available >= num_triples:
        return Combination(TRIPLE_SEQUENCE_SINGLE, max(run), num_triples, list(cards),
                          extra={'triples': run})

    return None


def _identify_triple_sequence_pair(cards: List[Card], grouped: Dict[int, List[Card]],
                                    count_map: Counter) -> Optional[Combination]:
    """Identify airplane with pair wings combination."""
    if len(cards) % 5 != 0 or len(cards) < TRIPLE_SEQUENCE_PAIR_MIN_SIZE:
        return None

    num_triples = len(cards) // 5
    triple_ranks = [r for r, cs in grouped.items() if len(cs) >= 3]
    valid_triple_ranks = sorted([r for r in triple_ranks if MIN_SEQ_RANK <= r <= MAX_SEQ_RANK])

    run = _find_consecutive_run(valid_triple_ranks, num_triples)
    if not run or len(run) != num_triples:
        return None

    # Calculate available pairs excluding triple run ranks
    leftover_counts = count_map.copy()
    for triple_rank in run:
        leftover_counts[triple_rank] -= 3

    pairs_available = sum(leftover_counts[r] // 2 for r in leftover_counts.keys()
                         if r not in run)

    if pairs_available >= num_triples:
        return Combination(TRIPLE_SEQUENCE_PAIR, max(run), num_triples, list(cards),
                          extra={'triples': run})

    return None


def identify_combination(cards: List[Card]) -> Optional[Combination]:
    """
    Identify the combination type from a list of cards according to Dou Dizhu rules.

    Args:
        cards: List of Card objects to analyze.

    Returns:
        Combination object if valid combination found, None otherwise.
    """
    if not cards:
        return None

    ranks = sorted(_extract_ranks(cards))
    grouped = _group_cards_by_rank(cards)
    counts = _get_count_distribution(grouped)
    count_map = Counter(ranks)

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

    result = _identify_bomb_or_triple_single(cards, ranks, grouped, counts)
    if result:
        return result

    result = _identify_triple_pair(cards, grouped, counts)
    if result:
        return result

    # Try sequence combinations
    result = _identify_straight(cards, ranks, grouped)
    if result:
        return result

    result = _identify_pair_sequence(cards, grouped)
    if result:
        return result

    result = _identify_triple_sequence(cards, grouped)
    if result:
        return result

    result = _identify_four_two_single(cards, grouped)
    if result:
        return result

    result = _identify_four_two_pair(cards, grouped)
    if result:
        return result

    result = _identify_triple_sequence_single(cards, grouped, count_map)
    if result:
        return result

    result = _identify_triple_sequence_pair(cards, grouped, count_map)
    if result:
        return result

    return None


def _can_beat_with_same_type(new_comb: Combination, prev_comb: Combination) -> bool:
    """
    Check if new combination beats previous combination of same type.

    Args:
        new_comb: New combination to play.
        prev_comb: Previous combination to beat.

    Returns:
        True if new_comb beats prev_comb, False otherwise.
    """
    # Sequence types require matching length
    if new_comb.type in (STRAIGHT, PAIR_SEQUENCE, TRIPLE_SEQUENCE,
                         TRIPLE_SEQUENCE_SINGLE, TRIPLE_SEQUENCE_PAIR):
        if new_comb.length != prev_comb.length:
            return False

    # All same-type comparisons use main_rank
    return new_comb.main_rank > prev_comb.main_rank


def can_beat(new_comb: Combination, prev_comb: Optional[Combination]) -> bool:
    """
    Determine if new combination legally beats previous combination.

    Args:
        new_comb: New combination to play.
        prev_comb: Previous combination to beat (None if first play).

    Returns:
        True if new_comb beats prev_comb, False otherwise.

    Raises:
        ValueError: If new_comb is None.