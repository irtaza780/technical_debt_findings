import logging
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Optional

from models import Card
from game import DouDizhuGame

# Constants
WINDOW_TITLE = "Dou Dizhu (Landlord) - ChatDev"
DEFAULT_FONT = "Arial"
STATUS_FONT_SIZE = 14
LAST_PLAY_FONT_SIZE = 12
HUMAN_PLAYER_INDEX = 1
LEFT_AI_INDEX = 0
RIGHT_AI_INDEX = 2
LOG_MAX_LINES = 200
AI_BIDDING_DELAY_MS = 600
AI_PLAY_DELAY_MS = 500
CARD_BUTTON_WIDTH = 4
CARD_BUTTON_PADX = 2
CARD_BUTTON_PADY = 4
FRAME_PADX = 10
FRAME_PADY = 10
CONTROL_PADX = 5
CONTROL_PADY = 5
CONTROL_BUTTON_PADX = 3
SELECTED_BG_COLOR = "#d0f0d0"
BID_VALUES = [0, 1, 2, 3]
AI_INFO_WIDTH = 15
LOG_TEXT_HEIGHT = 10

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GameUI:
    """
    Tkinter-based UI for playing Dou Dizhu against two AI opponents.
    Manages bidding phase, play phase, hand display, and game status updates.
    """

    def __init__(self):
        """Initialize the game UI with all frames, labels, and controls."""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.game = DouDizhuGame()
        self.selected: Dict[int, bool] = {}
        self.card_buttons: List[tk.Button] = []

        self._setup_frames()
        self._setup_top_section()
        self._setup_center_section()
        self._setup_bottom_section()

        self.new_round()

    def _setup_frames(self) -> None:
        """Create and pack the main layout frames."""
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.center_frame = tk.Frame(self.root)
        self.center_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_top_section(self) -> None:
        """Create status label and new round button in top frame."""
        self.status_label = tk.Label(
            self.top_frame,
            text="Welcome to Dou Dizhu!",
            font=(DEFAULT_FONT, STATUS_FONT_SIZE),
        )
        self.status_label.pack(side=tk.LEFT, padx=FRAME_PADX, pady=FRAME_PADY)

        self.new_game_btn = tk.Button(
            self.top_frame, text="New Round", command=self.new_round
        )
        self.new_game_btn.pack(side=tk.RIGHT, padx=CONTROL_BUTTON_PADX)

    def _setup_center_section(self) -> None:
        """Create AI info labels, play area, and game log in center frame."""
        self.left_info = tk.Label(
            self.center_frame,
            text="Left AI\nCards: 0",
            width=AI_INFO_WIDTH,
            relief=tk.GROOVE,
        )
        self.left_info.pack(side=tk.LEFT, padx=FRAME_PADX, pady=FRAME_PADY, fill=tk.Y)

        self._setup_play_area()

        self.right_info = tk.Label(
            self.center_frame,
            text="Right AI\nCards: 0",
            width=AI_INFO_WIDTH,
            relief=tk.GROOVE,
        )
        self.right_info.pack(side=tk.LEFT, padx=FRAME_PADX, pady=FRAME_PADY, fill=tk.Y)

    def _setup_play_area(self) -> None:
        """Create the central play area with last play info and game log."""
        self.play_area = tk.Frame(self.center_frame, relief=tk.RIDGE, borderwidth=2)
        self.play_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=FRAME_PADX, pady=FRAME_PADY)

        self.last_play_label = tk.Label(
            self.play_area, text="No plays yet.", font=(DEFAULT_FONT, LAST_PLAY_FONT_SIZE)
        )
        self.last_play_label.pack(pady=CONTROL_PADY)

        self.log_text = tk.Text(
            self.play_area, height=LOG_TEXT_HEIGHT, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=CONTROL_PADX, pady=CONTROL_PADY)

    def _setup_bottom_section(self) -> None:
        """Create hand display frame and control buttons in bottom frame."""
        self.hand_frame = tk.Frame(self.bottom_frame)
        self.hand_frame.pack(side=tk.TOP, fill=tk.X, padx=CONTROL_PADX, pady=CONTROL_PADY)

        self.controls_frame = tk.Frame(self.bottom_frame)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=CONTROL_PADX, pady=CONTROL_PADY)

        self._setup_control_buttons()

    def _setup_control_buttons(self) -> None:
        """Create play, pass, and bidding control buttons."""
        self.play_button = tk.Button(
            self.controls_frame, text="Play", command=self.on_play, state=tk.DISABLED
        )
        self.play_button.pack(side=tk.RIGHT, padx=CONTROL_BUTTON_PADX)

        self.pass_button = tk.Button(
            self.controls_frame, text="Pass", command=self.on_pass, state=tk.DISABLED
        )
        self.pass_button.pack(side=tk.RIGHT, padx=CONTROL_BUTTON_PADX)

        self.bid_buttons = {}
        for bid_value in BID_VALUES:
            btn = tk.Button(
                self.controls_frame,
                text=f"Bid {bid_value}",
                command=lambda v=bid_value: self.on_bid(v),
                state=tk.DISABLED,
            )
            btn.pack(side=tk.LEFT, padx=CONTROL_BUTTON_PADX)
            self.bid_buttons[bid_value] = btn

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()

    def new_round(self) -> None:
        """Initialize a new round and start the bidding phase."""
        self.game.start_new_round()
        self.update_all()
        self.status_label.config(text="Bidding phase. Left AI starts.")
        self.enable_bidding_controls_if_needed()
        self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)

    def process_ai_bidding_loop(self) -> None:
        """
        Process AI bidding actions in a loop until it's the human's turn or bidding ends.
        Schedules itself recursively to allow UI updates between AI actions.
        """
        if self.game.phase != "bidding":
            return

        bidder_idx = self.game.bid_turn_idx
        bidder = self.game.players[bidder_idx]

        if bidder.is_human:
            self.status_label.config(
                text=f"Your turn to bid. Highest bid: {self.game.highest_bid}"
            )
            self.enable_bidding_controls_if_needed()
            return

        # AI takes a bid action
        self.game.process_ai_bid_if_needed()
        self.update_all()

        if self.game.phase == "bidding":
            # Continue AI bidding loop
            self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)
        elif self.game.phase == "play":
            # Bidding finished, transition to play phase
            self.after_bidding_to_play()

    def enable_bidding_controls_if_needed(self) -> None:
        """
        Enable or disable bidding buttons based on game state.
        Only enabled during bidding phase when it's the human's turn.
        """
        is_human_turn = (
            self.game.phase == "bidding"
            and self.game.players[self.game.bid_turn_idx].is_human
        )

        for bid_value, btn in self.bid_buttons.items():
            if is_human_turn:
                # Disable bids that don't exceed current highest bid
                if bid_value == 0 or bid_value > self.game.highest_bid:
                    btn.config(state=tk.NORMAL)
                else:
                    btn.config(state=tk.DISABLED)
            else:
                btn.config(state=tk.DISABLED)

    def on_bid(self, value: int) -> None:
        """
        Handle human player's bid action.

        Args:
            value: The bid value (0-3).
        """
        if self.game.phase != "bidding":
            return

        if not self.game.players[self.game.bid_turn_idx].is_human:
            return

        self.game.apply_bid(self.game.bid_turn_idx, value)
        self.update_all()

        if self.game.phase == "bidding":
            self.enable_bidding_controls_if_needed()
            self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)
        elif self.game.phase == "play":
            self.after_bidding_to_play()

    def after_bidding_to_play(self) -> None:
        """
        Transition from bidding phase to play phase.
        Disables bidding controls and enables play controls.
        """
        # Disable all bidding buttons
        for btn in self.bid_buttons.values():
            btn.config(state=tk.DISABLED)

        if self.game.phase != "play":
            # All players passed; redeal and restart bidding
            self.status_label.config(
                text="All passed. New round dealt. Bidding again."
            )
            self.enable_bidding_controls_if_needed()
            self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)
            return

        # Update status with landlord info
        landlord_name = (
            self.game.players[self.game.landlord_idx].name
            if self.game.landlord_idx is not None
            else "Unknown"
        )
        self.status_label.config(text=f"Play phase. Landlord: {landlord_name}.")
        self.update_all()
        self.enable_play_controls_if_needed()
        self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def ai_play_loop(self) -> None:
        """
        Process AI play actions in a loop until it's the human's turn or game ends.
        Schedules itself recursively to allow UI updates between AI actions.
        """
        if self.game.phase != "play":
            return

        current_player = self.game.players[self.game.current_player_idx]

        if current_player.is_human:
            self.enable_play_controls_if_needed()
            return

        # AI takes a play action
        self.game.ai_take_turn_if_needed()
        self.update_all()

        if self.game.phase == "finished":
            self.end_round_actions()
        else:
            self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def enable_play_controls_if_needed(self) -> None:
        """
        Enable or disable play and pass buttons based on game state.
        Pass is disabled at the start of a trick.
        """
        is_human_turn = (
            self.game.phase == "play"
            and self.game.players[self.game.current_player_idx].is_human
        )

        if is_human_turn:
            self.play_button.config(state=tk.NORMAL)
            # Pass only allowed if not starting the trick
            pass_state = (
                tk.DISABLED if self.game.is_start_of_trick() else tk.NORMAL
            )
            self.pass_button.config(state=pass_state)
        else:
            self.play_button.config(state=tk.DISABLED)
            self.pass_button.config(state=tk.DISABLED)

    def on_play(self) -> None:
        """Handle human player's play action with selected cards."""
        if self.game.phase != "play":
            return

        selected_cards = self.get_selected_cards()
        if not selected_cards:
            messagebox.showinfo("Play", "Select cards to play.")
            return

        ok, msg = self.game.try_play(HUMAN_PLAYER_INDEX, selected_cards)
        if not ok:
            messagebox.showwarning("Invalid", msg)
            return

        self.clear_selection()
        self.update_all()

        if self.game.phase == "finished":
            self.end_round_actions()
        else:
            self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def on_pass(self) -> None:
        """Handle human player's pass action."""
        if self.game.phase != "play":
            return

        ok, msg = self.game.try_pass(HUMAN_PLAYER_INDEX)
        if not ok:
            messagebox.showwarning("Cannot pass", msg)
            return

        self.clear_selection()
        self.update_all()

        if self.game.phase == "finished":
            self.end_round_actions()
        else:
            self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def end_round_actions(self) -> None:
        """
        Finalize the round by disabling controls and displaying the result.
        """
        self.play_button.config(state=tk.DISABLED)
        self.pass_button.config(state=tk.DISABLED)
        for btn in self.bid_buttons.values():
            btn.config(state=tk.DISABLED)

        result_msg = (
            self.game.message_log[-1]
            if self.game.message_log
            else "Round finished."
        )
        messagebox.showinfo("Result", result_msg)
        self.status_label.config(
            text="Round finished. Click 'New Round' to play again."
        )

    def update_all(self) -> None:
        """Update all UI elements to reflect current game state."""
        self._update_ai_info()
        self._update_last_play_info()
        self._update_game_log()
        self._update_human_hand()
        self._update_status_label()
        self.enable_bidding_controls_if_needed()
        self.enable_play_controls_if_needed()

    def _update_ai_info(self) -> None:
        """Update left and right AI player information displays."""
        left_player = self.game.players[LEFT_AI_INDEX]
        right_player = self.game.players[RIGHT_AI_INDEX]

        left_text = (
            f"{left_player.name}\nRole: {left_player.role}\n"
            f