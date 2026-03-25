import logging
from typing import List, Optional, Tuple
from collections import deque
from models import Card, Deck, sort_cards
from rules import Combination, identify_combination, can_beat, ROCKET, BOMB
from ai import SimpleAI

# Constants
MIN_BID = 0
MAX_BID = 3
IMMEDIATE_LANDLORD_BID = 3
NUM_PLAYERS = 3
PASSES_FOR_REDEAL = 3
PASSES_FOR_BIDDING_END = 2
LANDLORD_ROLE = "landlord"
FARMER_ROLE = "farmer"
PHASE_DEAL = "deal"
PHASE_BIDDING = "bidding"
PHASE_PLAY = "play"
PHASE_FINISHED = "finished"

logger = logging.getLogger(__name__)


class Player:
    """
    Represents a player in Dou Dizhu with a hand of cards.
    
    Attributes:
        name: Player identifier
        is_human: Whether this is a human-controlled player
        hand: List of Card objects currently held
        role: Either 'landlord' or 'farmer'
    """
    
    def __init__(self, name: str, is_human: bool = False):
        """
        Initialize a player.
        
        Args:
            name: Player name/identifier
            is_human: True if human-controlled, False if AI
        """
        self.name = name
        self.is_human = is_human
        self.hand: List[Card] = []
        self.role: str = FARMER_ROLE

    def add_cards(self, cards: List[Card]) -> None:
        """
        Add cards to player's hand and sort.
        
        Args:
            cards: List of Card objects to add
        """
        self.hand.extend(cards)
        self.sort_hand()

    def sort_hand(self) -> None:
        """Sort player's hand using standard card ordering."""
        self.hand = sort_cards(self.hand)

    def remove_cards(self, cards: List[Card]) -> None:
        """
        Remove specific cards from player's hand.
        
        Args:
            cards: List of Card objects to remove (must be exact objects from hand)
        """
        for card in cards:
            self.hand.remove(card)

    def has_cards(self) -> bool:
        """Check if player has any cards remaining."""
        return len(self.hand) > 0


