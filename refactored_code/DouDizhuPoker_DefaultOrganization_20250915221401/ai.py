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
    Basic heuristic AI for Dou Dizhu card game.
    
    Implements bidding strategy based on hand strength evaluation and play decisions
    that attempt to play the smallest winning combination or prefer sequences when starting.
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
        
        Evaluates jokers, twos, high cards, triples, bombs, and straight potential.
        
        Args:
            hand: List of cards in hand
            
        Returns:
            Numeric strength score
        """
        ranks = [c.rank for c in hand]
        rank_counts = Counter(ranks)
        score = 0

        # Score jokers
        score += JOKER_BIG_SCORE if BIG_JOKER_RANK in rank_counts else 0
        score += JOKER_SMALL_SCORE if SMALL_JOKER_RANK in rank_counts else 0

        # Score twos
        score += TWO_SCORE * rank_counts.get(TWO_RANK, 0)

        # Score high cards (A, K)
        score += HIGH_CARD_SCORE * (rank_counts.get(14, 0) + rank_counts.get(13, 0))

        # Score triples and bombs
        score += TRIPLE_SCORE * sum(1 for count in rank_counts.values() if count >= 3)
        score += BOMB_SCORE * sum(1 for count in rank_counts.values() if count == 4)

        # Score straight potential
        valid_ranks = sorted(set(r for r in rank_counts.keys() if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK))
        longest_run = self._longest_consecutive_sequence(valid_ranks)
        score += max(0, longest_run - STRAIGHT_BONUS_THRESHOLD)

        return score

    def _longest_consecutive_sequence(self, values: List[int]) -> int:
        """
        Find the longest consecutive sequence in a sorted list of integers.
        
        Args:
            values: Sorted list of unique integers
            
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
        Choose which cards to play.
        
        Args:
            hand: List of cards in hand
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
        
        Prefers plays that shed more cards (sequences over singles).
        
        Args:
            hand: Sorted list of cards in hand
            
        Returns:
            List of cards to play, or None
        """
        # Try plays in order of preference (more cards shed first)
        play_generators = [
            self._find_low_straight_start,
            self._find_low_pair_sequence_start,
            self._find_low_triple_sequence_start,
            self._find_triple_with_attachment_start,
            self._find_low_pair_start,
            self._find_low_single_start,
            self._find_bomb_if_small,
        ]

        for generator in play_generators:
            play = generator(hand)
            if play:
                return play

        return self._find_rocket(hand)

    def _choose_beating_play(self, hand: List[Card], last_comb: Combination) -> Optional[List[Card]]:
        """
        Choose a play to beat the previous combination.
        
        Args:
            hand: Sorted list of cards in hand
            last_comb: Combination to beat
            
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

        # If last was a bomb, try higher bomb or rocket
        if last_comb.type == BOMB:
            bomb = self._find_bomb_to_beat(hand, last_comb)
            if bomb:
                return bomb
            rocket = self._find_rocket(hand)
            if rocket:
                return rocket

        return None

    def _find_low_single_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest single card to play, avoiding 2s and jokers if possible."""
        candidates = [c for c in hand if c.rank <= MAX_STRAIGHT_RANK]
        if not candidates:
            candidates = hand[:]
        return [candidates[0]] if candidates else None

    def _find_low_pair_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest pair to play, preferring ranks below 2."""
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() if count >= 2])
        
        # Prefer pairs below 2
        pair_ranks = [r for r in pair_ranks if r <= MAX_STRAIGHT_RANK] or pair_ranks
        
        if pair_ranks:
            rank = pair_ranks[0]
            return [c for c in hand if c.rank == rank][:2]
        return None

    def _find_triple_with_attachment_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest triple, optionally with a single attachment."""
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() 
                              if count >= 3 and MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK])
        
        if not triple_ranks:
            return None

        triple_rank = triple_ranks[0]
        triple_cards = [c for c in hand if c.rank == triple_rank][:3]
        
        # Try to add a single attachment
        singles = [c for c in hand if c.rank != triple_rank]
        if singles:
            # Prefer non-joker singles
            singles = self._sort_by_joker_preference(singles)
            attempt = triple_cards + [singles[0]]
            if identify_combination(attempt):
                return attempt

        return triple_cards

    def _find_low_straight_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest straight (5+ consecutive ranks)."""
        valid_ranks = sorted(set(c.rank for c in hand if MIN_STRAIGHT_RANK <= c.rank <= MAX_STRAIGHT_RANK))
        
        for length in range(MIN_STRAIGHT_LENGTH, MAX_STRAIGHT_LENGTH):
            for i in range(len(valid_ranks) - length + 1):
                sequence = valid_ranks[i:i + length]
                if self._is_consecutive(sequence):
                    cards = self._extract_cards_by_ranks(hand, sequence)
                    if identify_combination(cards):
                        return cards
        return None

    def _find_low_pair_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest pair sequence (3+ consecutive pairs)."""
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() 
                            if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= 2])
        
        for length in range(MIN_PAIR_SEQUENCE_LENGTH, MAX_PAIR_SEQUENCE_LENGTH):
            for i in range(len(pair_ranks) - length + 1):
                sequence = pair_ranks[i:i + length]
                if self._is_consecutive(sequence):
                    cards = self._extract_cards_by_ranks(hand, sequence, count_per_rank=2)
                    if identify_combination(cards):
                        return cards
        return None

    def _find_low_triple_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest triple sequence (2+ consecutive triples)."""
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() 
                              if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= 3])
        
        for length in range(MIN_TRIPLE_SEQUENCE_LENGTH, MAX_TRIPLE_SEQUENCE_LENGTH):
            for i in range(len(triple_ranks) - length + 1):
                sequence = triple_ranks[i:i + length]
                if self._is_consecutive(sequence):
                    cards = self._extract_cards_by_ranks(hand, sequence, count_per_rank=3)
                    if identify_combination(cards):
                        return cards
        return None

    def _find_bomb_if_small(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find lowest bomb (4 of a kind)."""
        rank_counts = Counter(c.rank for c in hand)
        bomb_ranks = sorted([r for r, count in rank_counts.items() if count == 4])
        
        if bomb_ranks:
            rank = bomb_ranks[0]
            return [c for c in hand if c.rank == rank][:4]
        return None

    def _find_rocket(self, hand: List[Card]) -> Optional[List[Card]]:
        """Find rocket (both jokers)."""
        small_joker = [c for c in hand if c.rank == SMALL_JOKER_RANK]
        big_joker = [c for c in hand if c.rank == BIG_JOKER_RANK]
        
        if small_joker and big_joker:
            return [small_joker[0], big_joker[0]]
        return None

    def _find_to_beat(self, hand: List[Card], last: Combination) -> Optional[List[Card]]:
        """
        Find a play that beats the given combination.
        
        Args:
            hand: Cards in hand
            last: Combination to beat
            
        Returns:
            Beating combination, or None
        """
        beat_methods = {
            SINGLE: self._beat_single,
            PAIR: self._beat_pair,
            TRIPLE: self._beat_triple,
            TRIPLE_SINGLE: self._beat_triple_single,
            TRIPLE_PAIR: self._beat_triple_pair,
            STRAIGHT: self._beat_straight,
            PAIR_SEQUENCE: self._beat_pair_sequence,
            TRIPLE_SEQUENCE: self._beat_triple_sequence,
            TRIPLE_SEQUENCE_SINGLE: lambda h, r: self._beat_triple_sequence_with_wings(h, last.length, r, "single"),
            TRIPLE_SEQUENCE_PAIR: lambda h, r: self._beat_triple_sequence_with_wings(h, last.length, r, "pair"),
            BOMB: self._beat_bomb,
            FOUR_TWO_SINGLE: self._beat_four_two_single,
            FOUR_TWO_PAIR: self._beat_four_two_pair,
        }

        beat_method = beat_methods.get(last.type)
        if beat_method:
            try:
                return beat_method(hand, last.main_rank)
            except (AttributeError, TypeError) as e:
                logger.warning(f"Error beating {last.type}: {e}")
                return None

        return None

    def _beat_single(self, hand: List[Card], rank: int) -> Optional[List[Card]]:
        """Find lowest single card that beats the given rank."""
        candidates = sorted([c for c in hand if c.rank > rank], 
                          key=lambda c: (c.rank, c.sort_key()[1]))
        return [candidates[0]] if candidates else None

    def _beat_pair(self, hand: List[Card], rank: int) -> Optional[List[Card]]:
        """Find lowest pair that beats the given rank."""
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() if count >= 2 and r > rank])
        
        if pair_ranks:
            rank = pair_ranks[0]
            return [c for c in hand if c.rank == rank][:2]
        return None

    def _beat_triple(self, hand: List[Card], rank: int) -> Optional[List[Card]]: