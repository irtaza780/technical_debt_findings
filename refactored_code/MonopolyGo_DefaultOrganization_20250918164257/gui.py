import tkinter as tk
from tkinter import ttk, messagebox
import logging
from game import Game, Player
from functools import partial

# Constants
PLAYER_COLORS = ["red", "blue", "green", "purple"]
MIN_PLAYERS = 2
MAX_PLAYERS = 4
DEFAULT_PLAYERS = 2
BOARD_COLS = 5
BOARD_ROWS = 4
JAIL_FINE = 50
TILE_MARKER_SIZE = 20
TILE_MARKER_PADDING = 2
STATUS_TEXT_HEIGHT = 12
STATUS_TEXT_WIDTH = 40
LOG_TEXT_HEIGHT = 16
LOG_TEXT_WIDTH = 40
LOG_DISPLAY_LIMIT = 200
TILE_WRAPLENGTH = 140
MARKER_AREA_PADDING = 3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SetupDialog(tk.Toplevel):
    """Dialog for configuring game setup with player count and names."""

    def __init__(self, master):
        """
        Initialize the setup dialog.

        Args:
            master: Parent window
        """
        super().__init__(master)
        self.title("Game Setup")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._build_ui()

    def _build_ui(self):
        """Build the user interface for player setup."""
        # Player count selector
        tk.Label(self, text=f"Number of Players ({MIN_PLAYERS}-{MAX_PLAYERS}):").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.num_var = tk.IntVar(value=DEFAULT_PLAYERS)
        ttk.Spinbox(
            self, from_=MIN_PLAYERS, to=MAX_PLAYERS, textvariable=self.num_var, width=5
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # Player name entries
        self.entries = []
        for i in range(MAX_PLAYERS):
            tk.Label(self, text=f"Player {i+1} Name:").grid(
                row=i+1, column=0, sticky="w", padx=10, pady=5
            )
            entry = ttk.Entry(self, width=20)
            entry.grid(row=i+1, column=1, sticky="w", padx=10, pady=5)
            if i < DEFAULT_PLAYERS:
                entry.insert(0, f"Player {i+1}")
            self.entries.append(entry)

        # Start button
        ttk.Button(self, text="Start Game", command=self.on_start).grid(
            row=6, column=0, columnspan=2, pady=10
        )

    def on_start(self):
        """Handle start button click and validate player setup."""
        num_players = self.num_var.get()
        names = []
        for i in range(num_players):
            name = self.entries[i].get().strip() or f"Player {i+1}"
            names.append(name)
        self.result = names
        self.destroy()


class BoardFrame(tk.Frame):
    """Visual representation of the game board with tiles and player markers."""

    def __init__(self, master, game: Game):
        """
        Initialize the board frame.

        Args:
            game: Game instance to display
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.tile_labels = []
        self.player_markers = {}

        self._configure_grid()
        self._build_board()

    def _configure_grid(self):
        """Configure grid weights for proper tile layout."""
        for col in range(BOARD_COLS):
            self.grid_columnconfigure(col, weight=1)
        for row in range(BOARD_ROWS):
            self.grid_rowconfigure(row, weight=1)

    def _index_to_grid(self, idx):
        """
        Convert tile index to grid coordinates.

        Args:
            idx: Tile index (0-19)

        Returns:
            Tuple of (row, col)
        """
        row = idx // BOARD_COLS
        col = idx % BOARD_COLS
        return row, col

    def _build_board(self):
        """Build all board tiles with labels and marker areas."""
        for i, tile in enumerate(self.game.board.tiles):
            row, col = self._index_to_grid(i)
            self._create_tile_widget(i, tile, row, col)
        self.update_board()

    def _create_tile_widget(self, tile_idx, tile, row, col):
        """
        Create a single tile widget.

        Args:
            tile_idx: Index of the tile
            tile: Tile object
            row: Grid row
            col: Grid column
        """
        frame = tk.Frame(self, bd=1, relief="ridge", bg="#f4f4f4")
        frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        # Tile name label
        name_label = tk.Label(
            frame, text=f"{tile_idx}: {tile.name}", bg="#f4f4f4",
            anchor="w", justify="left", wraplength=TILE_WRAPLENGTH
        )
        name_label.pack(fill="x", padx=4, pady=(3, 0))

        # Owner/property info label
        owner_label = tk.Label(
            frame, text="", fg="black", bg="#f4f4f4",
            anchor="w", justify="left", wraplength=TILE_WRAPLENGTH
        )
        owner_label.pack(fill="x", padx=4, pady=(0, 3))

        # Player marker area
        marker_area = tk.Frame(frame, bg="#ffffff")
        marker_area.pack(fill="both", expand=True, padx=3, pady=3)

        self.tile_labels.append((name_label, owner_label, marker_area))

    def _get_owner_text(self, tile):
        """
        Generate owner information text for a tile.

        Args:
            tile: Tile object

        Returns:
            String describing ownership and rent/price
        """
        if hasattr(tile, "owner") and tile.owner is not None:
            return f"Owner: {tile.owner.name} | Rent: ${tile.rent} | Price: ${tile.price}"
        elif hasattr(tile, "price") and hasattr(tile, "rent"):
            return f"Unowned | Rent: ${tile.rent} | Price: ${tile.price}"
        return ""

    def _place_player_markers(self, marker_area, tile_idx):
        """
        Place player markers on a tile.

        Args:
            marker_area: Frame to place markers in
            tile_idx: Index of the tile
        """
        # Clear previous markers
        for child in list(marker_area.children.values()):
            child.destroy()

        # Place markers for players on this tile
        players_here = [p for p in self.game.players if p.position == tile_idx and not p.bankrupt]
        for player in players_here:
            dot = tk.Canvas(
                marker_area, width=TILE_MARKER_SIZE, height=TILE_MARKER_SIZE,
                bg="#ffffff", highlightthickness=0
            )
            dot.create_oval(4, 4, 16, 16, fill=player.color, outline="black")
            dot.pack(side="left", padx=TILE_MARKER_PADDING, pady=TILE_MARKER_PADDING)

    def update_board(self):
        """Update board display with current game state."""
        for i, tile in enumerate(self.game.board.tiles):
            name_label, owner_label, marker_area = self.tile_labels[i]
            owner_text = self._get_owner_text(tile)
            owner_label.config(text=owner_text)
            self._place_player_markers(marker_area, i)


class InfoPanel(tk.Frame):
    """Panel displaying player status and game log."""

    def __init__(self, master, game: Game):
        """
        Initialize the info panel.

        Args:
            game: Game instance to display information from
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.status_text = tk.Text(
            self, height=STATUS_TEXT_HEIGHT, width=STATUS_TEXT_WIDTH, state="disabled"
        )
        self.status_text.pack(side="top", fill="x", padx=4, pady=4)

        self.log_text = tk.Text(
            self, height=LOG_TEXT_HEIGHT, width=LOG_TEXT_WIDTH, state="disabled"
        )
        self.log_text.pack(side="bottom", fill="both", expand=True, padx=4, pady=4)
        self.refresh()

    def _get_player_status(self, player):
        """
        Get status string for a player.

        Args:
            player: Player object

        Returns:
            Status string
        """
        if player.bankrupt:
            return "BANKRUPT"
        elif player.in_jail:
            return "In Jail"
        return "Active"

    def _update_status_text(self):
        """Update the status text widget with current game state."""
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")

        # Free parking pot
        self.status_text.insert("end", f"Free Parking Pot: ${self.game.free_parking_pot}\n")

        # Player information
        self.status_text.insert("end", "Players:\n")
        for player in self.game.players:
            status = self._get_player_status(player)
            self.status_text.insert(
                "end",
                f"- {player.name} (${player.money}) | Pos {player.position} | "
                f"{status} | GOOJF Cards: {player.get_out_of_jail_cards}\n"
            )

        # Current turn and last roll
        current = self.game.current_player
        self.status_text.insert("end", f"\nCurrent Turn: {current.name}\n")

        if self.game.last_roll:
            d1, d2 = self.game.last_roll
            doubles_text = "Doubles" if d1 == d2 else "No Doubles"
            self.status_text.insert("end", f"Last Roll: {d1} + {d2} = {d1+d2} ({doubles_text})\n")

        # Game over indicator
        if self.game.game_over:
            self.status_text.insert("end", "\nGAME OVER.\n")

        self.status_text.config(state="disabled")

    def _update_log_text(self):
        """Update the log text widget with recent game messages."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        for msg in self.game.log[-LOG_DISPLAY_LIMIT:]:
            self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def refresh(self):
        """Refresh both status and log displays."""
        self._update_status_text()
        self._update_log_text()


class ControlPanel(tk.Frame):
    """Control panel with buttons for game actions."""

    def __init__(self, master, game: Game, board_frame: BoardFrame, info_panel: InfoPanel):
        """
        Initialize the control panel.

        Args:
            game: Game instance
            board_frame: Board display frame
            info_panel: Info panel for updates
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.board_frame = board_frame
        self.info_panel = info_panel
        self.game_over_announced = False

        self._build_buttons()
        self._configure_grid()
        self.update_buttons()

    def _build_buttons(self):
        """Build all control buttons."""
        self.roll_btn = ttk.Button(self, text="Roll Dice", command=self.on_roll)
        self.roll_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.end_turn_btn = ttk.Button(self, text="End Turn", command=self.on_end_turn)
        self.end_turn_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.pay_jail_btn = ttk.Button(self, text="Pay $50 (Jail)", command=self.on_pay_jail)
        self.pay_jail_btn.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.attempt_doubles_btn = ttk.Button(
            self, text="Attempt Doubles (Jail)", command=self.on_attempt_doubles
        )
        self.attempt_doubles_btn.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        self.use_goojf_btn = ttk.Button(
            self, text="Use Get Out of Jail Free", command=self.on_use_goojf
        )
        self.use_goojf_btn.grid(row=2, column=0, columnspan=2, padx=4, pady=4, sticky="ew")

    def _configure_grid(self):
        """Configure grid weights for button layout."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def _refresh_display(self):
        """Refresh board and info panel displays."""
        self.board_frame.update_board()
        self.info_panel.refresh()

    def _prompt_purchase_if_needed(self):
        """Prompt current player to purchase property if applicable."""
        tile = self.game.pending_purchase_tile
        if tile is None or tile.owner is not None:
            return

        player = self.game.current_player

        if player.bankrupt:
            self.game.log_message(f"{player.name} is bankrupt and cannot buy properties.")
            self.game.pending_purchase_tile = None
            return

        if player.money < tile.price:
            self.game.log_message(f"{player.name} cannot afford {tile.name} (${tile.price}).")
            self.game.pending_purchase_tile = None
            return

        # Prompt player to buy
        buy = messagebox.askyesno(
            "Buy Property?",
            f"{player.name}, do you want to buy {tile.name} for ${tile.price}? Rent: ${tile.rent}"
        )

        if buy:
            msg = self.game.attempt_purchase_current_tile()
            self.game.log_message(msg)
        else:
            self.game.log_message(f"{player.name} declined to purchase {tile.name}.")

        self.game.pending_purchase_tile = None

    def _check_game_over(self):
        """Check if game is over and announce winner if needed."""
        if self.game.game_over and not self.game_over_announced:
            active_players = [p for p in self.game.players if not p.bankrupt]
            winner = active_players[0].name if active_players else "No one"
            messagebox.showinfo("Game Over", f"Game over! Winner: {winner}.")
            self.game_over_announced = True

    def on_roll(self):
        """Handle roll dice button click."""
        if self.game.game_over:
            messagebox.showinfo("Game Over", "The game has ended. See the log for details.")
            return

        player = self.game.current_player

        if player.in_jail: