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
BOARD_GRID_COLS = 5
BOARD_GRID_ROWS = 4
TILES_PER_ROW = 5
JAIL_FINE = 50
MARKER_SIZE = 20
MARKER_PADDING = 2
TEXT_WRAPLENGTH = 140
TILE_PADDING = 2
TILE_PADY = 2
FRAME_PADDING = 4
FRAME_PADY = 4
STATUS_TEXT_HEIGHT = 12
STATUS_TEXT_WIDTH = 40
LOG_TEXT_HEIGHT = 16
LOG_TEXT_WIDTH = 40
LOG_MAX_LINES = 200
MARKER_AREA_PADDING = 3
MARKER_AREA_PADY = 3
OWNER_LABEL_PADY_TOP = 0
OWNER_LABEL_PADY_BOTTOM = 3
NAME_LABEL_PADY_TOP = 3
NAME_LABEL_PADY_BOTTOM = 0

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SetupDialog(tk.Toplevel):
    """Dialog for initial game setup with player configuration."""

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
        # Number of players selection
        tk.Label(self, text=f"Number of Players ({MIN_PLAYERS}-{MAX_PLAYERS}):").grid(
            row=0, column=0, sticky="w", padx=FRAME_PADDING, pady=FRAME_PADY
        )
        self.num_var = tk.IntVar(value=DEFAULT_PLAYERS)
        ttk.Spinbox(
            self, from_=MIN_PLAYERS, to=MAX_PLAYERS, textvariable=self.num_var, width=5
        ).grid(row=0, column=1, sticky="w", padx=FRAME_PADDING, pady=FRAME_PADY)

        # Player name entries
        self.entries = []
        for i in range(MAX_PLAYERS):
            tk.Label(self, text=f"Player {i+1} Name:").grid(
                row=i+1, column=0, sticky="w", padx=FRAME_PADDING, pady=FRAME_PADY
            )
            entry = ttk.Entry(self, width=20)
            entry.grid(row=i+1, column=1, sticky="w", padx=FRAME_PADDING, pady=FRAME_PADY)
            if i < DEFAULT_PLAYERS:
                entry.insert(0, f"Player {i+1}")
            self.entries.append(entry)

        # Start button
        ttk.Button(self, text="Start Game", command=self.on_start).grid(
            row=MAX_PLAYERS+2, column=0, columnspan=2, pady=FRAME_PADY
        )

    def on_start(self):
        """Handle start button click and validate player setup."""
        num_players = self.num_var.get()
        names = []
        for i in range(num_players):
            name = self.entries[i].get().strip() or f"Player {i+1}"
            names.append(name)
        self.result = names
        logger.info(f"Game setup complete with {num_players} players")
        self.destroy()


class BoardFrame(tk.Frame):
    """Frame displaying the game board with tiles and player positions."""

    def __init__(self, master, game: Game):
        """
        Initialize the board frame.

        Args:
            master: Parent widget
            game: Game instance
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.tile_labels = []
        self.player_markers = {}

        self._configure_grid()
        self._build_board()

    def _configure_grid(self):
        """Configure grid weights for proper layout."""
        for col in range(BOARD_GRID_COLS):
            self.grid_columnconfigure(col, weight=1)
        for row in range(BOARD_GRID_ROWS):
            self.grid_rowconfigure(row, weight=1)

    def _index_to_grid(self, idx):
        """
        Convert tile index to grid coordinates.

        Args:
            idx: Tile index (0-19)

        Returns:
            Tuple of (row, col)
        """
        row = idx // TILES_PER_ROW
        col = idx % TILES_PER_ROW
        return row, col

    def _build_board(self):
        """Build the board UI with all tiles."""
        for i, tile in enumerate(self.game.board.tiles):
            row, col = self._index_to_grid(i)
            frame = tk.Frame(self, bd=1, relief="ridge", bg="#f4f4f4")
            frame.grid(row=row, column=col, sticky="nsew", padx=TILE_PADDING, pady=TILE_PADY)

            # Tile name label
            name_label = tk.Label(
                frame, text=f"{i}: {tile.name}", bg="#f4f4f4",
                anchor="w", justify="left", wraplength=TEXT_WRAPLENGTH
            )
            name_label.pack(fill="x", padx=FRAME_PADDING, pady=(NAME_LABEL_PADY_TOP, NAME_LABEL_PADY_BOTTOM))

            # Owner/property info label
            owner_label = tk.Label(
                frame, text="", fg="black", bg="#f4f4f4",
                anchor="w", justify="left", wraplength=TEXT_WRAPLENGTH
            )
            owner_label.pack(fill="x", padx=FRAME_PADDING, pady=(OWNER_LABEL_PADY_TOP, OWNER_LABEL_PADY_BOTTOM))

            # Player marker area
            marker_area = tk.Frame(frame, bg="#ffffff")
            marker_area.pack(fill="both", expand=True, padx=MARKER_AREA_PADDING, pady=MARKER_AREA_PADY)

            self.tile_labels.append((name_label, owner_label, marker_area))

        self.update_board()

    def _get_owner_text(self, tile):
        """
        Generate owner information text for a tile.

        Args:
            tile: Tile object

        Returns:
            String with owner information
        """
        if hasattr(tile, "owner") and tile.owner is not None:
            return f"Owner: {tile.owner.name} | Rent: ${tile.rent} | Price: ${tile.price}"
        elif hasattr(tile, "price") and hasattr(tile, "rent"):
            return f"Unowned | Rent: ${tile.rent} | Price: ${tile.price}"
        return ""

    def _update_tile_markers(self, tile_idx, marker_area):
        """
        Update player markers on a specific tile.

        Args:
            tile_idx: Index of the tile
            marker_area: Frame widget for markers
        """
        # Clear previous markers
        for child in list(marker_area.children.values()):
            child.destroy()

        # Place new markers for players on this tile
        players_here = [p for p in self.game.players if p.position == tile_idx and not p.bankrupt]
        for player in players_here:
            dot = tk.Canvas(
                marker_area, width=MARKER_SIZE, height=MARKER_SIZE,
                bg="#ffffff", highlightthickness=0
            )
            dot.create_oval(4, 4, 16, 16, fill=player.color, outline="black")
            dot.pack(side="left", padx=MARKER_PADDING, pady=MARKER_PADDING)

    def update_board(self):
        """Update board display with current game state."""
        for i, tile in enumerate(self.game.board.tiles):
            name_label, owner_label, marker_area = self.tile_labels[i]
            owner_text = self._get_owner_text(tile)
            owner_label.config(text=owner_text)
            self._update_tile_markers(i, marker_area)


class InfoPanel(tk.Frame):
    """Panel displaying game status and event log."""

    def __init__(self, master, game: Game):
        """
        Initialize the info panel.

        Args:
            master: Parent widget
            game: Game instance
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.status_text = tk.Text(
            self, height=STATUS_TEXT_HEIGHT, width=STATUS_TEXT_WIDTH, state="disabled"
        )
        self.status_text.pack(side="top", fill="x", padx=FRAME_PADDING, pady=FRAME_PADY)

        self.log_text = tk.Text(
            self, height=LOG_TEXT_HEIGHT, width=LOG_TEXT_WIDTH, state="disabled"
        )
        self.log_text.pack(side="bottom", fill="both", expand=True, padx=FRAME_PADDING, pady=FRAME_PADY)
        self.refresh()

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
                f"- {player.name} (${player.money}) | Pos {player.position} | {status} | GOOJF Cards: {player.get_out_of_jail_cards}\n"
            )

        # Current turn and last roll
        current = self.game.current_player
        self.status_text.insert("end", f"\nCurrent Turn: {current.name}\n")

        if self.game.last_roll:
            d1, d2 = self.game.last_roll
            doubles_text = "Doubles" if d1 == d2 else "No Doubles"
            self.status_text.insert("end", f"Last Roll: {d1} + {d2} = {d1+d2} ({doubles_text})\n")

        # Game over status
        if self.game.game_over:
            self.status_text.insert("end", "\nGAME OVER.\n")

        self.status_text.config(state="disabled")

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

    def _update_log_text(self):
        """Update the log text widget with recent game events."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")

        # Display last N log messages
        for msg in self.game.log[-LOG_MAX_LINES:]:
            self.log_text.insert("end", f"{msg}\n")

        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def refresh(self):
        """Refresh both status and log displays."""
        self._update_status_text()
        self._update_log_text()


class ControlPanel(tk.Frame):
    """Panel with game control buttons."""

    def __init__(self, master, game: Game, board_frame: BoardFrame, info_panel: InfoPanel):
        """
        Initialize the control panel.

        Args:
            master: Parent widget
            game: Game instance
            board_frame: BoardFrame reference
            info_panel: InfoPanel reference
        """
        super().__init__(master, bd=2, relief="groove")
        self.game = game
        self.board_frame = board_frame
        self.info_panel = info_panel
        self.game_over_announced = False

        self._build_buttons()
        self.update_buttons()

    def _build_buttons(self):
        """Build all control buttons."""
        self.roll_btn = ttk.Button(self, text="Roll Dice", command=self.on_roll)
        self.roll_btn.grid(row=0, column=0, padx=FRAME_PADDING, pady=FRAME_PADY, sticky="ew")

        self.end_turn_btn = ttk.Button(self, text="End Turn", command=self.on_end_turn)
        self.end_turn_btn.grid(row=0, column=1, padx=FRAME_PADDING, pady=FRAME_PADY, sticky="ew")

        self.pay_jail_btn = ttk.Button(self, text="Pay $50 (Jail)", command=self.on_pay_jail)
        self.pay_jail_btn.grid(row=1, column=0, padx=FRAME_PADDING, pady=FRAME_PADY, sticky="ew")

        self.attempt_doubles_btn = ttk.Button(self, text="Attempt Doubles (Jail)", command=self.on_attempt_doubles)
        self.attempt_doubles_btn.grid(row=1, column=1, padx=FRAME_PADDING, pady=FRAME_PADY, sticky="ew")

        self.use_goojf_btn = ttk.Button(self, text="Use Get Out of Jail Free", command=self.on_use_goojf)
        self.use_goojf_btn.grid(row=2, column=0, columnspan=2, padx=FRAME_PADDING, pady=FRAME_PADY, sticky="ew")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def _refresh_ui(self):
        """Refresh board, info panel, and button states."""
        self.board_frame.update_board()
        self.info_panel.refresh()
        self.update_buttons()

    def _check_game_over(self):
        """Check and announce game over if applicable."""
        if self.game.game_over and not self.game_over_announced:
            active_players = [p for p in self.game.players if not p.bankrupt]
            winner = active_players[0].name if active_players else "No one"
            messagebox.showinfo("Game Over", f"Game over! Winner: {winner}.")
            self.game_over_announced = True
            logger.info(f"Game over. Winner: {winner}")

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

        if player.money >= tile.price:
            buy = messagebox.askyesno(
                "Buy Property?",
                f"{player.name}, do you want to buy {tile.name} for ${tile.price}? Rent: ${tile.rent}"
            )
            if buy:
                msg =