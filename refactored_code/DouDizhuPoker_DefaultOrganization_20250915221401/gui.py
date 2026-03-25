import logging
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Optional

from models import Card
from game import DouDizhuGame

# Constants
WINDOW_TITLE = "Dou Dizhu (Landlord) - ChatDev"
DEFAULT_FONT = ("Arial", 14)
SMALL_FONT = ("Arial", 12)
HUMAN_PLAYER_INDEX = 1
LEFT_AI_INDEX = 0
RIGHT_AI_INDEX = 2
AI_BIDDING_DELAY_MS = 600
AI_PLAY_DELAY_MS = 500
CARD_BUTTON_WIDTH = 4
CARD_PADDING_X = 2
CARD_PADDING_Y = 4
FRAME_PADDING_X = 5
FRAME_PADDING_Y = 5
LABEL_PADDING_X = 10
LABEL_PADDING_Y = 10
BUTTON_PADDING_X = 5
BUTTON_PADDING_Y = 5
LOG_MAX_LINES = 200
HAND_FRAME_LABEL_WIDTH = 15
PLAY_AREA_HEIGHT = 10
BID_VALUES = [0, 1, 2, 3]
SELECTED_BG_COLOR = "#d0f0d0"
PHASE_BIDDING = "bidding"
PHASE_PLAY = "play"
PHASE_FINISHED = "finished"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GameUI:
    """
    Tkinter-based UI for playing Dou Dizhu against two AI opponents.
    Manages game state display, user input, and AI turn processing.
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
            font=DEFAULT_FONT
        )
        self.status_label.pack(side=tk.LEFT, padx=LABEL_PADDING_X, pady=LABEL_PADDING_Y)

        self.new_game_btn = tk.Button(
            self.top_frame,
            text="New Round",
            command=self.new_round
        )
        self.new_game_btn.pack(side=tk.RIGHT, padx=BUTTON_PADDING_X)

    def _setup_center_section(self) -> None:
        """Create AI info labels and play area in center frame."""
        self.left_info = tk.Label(
            self.center_frame,
            text="Left AI\nCards: 0",
            width=HAND_FRAME_LABEL_WIDTH,
            relief=tk.GROOVE
        )
        self.left_info.pack(
            side=tk.LEFT,
            padx=LABEL_PADDING_X,
            pady=LABEL_PADDING_Y,
            fill=tk.Y
        )

        self._setup_play_area()

        self.right_info = tk.Label(
            self.center_frame,
            text="Right AI\nCards: 0",
            width=HAND_FRAME_LABEL_WIDTH,
            relief=tk.GROOVE
        )
        self.right_info.pack(
            side=tk.LEFT,
            padx=LABEL_PADDING_X,
            pady=LABEL_PADDING_Y,
            fill=tk.Y
        )

    def _setup_play_area(self) -> None:
        """Create the central play area with last play info and message log."""
        self.play_area = tk.Frame(self.center_frame, relief=tk.RIDGE, borderwidth=2)
        self.play_area.pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.BOTH,
            padx=LABEL_PADDING_X,
            pady=LABEL_PADDING_Y
        )

        self.last_play_label = tk.Label(
            self.play_area,
            text="No plays yet.",
            font=SMALL_FONT
        )
        self.last_play_label.pack(pady=BUTTON_PADDING_Y)

        self.log_text = tk.Text(
            self.play_area,
            height=PLAY_AREA_HEIGHT,
            state=tk.DISABLED
        )
        self.log_text.pack(
            fill=tk.BOTH,
            expand=True,
            padx=FRAME_PADDING_X,
            pady=FRAME_PADDING_Y
        )

    def _setup_bottom_section(self) -> None:
        """Create hand display and control buttons in bottom frame."""
        self.hand_frame = tk.Frame(self.bottom_frame)
        self.hand_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=FRAME_PADDING_X,
            pady=FRAME_PADDING_Y
        )

        self.controls_frame = tk.Frame(self.bottom_frame)
        self.controls_frame.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=FRAME_PADDING_X,
            pady=FRAME_PADDING_Y
        )

        self._setup_control_buttons()

    def _setup_control_buttons(self) -> None:
        """Create play, pass, and bidding control buttons."""
        self.play_button = tk.Button(
            self.controls_frame,
            text="Play",
            command=self.on_play,
            state=tk.DISABLED
        )
        self.play_button.pack(side=tk.RIGHT, padx=BUTTON_PADDING_X)

        self.pass_button = tk.Button(
            self.controls_frame,
            text="Pass",
            command=self.on_pass,
            state=tk.DISABLED
        )
        self.pass_button.pack(side=tk.RIGHT, padx=BUTTON_PADDING_X)

        self.bid_buttons = {}
        for bid_value in BID_VALUES:
            btn = tk.Button(
                self.controls_frame,
                text=f"Bid {bid_value}",
                command=lambda v=bid_value: self.on_bid(v),
                state=tk.DISABLED
            )
            btn.pack(side=tk.LEFT, padx=BUTTON_PADDING_X)
            self.bid_buttons[bid_value] = btn

    def run(self) -> None:
        """Start the main event loop."""
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
        Process AI bidding turns in a loop until human's turn or bidding ends.
        Schedules itself recursively to allow UI updates between AI actions.
        """
        # Continue auto-bidding for AI until it's human's turn or bidding ends
        while self.game.phase == PHASE_BIDDING:
            bidder_idx = self.game.bid_turn_idx
            bidder = self.game.players[bidder_idx]

            if bidder.is_human:
                self.status_label.config(
                    text=f"Your turn to bid. Highest bid: {self.game.highest_bid}"
                )
                self.enable_bidding_controls_if_needed()
                break

            # AI takes a bid action
            self.game.process_ai_bid_if_needed()
            self.update_all()

            if self.game.phase != PHASE_BIDDING:
                # Bidding finished, transition to play phase
                self.after_bidding_to_play()
                return

        # If still in bidding and human's turn, wait for input
        if self.game.phase == PHASE_BIDDING:
            return

        # If phase changed to play, transition
        if self.game.phase == PHASE_PLAY:
            self.after_bidding_to_play()

    def enable_bidding_controls_if_needed(self) -> None:
        """
        Enable or disable bidding buttons based on game state.
        Only enabled during bidding phase when it's the human player's turn.
        """
        is_human_turn = (
            self.game.phase == PHASE_BIDDING and
            self.game.players[self.game.bid_turn_idx].is_human
        )

        for bid_value, btn in self.bid_buttons.items():
            if is_human_turn:
                # Disable bids that don't exceed current highest bid
                if bid_value > 0 and bid_value <= self.game.highest_bid:
                    btn.config(state=tk.DISABLED)
                else:
                    btn.config(state=tk.NORMAL)
            else:
                btn.config(state=tk.DISABLED)

    def on_bid(self, value: int) -> None:
        """
        Handle human player bid action.

        Args:
            value: The bid value (0-3).
        """
        if self.game.phase != PHASE_BIDDING:
            return

        if not self.game.players[self.game.bid_turn_idx].is_human:
            return

        self.game.apply_bid(self.game.bid_turn_idx, value)
        self.update_all()

        if self.game.phase == PHASE_BIDDING:
            self.enable_bidding_controls_if_needed()
            self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)
        elif self.game.phase == PHASE_PLAY:
            self.after_bidding_to_play()

    def after_bidding_to_play(self) -> None:
        """
        Transition from bidding phase to play phase.
        Handles case where all players pass and a new round is dealt.
        """
        # Disable all bidding controls
        for btn in self.bid_buttons.values():
            btn.config(state=tk.DISABLED)

        if self.game.phase != PHASE_PLAY:
            # All passed, redeal occurred
            self.status_label.config(
                text="All passed. New round dealt. Bidding again."
            )
            self.enable_bidding_controls_if_needed()
            self.root.after(AI_BIDDING_DELAY_MS, self.process_ai_bidding_loop)
            return

        # Bidding completed, show landlord and start play
        landlord_name = (
            self.game.players[self.game.landlord_idx].name
            if self.game.landlord_idx is not None
            else "Unknown"
        )
        self.status_label.config(text=f"Play phase. Landlord: {landlord_name}.")
        self.update_all()
        self.enable_play_controls_if_needed()
        self.root.after(AI_BIDDING_DELAY_MS, self.ai_play_loop)

    def ai_play_loop(self) -> None:
        """
        Process AI play turns in a loop until human's turn or game ends.
        Schedules itself recursively to allow UI updates between AI actions.
        """
        while self.game.phase == PHASE_PLAY:
            current_player = self.game.players[self.game.current_player_idx]

            if current_player.is_human:
                self.enable_play_controls_if_needed()
                break

            # AI takes a play action
            self.game.ai_take_turn_if_needed()
            self.update_all()

            if self.game.phase == PHASE_FINISHED:
                self.end_round_actions()
                break

    def enable_play_controls_if_needed(self) -> None:
        """
        Enable or disable play and pass buttons based on game state.
        Pass is disabled at the start of a trick.
        """
        is_human_turn = (
            self.game.phase == PHASE_PLAY and
            self.game.players[self.game.current_player_idx].is_human
        )

        if is_human_turn:
            self.play_button.config(state=tk.NORMAL)
            # Pass only allowed if not starting the trick
            pass_state = tk.DISABLED if self.game.is_start_of_trick() else tk.NORMAL
            self.pass_button.config(state=pass_state)
        else:
            self.play_button.config(state=tk.DISABLED)
            self.pass_button.config(state=tk.DISABLED)

    def on_play(self) -> None:
        """Handle human player play action with selected cards."""
        if self.game.phase != PHASE_PLAY:
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

        if self.game.phase == PHASE_FINISHED:
            self.end_round_actions()
            return

        self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def on_pass(self) -> None:
        """Handle human player pass action."""
        if self.game.phase != PHASE_PLAY:
            return

        ok, msg = self.game.try_pass(HUMAN_PLAYER_INDEX)
        if not ok:
            messagebox.showwarning("Cannot pass", msg)
            return

        self.clear_selection()
        self.update_all()

        if self.game.phase == PHASE_FINISHED:
            self.end_round_actions()
            return

        self.root.after(AI_PLAY_DELAY_MS, self.ai_play_loop)

    def end_round_actions(self) -> None:
        """Disable all controls and display round result."""
        self.play_button.config(state=tk.DISABLED)
        self.pass_button.config(state=tk.DISABLED)
        for btn in self.bid_buttons.values():
            btn.config(state=tk.DISABLED)

        result_msg = (
            self.game.message_log[-1]
            if self.game.message_log
            else "Round finished."
        )

        if "wins" in result_msg:
            messagebox.showinfo("Result", result_msg)
        else:
            messagebox.showinfo("Result", "Round finished.")

        self.status_label.config(
            text="Round finished. Click 'New Round' to play again."
        )

    def update_all(self) -> None:
        """