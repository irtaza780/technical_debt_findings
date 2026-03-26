import logging
from typing import List, Optional
from collections import Counter
from models import Card, sort_cards
from rules import (
    Combination, identify_combination, can_beat,
    SINGLE, PAIR, TRIPLE, TRIPLE_SINGLE, TRIPLE_PAIR,
    STRAIGHT, PAIR_SEQUENCE, TRIPLE_SEQUENCE,
    TRIPLE_SEQUENCE_SINGLE, TRIPLE_SEQUENCE_PAIR,
    BOMB, ROCKET, FOUR_TWO_SINGLE, FOUR_TWO_PAIR
)

logger = logging.getLogger(__name__)

# Hand strength scoring constants
JOKER_BIG_SCORE = 5
JOKER_SMALL_SCORE = 4
TWO_SCORE = 3
HIGH_CARD_SCORE = 2
TRIPLE_SCORE = 3
BOMB_SCORE = 5
STRAIGHT_BONUS_THRESHOLD = 4

# Bidding thresholds
BID_3_THRESHOLD = 16
BID_2_THRESHOLD = 11
BID_1_THRESHOLD = 7

# Card rank boundaries
MIN_STRAIGHT_RANK = 3
MAX_STRAIGHT_RANK = 14
TWO_RANK = 15
SMALL_JOKER_RANK = 16
BIG_JOKER_RANK = 17

# Sequence lengths
MIN_STRAIGHT_LENGTH = 5
MAX_STRAIGHT_LENGTH = 13
MIN_PAIR_SEQUENCE_LENGTH = 3
MAX_PAIR_SEQUENCE_LENGTH = 11
MIN_TRIPLE_SEQUENCE_LENGTH = 2
MAX_TRIPLE_SEQUENCE_LENGTH = 7


class SimpleAI:
    """
    Basic heuristic AI for Dou Dizhu:
    - Bidding: evaluates hand strength and bids 0-3 accordingly.
    - Play: attempts to play the smallest winning combination, prefers sequences when starting.
    """

    def decide_bid(self, hand: List[Card], highest_bid: int) -> int:
        """
        Determine bid amount based on hand strength.

        Args:
            hand: List of cards in player's hand
            highest_bid: Current highest bid to beat

        Returns:
            Bid amount (0-3), or 0 if cannot exceed highest_bid
        """
        score = self._hand_strength_score(hand)
        bid = self._score_to_bid(score)

        if bid <= highest_bid:
            return 0
        return bid

    def _score_to_bid(self, score: int) -> int:
        """
        Convert hand strength score to bid amount.

        Args:
            score: Hand strength score

        Returns:
            Bid amount (0-3)
        """
        if score >= BID_3_THRESHOLD:
            return 3
        elif score >= BID_2_THRESHOLD:
            return 2
        elif score >= BID_1_THRESHOLD:
            return 1
        return 0

    def _hand_strength_score(self, hand: List[Card]) -> int:
        """
        Calculate overall hand strength score.

        Args:
            hand: List of cards in player's hand

        Returns:
            Numeric strength score
        """
        ranks = [c.rank for c in hand]
        rank_counts = Counter(ranks)
        score = 0

        # Score special cards
        score += self._score_jokers(rank_counts)
        score += self._score_twos(rank_counts)
        score += self._score_high_cards(rank_counts)
        score += self._score_multiples(rank_counts)
        score += self._score_straight_potential(rank_counts)

        return score

    def _score_jokers(self, rank_counts: Counter) -> int:
        """Score jokers in hand."""
        score = 0
        if BIG_JOKER_RANK in rank_counts:
            score += JOKER_BIG_SCORE
        if SMALL_JOKER_RANK in rank_counts:
            score += JOKER_SMALL_SCORE
        return score

    def _score_twos(self, rank_counts: Counter) -> int:
        """Score twos in hand."""
        return TWO_SCORE * rank_counts.get(TWO_RANK, 0)

    def _score_high_cards(self, rank_counts: Counter) -> int:
        """Score aces and kings in hand."""
        return HIGH_CARD_SCORE * (rank_counts.get(14, 0) + rank_counts.get(13, 0))

    def _score_multiples(self, rank_counts: Counter) -> int:
        """Score triples and bombs in hand."""
        score = 0
        score += TRIPLE_SCORE * sum(1 for count in rank_counts.values() if count >= 3)
        score += BOMB_SCORE * sum(1 for count in rank_counts.values() if count == 4)
        return score

    def _score_straight_potential(self, rank_counts: Counter) -> int:
        """Score potential for straights in hand."""
        valid_ranks = sorted(set(r for r in rank_counts.keys() if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK))
        longest_run = self._longest_consecutive_sequence(valid_ranks)
        return max(0, longest_run - STRAIGHT_BONUS_THRESHOLD)

    def _longest_consecutive_sequence(self, values: List[int]) -> int:
        """
        Find the longest consecutive sequence in a sorted list of integers.

        Args:
            values: Sorted list of integers

        Returns:
            Length of longest consecutive sequence
        """
        if not values:
            return 0

        longest = current = 1
        for i in range(len(values) - 1):
            if values[i + 1] == values[i] + 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest

    def choose_play(self, hand: List[Card], last_comb: Optional[Combination], is_start: bool) -> Optional[List[Card]]:
        """
        Determine which cards to play.

        Args:
            hand: List of cards in player's hand
            last_comb: Previous combination to beat, or None if starting
            is_start: Whether this player is starting the trick

        Returns:
            List of cards to play, or None to pass
        """
        hand = sort_cards(hand)

        if is_start or last_comb is None:
            return self._choose_starting_play(hand)
        else:
            return self._choose_beating_play(hand, last_comb)

    def _choose_starting_play(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Choose a play when starting a new trick.
        Prefers plays that shed more cards.

        Args:
            hand: Sorted list of cards in player's hand

        Returns:
            List of cards to play, or None
        """
        generators = [
            self._find_low_straight_start,
            self._find_low_pair_sequence_start,
            self._find_low_triple_sequence_start,
            self._find_triple_with_attachment_start,
            self._find_low_pair_start,
            self._find_low_single_start,
            self._find_bomb_if_small,
        ]

        for generator in generators:
            play = generator(hand)
            if play:
                return play

        return self._find_rocket(hand)

    def _choose_beating_play(self, hand: List[Card], last_comb: Combination) -> Optional[List[Card]]:
        """
        Choose a play to beat the previous combination.

        Args:
            hand: Sorted list of cards in player's hand
            last_comb: Previous combination to beat

        Returns:
            List of cards to play, or None to pass
        """
        # Try to beat with same combination type
        play = self._find_to_beat(hand, last_comb)
        if play:
            return play

        # Try bombs if last wasn't a bomb or rocket
        if last_comb.type not in (BOMB, ROCKET):
            bomb = self._find_bomb_to_beat(hand, None)
            if bomb:
                return bomb

        # Try rocket as last resort
        rocket = self._find_rocket(hand)
        if rocket:
            return rocket

        return None

    def _find_low_single_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest single card to play, avoiding 2s and jokers if possible.

        Args:
            hand: List of cards in player's hand

        Returns:
            List containing single card, or None
        """
        candidates = [c for c in hand if c.rank <= MAX_STRAIGHT_RANK]
        if not candidates:
            candidates = hand

        return [candidates[0]] if candidates else None

    def _find_low_pair_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest pair to play, preferring ranks below 2.

        Args:
            hand: List of cards in player's hand

        Returns:
            List containing pair, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() if count >= 2])

        # Prefer pairs below 2
        preferred = [r for r in pair_ranks if r <= MAX_STRAIGHT_RANK] or pair_ranks

        if preferred:
            rank = preferred[0]
            return [c for c in hand if c.rank == rank][:2]

        return None

    def _find_triple_with_attachment_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest triple with single attachment to play.

        Args:
            hand: List of cards in player's hand

        Returns:
            List containing triple with attachment, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() if count >= 3 and MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK])

        if not triple_ranks:
            return None

        triple_rank = triple_ranks[0]
        triple_cards = [c for c in hand if c.rank == triple_rank][:3]
        singles = [c for c in hand if c.rank != triple_rank]

        # Prefer non-joker singles
        non_joker_singles = [c for c in singles if c.rank < SMALL_JOKER_RANK]
        singles_to_use = non_joker_singles or singles

        if singles_to_use:
            combination = triple_cards + [singles_to_use[0]]
            if identify_combination(combination):
                return combination

        return triple_cards

    def _find_low_straight_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest straight (length >= 5) to play.

        Args:
            hand: List of cards in player's hand

        Returns:
            List of cards forming straight, or None
        """
        valid_ranks = sorted(set(c.rank for c in hand if MIN_STRAIGHT_RANK <= c.rank <= MAX_STRAIGHT_RANK))

        for length in range(MIN_STRAIGHT_LENGTH, MAX_STRAIGHT_LENGTH):
            for start_idx in range(len(valid_ranks) - length + 1):
                sequence = valid_ranks[start_idx:start_idx + length]

                if self._is_consecutive(sequence):
                    chosen = self._extract_cards_for_ranks(hand, sequence)
                    if identify_combination(chosen):
                        return chosen

        return None

    def _find_low_pair_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest pair sequence (length >= 3) to play.

        Args:
            hand: List of cards in player's hand

        Returns:
            List of cards forming pair sequence, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= 2])

        for length in range(MIN_PAIR_SEQUENCE_LENGTH, MAX_PAIR_SEQUENCE_LENGTH):
            for start_idx in range(len(pair_ranks) - length + 1):
                sequence = pair_ranks[start_idx:start_idx + length]

                if self._is_consecutive(sequence):
                    chosen = []
                    for rank in sequence:
                        chosen.extend([c for c in hand if c.rank == rank][:2])

                    if identify_combination(chosen):
                        return chosen

        return None

    def _find_low_triple_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest triple sequence (length >= 2) to play.

        Args:
            hand: List of cards in player's hand

        Returns:
            List of cards forming triple sequence, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= 3])

        for length in range(MIN_TRIPLE_SEQUENCE_LENGTH, MAX_TRIPLE_SEQUENCE_LENGTH):
            for start_idx in range(len(triple_ranks) - length + 1):
                sequence = triple_ranks[start_idx:start_idx + length]

                if self._is_consecutive(sequence):
                    chosen = []
                    for rank in sequence:
                        chosen.extend([c for c in hand if c.rank == rank][:3])

                    if identify_combination(chosen):
                        return chosen

        return None

    def _find_bomb_if_small(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest bomb (four-of-a-kind) to play.

        Args:
            hand: List of cards in player's hand

        Returns:
            List of four cards forming bomb, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        bomb_ranks = sorted([r for r, count in rank_counts.items() if count == 4])

        if bomb_ranks:
            rank = bomb_ranks[0]
            return [c for c in hand if c.rank == rank][:4]

        return None

    def _find_rocket(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find rocket (both jokers) in hand.

        Args:
            hand: List of cards in player's hand

        Returns:
            List containing both jokers, or None
        """
        small_joker = [c for c in hand if c.rank == SMALL_JOKER_RANK]
        big_joker = [c for c in hand if c.rank == BIG_JOKER_RANK]

        if small_joker and big_joker:
            return [small_joker[0], big_joker[0]]

        return None

    def _find_to_beat(self, hand: List[Card], last: Combination) -> Optional[List[Card]]:
        """
        Find a combination to beat the previous play.

        Args:
            hand: List of cards in player's hand
            last: Previous combination to beat

        Returns:
            List of cards to play, or None
        """
        beat_strategies = {
            SINGLE: lambda: self._beat_single(hand, last.main_rank),
            PAIR: lambda: self._beat_pair(hand, last.main_rank),
            TRIPLE: lambda: self._beat_triple(hand, last.main_rank),
            TRIPLE_SINGLE: lambda: self._beat_triple_single(hand, last.main_rank),
            TRIPLE_PAIR: lambda: self._beat_triple_pair(hand, last.main_rank),
            STRAIGHT: lambda: self._beat_straight(hand, last.length, last.main_rank),
            PAIR_SEQUENCE: lambda: self._beat_pair_sequence(hand, last.length, last.main_rank),
            TRIPLE_SEQUENCE: lambda: self._beat_triple_sequence(hand, last.length, last.main_