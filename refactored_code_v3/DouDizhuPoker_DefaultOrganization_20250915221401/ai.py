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

# Bidding constants
BID_THRESHOLD_HIGH = 16
BID_THRESHOLD_MID = 11
BID_THRESHOLD_LOW = 7
BID_HIGH = 3
BID_MID = 2
BID_LOW = 1
BID_PASS = 0

# Hand strength scoring constants
JOKER_BIG_SCORE = 5
JOKER_SMALL_SCORE = 4
TWO_SCORE = 3
HIGH_CARD_SCORE = 2
TRIPLE_SCORE = 3
BOMB_SCORE = 5
STRAIGHT_BONUS_THRESHOLD = 4

# Card rank constants
JOKER_BIG_RANK = 17
JOKER_SMALL_RANK = 16
TWO_RANK = 15
ACE_RANK = 14
KING_RANK = 13
MIN_STRAIGHT_RANK = 3
MAX_STRAIGHT_RANK = 14

# Sequence length constants
MIN_STRAIGHT_LENGTH = 5
MAX_STRAIGHT_LENGTH = 13
MIN_PAIR_SEQUENCE_LENGTH = 3
MAX_PAIR_SEQUENCE_LENGTH = 11
MIN_TRIPLE_SEQUENCE_LENGTH = 2
MAX_TRIPLE_SEQUENCE_LENGTH = 7

# Card count constants
PAIR_COUNT = 2
TRIPLE_COUNT = 3
BOMB_COUNT = 4
WING_PAIR_COUNT = 2


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
            Bid amount (0-3), or 0 to pass
        """
        score = self._hand_strength_score(hand)
        
        # Map score to bid level
        if score >= BID_THRESHOLD_HIGH:
            bid = BID_HIGH
        elif score >= BID_THRESHOLD_MID:
            bid = BID_MID
        elif score >= BID_THRESHOLD_LOW:
            bid = BID_LOW
        else:
            bid = BID_PASS
        
        # Must exceed current highest bid
        return bid if bid > highest_bid else BID_PASS

    def _hand_strength_score(self, hand: List[Card]) -> int:
        """
        Calculate numerical strength score of a hand.
        
        Evaluates presence of high-value cards, bombs, and straight potential.
        
        Args:
            hand: List of cards to evaluate
            
        Returns:
            Numerical strength score
        """
        ranks = [c.rank for c in hand]
        rank_counts = Counter(ranks)
        score = 0
        
        # Score jokers
        score += JOKER_BIG_SCORE if JOKER_BIG_RANK in rank_counts else 0
        score += JOKER_SMALL_SCORE if JOKER_SMALL_RANK in rank_counts else 0
        
        # Score twos
        score += TWO_SCORE * rank_counts.get(TWO_RANK, 0)
        
        # Score high cards (A, K)
        score += HIGH_CARD_SCORE * (rank_counts.get(ACE_RANK, 0) + rank_counts.get(KING_RANK, 0))
        
        # Score triples and bombs
        score += TRIPLE_SCORE * sum(1 for count in rank_counts.values() if count >= TRIPLE_COUNT)
        score += BOMB_SCORE * sum(1 for count in rank_counts.values() if count == BOMB_COUNT)
        
        # Score straight potential
        valid_ranks = sorted(set(r for r in rank_counts.keys() if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK))
        longest_run = self._longest_consecutive_sequence(valid_ranks)
        score += max(0, longest_run - STRAIGHT_BONUS_THRESHOLD)
        
        return score

    def _longest_consecutive_sequence(self, values: List[int]) -> int:
        """
        Find length of longest consecutive sequence in sorted values.
        
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
        
        When starting a trick, prefers combinations that shed more cards.
        When responding, attempts to beat the previous play or passes.
        
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
            return self._choose_response_play(hand, last_comb)

    def _choose_starting_play(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Select a play when starting a new trick.
        
        Prefers sequences and multi-card combinations to shed more cards.
        
        Args:
            hand: Sorted list of cards
            
        Returns:
            List of cards to play, or None
        """
        # Priority order: straight, pair sequence, triple sequence, triple+attachment, pair, single, bomb, rocket
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

    def _choose_response_play(self, hand: List[Card], last_comb: Combination) -> Optional[List[Card]]:
        """
        Select a play when responding to opponent's combination.
        
        Attempts to beat with same type, then considers bombs/rocket.
        
        Args:
            hand: Sorted list of cards
            last_comb: Combination to beat
            
        Returns:
            List of cards to play, or None to pass
        """
        # Try to beat with same combination type
        play = self._find_to_beat(hand, last_comb)
        if play:
            return play
        
        # If cannot beat, try bombs and rocket
        if last_comb.type not in (BOMB, ROCKET):
            bomb = self._find_bomb_to_beat(hand, None)
            if bomb:
                return bomb
            
            rocket = self._find_rocket(hand)
            if rocket:
                return rocket
        elif last_comb.type == BOMB:
            bomb = self._find_bomb_to_beat(hand, last_comb)
            if bomb:
                return bomb
            
            rocket = self._find_rocket(hand)
            if rocket:
                return rocket
        
        return None

    def _find_low_single_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest single card to play, avoiding 2s and jokers if possible.
        
        Args:
            hand: List of cards
            
        Returns:
            Single card as list, or None
        """
        candidates = [c for c in hand if c.rank <= MAX_STRAIGHT_RANK]
        if not candidates:
            candidates = hand
        
        return [candidates[0]] if candidates else None

    def _find_low_pair_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest pair to play, preferring ranks below 2.
        
        Args:
            hand: List of cards
            
        Returns:
            Pair as list, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() if count >= PAIR_COUNT])
        
        # Prefer pairs below rank 2
        preferred = [r for r in pair_ranks if r <= MAX_STRAIGHT_RANK]
        target_rank = preferred[0] if preferred else (pair_ranks[0] if pair_ranks else None)
        
        if target_rank:
            return [c for c in hand if c.rank == target_rank][:PAIR_COUNT]
        
        return None

    def _find_triple_with_attachment_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest triple with single or pair attachment.
        
        Args:
            hand: List of cards
            
        Returns:
            Triple with attachment as list, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() 
                              if count >= TRIPLE_COUNT and MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK])
        
        if not triple_ranks:
            return None
        
        triple_rank = triple_ranks[0]
        triple_cards = [c for c in hand if c.rank == triple_rank][:TRIPLE_COUNT]
        
        # Try triple + single
        singles = [c for c in hand if c.rank != triple_rank]
        if singles:
            combination = triple_cards + [singles[0]]
            if identify_combination(combination):
                return combination
        
        # Return triple alone if no attachment available
        return triple_cards

    def _find_low_straight_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest straight of length >= 5.
        
        Args:
            hand: List of cards
            
        Returns:
            Straight as list, or None
        """
        valid_ranks = sorted(set(c.rank for c in hand if MIN_STRAIGHT_RANK <= c.rank <= MAX_STRAIGHT_RANK))
        
        for length in range(MIN_STRAIGHT_LENGTH, MAX_STRAIGHT_LENGTH):
            for start_idx in range(len(valid_ranks) - length + 1):
                sequence = valid_ranks[start_idx:start_idx + length]
                
                if self._is_consecutive(sequence):
                    cards = self._extract_cards_by_ranks(hand, sequence)
                    if identify_combination(cards):
                        return cards
        
        return None

    def _find_low_pair_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest pair sequence of length >= 3.
        
        Args:
            hand: List of cards
            
        Returns:
            Pair sequence as list, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        pair_ranks = sorted([r for r, count in rank_counts.items() 
                            if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= PAIR_COUNT])
        
        for length in range(MIN_PAIR_SEQUENCE_LENGTH, MAX_PAIR_SEQUENCE_LENGTH):
            for start_idx in range(len(pair_ranks) - length + 1):
                sequence = pair_ranks[start_idx:start_idx + length]
                
                if self._is_consecutive(sequence):
                    cards = self._extract_pairs_by_ranks(hand, sequence)
                    if identify_combination(cards):
                        return cards
        
        return None

    def _find_low_triple_sequence_start(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest triple sequence of length >= 2.
        
        Args:
            hand: List of cards
            
        Returns:
            Triple sequence as list, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        triple_ranks = sorted([r for r, count in rank_counts.items() 
                              if MIN_STRAIGHT_RANK <= r <= MAX_STRAIGHT_RANK and count >= TRIPLE_COUNT])
        
        for length in range(MIN_TRIPLE_SEQUENCE_LENGTH, MAX_TRIPLE_SEQUENCE_LENGTH):
            for start_idx in range(len(triple_ranks) - length + 1):
                sequence = triple_ranks[start_idx:start_idx + length]
                
                if self._is_consecutive(sequence):
                    cards = self._extract_triples_by_ranks(hand, sequence)
                    if identify_combination(cards):
                        return cards
        
        return None

    def _find_bomb_if_small(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find lowest bomb (four-of-a-kind).
        
        Args:
            hand: List of cards
            
        Returns:
            Bomb as list, or None
        """
        rank_counts = Counter(c.rank for c in hand)
        bomb_ranks = sorted([r for r, count in rank_counts.items() if count == BOMB_COUNT])
        
        if bomb_ranks:
            return [c for c in hand if c.rank == bomb_ranks[0]][:BOMB_COUNT]
        
        return None

    def _find_rocket(self, hand: List[Card]) -> Optional[List[Card]]:
        """
        Find rocket (both jokers).
        
        Args:
            hand: List of cards
            
        Returns:
            Rocket as list, or None
        """
        small_joker = [c for c in hand if c.rank == JOKER_SMALL_RANK]
        big_joker = [c for c in hand if c.rank == JOKER_BIG_RANK]
        
        if small_joker and big_joker:
            return [small_joker[0], big_joker[0]]
        
        return None

    def _find_to_beat(self, hand: List[Card], last: Combination) -> Optional[List[Card]]:
        """
        Find a combination to beat the last play.
        
        Dispatches to type-specific beating methods.
        
        Args:
            hand: List of cards
            last: Combination to beat
            
        Returns:
            Beating combination as list, or None
        """
        beating_methods = {
            SINGLE: lambda: self._beat_single(hand, last.main_rank),
            PAIR: lambda: self._beat_pair(hand, last.main_rank),
            TRIPLE: lambda: self._beat_triple(hand, last.main_rank),
            TRIPLE_SINGLE: lambda: self._beat_triple_single(hand, last.main_rank),
            TRIPLE_PAIR: lambda: self._beat_triple_pair(hand, last.main_rank),
            STRAIGHT: lambda: self._beat_straight(hand, last.length, last.main_rank),
            PAIR_SEQUENCE: lambda: self._beat_pair_sequence