class DouDizhuGame:
    """
    Game engine managing state and flow of a Dou Dizhu round.
    
    Handles dealing, bidding, landlord assignment, play phase, and win conditions.
    """
    
    def __init__(self):
        """Initialize a new game instance."""
        self.players: List[Player] = [
            Player("Left AI"),
            Player("You", is_human=True),
            Player("Right AI")
        ]
        self.ai = SimpleAI()
        self.deck = Deck()
        self.bottom_cards: List[Card] = []
        self.landlord_idx: Optional[int] = None
        self.current_player_idx: int = 0
        self.phase: str = PHASE_DEAL
        self.highest_bid: int = MIN_BID
        self.best_bidder_idx: Optional[int] = None
        self.bids_since_highest: int = 0
        self.bid_turn_idx: int = 0
        self.last_combination: Optional[Combination] = None
        self.last_player_idx: Optional[int] = None
        self.message_log: List[str] = []

    def log(self, message: str) -> None:
        """
        Log a game message.
        
        Args:
            message: Message to log
        """
        self.message_log.append(message)
        logger.info(message)

    def start_new_round(self) -> None:
        """Initialize a new round with fresh deck and deal cards to players."""
        self.deck = Deck()
        hands, bottom = self.deck.deal()
        self.bottom_cards = bottom
        
        # Distribute cards to players
        for i, player in enumerate(self.players):
            player.role = FARMER_ROLE
            player.hand = hands[i]
            player.sort_hand()
        
        # Reset bidding state
        self.phase = PHASE_BIDDING
        self.highest_bid = MIN_BID
        self.best_bidder_idx = None
        self.bids_since_highest = 0
        self.bid_turn_idx = 0
        self.landlord_idx = None
        self.last_combination = None
        self.last_player_idx = None

    def get_state(self) -> dict:
        """
        Get current game state for UI rendering.
        
        Returns:
            Dictionary containing all relevant game state
        """
        return {
            "phase": self.phase,
            "players": self.players,
            "bottom": self.bottom_cards,
            "landlord_idx": self.landlord_idx,
            "current_idx": self.current_player_idx,
            "highest_bid": self.highest_bid,
            "best_bidder": self.best_bidder_idx,
            "last_comb": self.last_combination,
            "last_player": self.last_player_idx
        }

    def _advance_bidder(self) -> None:
        """Move to next player in bidding order."""
        self.bid_turn_idx = (self.bid_turn_idx + 1) % NUM_PLAYERS

    def _is_valid_bid(self, bid: int) -> bool:
        """
        Validate bid value.
        
        Args:
            bid: Bid amount to validate
            
        Returns:
            True if bid is valid (0-3 and higher than current highest)
        """
        if bid not in range(MIN_BID, MAX_BID + 1):
            return False
        if bid > MIN_BID and bid <= self.highest_bid:
            return False
        return True

    def _handle_immediate_landlord(self, idx: int) -> None:
        """
        Handle bid of 3 (immediate landlord assignment).
        
        Args:
            idx: Index of player bidding 3
        """
        self.highest_bid = IMMEDIATE_LANDLORD_BID
        self.best_bidder_idx = idx
        self.log(f"{self.players[idx].name} bids 3!")
        self.finish_bidding()

    def _handle_valid_bid(self, idx: int, bid: int) -> None:
        """
        Process a valid bid increase.
        
        Args:
            idx: Index of bidding player
            bid: Bid amount
        """
        self.highest_bid = bid
        self.best_bidder_idx = idx
        self.bids_since_highest = 0
        self.log(f"{self.players[idx].name} bids {bid}.")

    def _handle_pass(self, idx: int) -> None:
        """
        Process a pass action.
        
        Args:
            idx: Index of passing player
        """
        self.bids_since_highest += 1
        self.log(f"{self.players[idx].name} passes bidding.")

    def _check_bidding_end_conditions(self) -> bool:
        """
        Check if bidding should end or redeal.
        
        Returns:
            True if bidding ended or redeal started, False otherwise
        """
        # Two passes after a bid ends bidding
        if self.best_bidder_idx is not None and self.bids_since_highest >= PASSES_FOR_BIDDING_END:
            self.finish_bidding()
            return True
        
        # All three passes without any bid triggers redeal
        if self.best_bidder_idx is None and self.bids_since_highest >= PASSES_FOR_REDEAL:
            self.log("All players passed. Redealing...")
            self.start_new_round()
            return True
        
        return False

    def apply_bid(self, idx: int, bid: int) -> None:
        """
        Apply a bid action from a player.
        
        Args:
            idx: Index of bidding player
            bid: Bid amount (0-3, where 0 is pass)
        """
        if self.phase != PHASE_BIDDING:
            return
        
        # Normalize invalid bids to pass
        if not self._is_valid_bid(bid):
            bid = MIN_BID
        
        # Handle immediate landlord
        if bid == IMMEDIATE_LANDLORD_BID:
            self._handle_immediate_landlord(idx)
            return
        
        # Handle valid bid or pass
        if bid > MIN_BID:
            self._handle_valid_bid(idx, bid)
        else:
            self._handle_pass(idx)
        
        # Check end conditions
        if self._check_bidding_end_conditions():
            return
        
        # Move to next bidder
        self._advance_bidder()

    def process_ai_bid_if_needed(self) -> Optional[Tuple[int, int]]:
        """
        Process AI bid if current bidder is AI.
        
        Returns:
            Tuple of (player_idx, bid_value) if AI bid processed, None if human turn
        """
        if self.phase != PHASE_BIDDING:
            return None
        
        bidder = self.players[self.bid_turn_idx]
        if bidder.is_human:
            return None
        
        bid = self.ai.decide_bid(bidder.hand, self.highest_bid)
        self.apply_bid(self.bid_turn_idx, bid)
        return (self.bid_turn_idx, bid)

    def finish_bidding(self) -> None:
        """Conclude bidding phase and assign landlord role."""
        if self.best_bidder_idx is None:
            # Fallback: assign to first player if no valid bid
            self.best_bidder_idx = 0
        self.assign_landlord(self.best_bidder_idx)

    def assign_landlord(self, idx: int) -> None:
        """
        Assign landlord role and begin play phase.
        
        Args:
            idx: Index of player becoming landlord
        """
        self.landlord_idx = idx
        landlord = self.players[idx]
        landlord.role = LANDLORD_ROLE
        landlord.add_cards(self.bottom_cards)
        self.bottom_cards = []
        self.phase = PHASE_PLAY
        self.current_player_idx = self.landlord_idx
        self.last_combination = None
        self.last_player_idx = self.current_player_idx
        self.log(f"{landlord.name} is the landlord and starts the play.")

    def current_player(self) -> Player:
        """Get the player whose turn it is."""
        return self.players[self.current_player_idx]

    def _advance_current_player(self) -> None:
        """Move to next player in play order."""
        self.current_player_idx = (self.current_player_idx + 1) % NUM_PLAYERS

    def _is_start_of_trick(self) -> bool:
        """
        Check if current turn starts a new trick.
        
        A trick starts if no combination has been played yet, or if the last
        player to play is now the current player (trick reset).
        
        Returns:
            True if starting a new trick
        """
        if self.last_combination is None:
            return True
        return self.last_player_idx == self.current_player_idx

    def _validate_cards_in_hand(self, idx: int, cards: List[Card]) -> bool:
        """
        Verify all cards are in player's hand.
        
        Args:
            idx: Player index
            cards: Cards to validate
            
        Returns:
            True if all cards are in player's hand
        """
        return all(card in self.players[idx].hand for card in cards)

    def _check_win_condition(self, idx: int) -> bool:
        """
        Check if player has won by emptying their hand.
        
        Args:
            idx: Player index to check
            
        Returns:
            True if player has won
        """
        if not self.players[idx].has_cards():
            self.phase = PHASE_FINISHED
            winner_role = self.players[idx].role
            if winner_role == LANDLORD_ROLE:
                self.log("Landlord wins!")
            else:
                self.log("Farmers win!")
            return True
        return False

    def try_play(self, idx: int, cards: List[Card]) -> Tuple[bool, str]:
        """
        Attempt to play cards from player's hand.
        
        Args:
            idx: Index of player attempting to play
            cards: List of cards to play
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.phase != PHASE_PLAY or idx != self.current_player_idx:
            return False, "Not your turn."
        
        if not self._validate_cards_in_hand(idx, cards):
            return False, "You don't have those cards."
        
        combination = identify_combination(cards)
        if combination is None:
            return False, "Invalid combination."
        
        # Validate combination beats previous if not starting trick
        if not self._is_start_of_trick():
            if not can_beat(combination, self.last_combination):
                return False, "Your play does not beat the current combination."
        
        # Apply the play
        self.players[idx].remove_cards(cards)
        self.last_combination = combination
        self.last_player_idx = idx
        self.log(f"{self.players[idx].name} plays: {self._format_cards(cards)} [{combination.type}]")
        
        # Check win condition
        if self._check_win_condition(idx):
            return True, "Game over."
        
        # Advance to next player
        self._advance_current_player()
        return True, "Played."

    def try_pass(self, idx: int) -> Tuple[bool, str]:
        """
        Attempt to pass the current turn.
        
        Passing is only valid when there is an active combination and the player
        is not starting the trick.
        
        Args:
            idx: Index of player attempting to pass
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.phase != PHASE_PLAY or idx != self.current_player_idx:
            return False, "Not your turn."
        
        if self._is_start_of_trick():
            return False, "You cannot pass when starting a trick."
        
        self.log(f"{self.players[idx].name} passes.")
        self._advance_current_player()
        
        # Reset trick if turn returns to last player who played
        if self.last_player_idx is not None and self.current_player_idx == self.last_player_idx:
            self.last_combination = None
            self.log("All others passed. Trick resets; free lead.")
        
        return True, "Passed."

    def _get_ai_play(self) -> Optional[List[Card]]:
        """
        Get AI's chosen play for current hand.
        
        Returns:
            List of cards to play, or None if AI chooses to pass
        """
        current_hand = self.players[self.current_player_idx].hand
        is_start = self._is_start_of_trick()
        return self.ai.choose_play(current_hand, self.last_combination, is_start)

    def _handle_ai_pass(self) -> Tuple[str, None]:
        """
        Handle AI passing turn.
        
        Returns:
            Tuple of ("pass", None)
        """
        self.try_pass(self.current_player_idx)
        return ("pass", None)

    def _handle_ai_play(self, cards: List[Card]) -> Tuple[str, List[Card]]:
        """
        Handle AI playing cards.
        
        Args:
            cards: Cards AI chose to play
            
        Returns:
            Tuple of ("play", cards)
        """
        self.try_