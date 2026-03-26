import tkinter as tk
from tkinter import messagebox
import logging
from typing import Tuple, Optional
from game import ReversiGame

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Board and display constants
BOARD_SIZE = 8
CELL_SIZE = 80
BOARD_PIXEL_SIZE = BOARD_SIZE * CELL_SIZE
DISC_MARGIN = 6
HINT_RADIUS_FACTOR = 0.18
LAST_MOVE_OUTLINE_WIDTH = 3
GRID_LINE_WIDTH = 2
DISC_OUTLINE_WIDTH = 2

# Color constants
BOARD_BG_COLOR = "#1f8b4c"
GRID_COLOR = "#0e5b31"
HINT_COLOR_BLACK = "#444444"
HINT_COLOR_WHITE = "#dddddd"
LAST_MOVE_OUTLINE_COLOR = "#ffcc00"
BLACK_DISC_FILL = "#000000"
BLACK_DISC_OUTLINE = "#222222"
WHITE_DISC_FILL = "#ffffff"
WHITE_DISC_OUTLINE = "#e0e0e0"
INFO_TEXT_COLOR = "#333333"

# Font constants
TITLE_FONT = ("Arial", 16, "bold")
LABEL_FONT = ("Arial", 12)
INFO_FONT = ("Arial", 11)

# UI text constants
TITLE_TEXT = "Reversi (Othello)"
NEW_GAME_TEXT = "New Game"
UNDO_TEXT = "Undo Move"
QUIT_TEXT = "Quit"
BUTTON_WIDTH = 18
INVALID_MOVE_MSG = "Invalid move. Choose a highlighted cell."
NO_MOVES_MSG = "No valid moves. Turn will be passed."
VALID_MOVES_MSG = "{} valid move(s) available."
NEW_GAME_MSG = "New game started. Black moves first."
UNDO_MSG = "Last move undone."
NOTHING_UNDO_MSG = "Nothing to undo."
GAME_OVER_TITLE = "Game Over"
PASS_TITLE = "Pass"
PASS_MSG = "{} has no valid moves and must pass."
BLACK_WINS_MSG = "Black wins!"
WHITE_WINS_MSG = "White wins!"
TIE_MSG = "It's a tie!"
FINAL_SCORE_MSG = "Final Score:\nBlack: {}   White: {}\n\n{}"
CURRENT_PLAYER_MSG = "Current: {}"
SCORE_MSG = "Score — Black: {}  White: {}"
GAME_OVER_PLAYER = "Game Over"


class ReversiGUI:
    """Tkinter GUI wrapper for the ReversiGame.
    
    Manages the visual representation of the Reversi board, handles user interactions,
    displays game status, and controls game flow.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI and set up all UI components.
        
        Args:
            root: The root Tkinter window.
        """
        self.root = root
        self.game = ReversiGame()
        self.show_hints = True

        self._setup_frames()
        self._setup_labels()
        self._setup_buttons()
        self._bind_events()
        self.update_all()

    def _setup_frames(self) -> None:
        """Set up the main frame layout."""
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        self.canvas = tk.Canvas(
            self.root,
            width=BOARD_PIXEL_SIZE,
            height=BOARD_PIXEL_SIZE,
            bg=BOARD_BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.side_frame = tk.Frame(self.root)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    def _setup_labels(self) -> None:
        """Set up status labels."""
        self.current_player_var = tk.StringVar()
        self.score_var = tk.StringVar()
        self.info_var = tk.StringVar()

        tk.Label(self.top_frame, text=TITLE_TEXT, font=TITLE_FONT).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.current_player_var, font=LABEL_FONT, padx=15).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.score_var, font=LABEL_FONT, padx=15).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.info_var, font=INFO_FONT, fg=INFO_TEXT_COLOR).pack(side=tk.RIGHT)

    def _setup_buttons(self) -> None:
        """Set up control buttons."""
        self.new_game_btn = tk.Button(
            self.side_frame, text=NEW_GAME_TEXT, width=BUTTON_WIDTH, command=self.new_game
        )
        self.undo_btn = tk.Button(
            self.side_frame, text=UNDO_TEXT, width=BUTTON_WIDTH, command=self.undo_move
        )
        self.quit_btn = tk.Button(
            self.side_frame, text=QUIT_TEXT, width=BUTTON_WIDTH, command=self.root.destroy
        )
        self.new_game_btn.pack(pady=(0, 8))
        self.undo_btn.pack(pady=8)
        self.quit_btn.pack(pady=8)

    def _bind_events(self) -> None:
        """Bind keyboard and mouse events."""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.root.bind("<n>", lambda e: self.new_game())
        self.root.bind("<u>", lambda e: self.undo_move())

    def new_game(self) -> None:
        """Reset the game and refresh the UI."""
        self.game.reset()
        self.update_all()
        self.info_var.set(NEW_GAME_MSG)
        logger.info("New game started")

    def undo_move(self) -> None:
        """Undo the last move if possible."""
        if self.game.can_undo():
            self.game.undo()
            self.update_all()
            self.info_var.set(UNDO_MSG)
            logger.info("Move undone")
        else:
            self.info_var.set(NOTHING_UNDO_MSG)
            logger.info("Undo attempted but no moves to undo")

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle a click on the board to place a disc if the move is valid.
        
        Args:
            event: The click event containing coordinates.
        """
        # Game is over, no moves allowed
        if self.game.current_player is None:
            return

        # Convert pixel coordinates to board coordinates
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE

        # Validate coordinates are within board bounds
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        result = self.game.apply_move(row, col)
        if not result["moved"]:
            self.info_var.set(INVALID_MOVE_MSG)
            self.root.bell()
            logger.warning(f"Invalid move attempted at ({row}, {col})")
            return

        self.update_all()
        logger.info(f"Valid move placed at ({row}, {col})")

        # Handle pass scenario
        if result["pass_occurred"]:
            passed_player = (
                self.game.opponent(result["current_player"])
                if result["current_player"] is not None
                else None
            )
            self._show_pass_message(passed_player)

        # Check for game over
        if result["game_over"] or self.game.is_game_over():
            self._show_game_over()

    def update_all(self) -> None:
        """Redraw the board and update all status labels."""
        self.canvas.delete("all")
        self._draw_board()
        self._update_status_labels()

    def _update_status_labels(self) -> None:
        """Update the current player, score, and info labels."""
        score = self.game.get_score()
        self.score_var.set(SCORE_MSG.format(score['black'], score['white']))

        # Update current player label
        if self.game.current_player == ReversiGame.BLACK:
            self.current_player_var.set(CURRENT_PLAYER_MSG.format("Black"))
        elif self.game.current_player == ReversiGame.WHITE:
            self.current_player_var.set(CURRENT_PLAYER_MSG.format("White"))
        else:
            self.current_player_var.set(GAME_OVER_PLAYER)

        # Update info about available moves
        self._update_info_label()

    def _update_info_label(self) -> None:
        """Update the info label with move availability information."""
        if self.game.current_player is not None:
            moves = self.game.get_valid_moves()
            if len(moves) == 0:
                self.info_var.set(NO_MOVES_MSG)
            else:
                self.info_var.set(VALID_MOVES_MSG.format(len(moves)))
        else:
            self.info_var.set("")

    def _draw_board(self) -> None:
        """Draw the complete board including grid, discs, hints, and last move marker."""
        self._draw_grid()
        self._draw_discs()
        self._draw_last_move_highlight()
        self._draw_valid_move_hints()

    def _draw_grid(self) -> None:
        """Draw the board background and grid lines."""
        self.canvas.create_rectangle(
            0, 0, BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE,
            fill=BOARD_BG_COLOR, outline=""
        )
        for i in range(BOARD_SIZE + 1):
            pos = i * CELL_SIZE
            # Vertical lines
            self.canvas.create_line(
                pos, 0, pos, BOARD_PIXEL_SIZE,
                fill=GRID_COLOR, width=GRID_LINE_WIDTH
            )
            # Horizontal lines
            self.canvas.create_line(
                0, pos, BOARD_PIXEL_SIZE, pos,
                fill=GRID_COLOR, width=GRID_LINE_WIDTH
            )

    def _draw_discs(self) -> None:
        """Draw all discs currently on the board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.game.board[row][col]
                if cell == ReversiGame.EMPTY:
                    continue

                x0, y0, x1, y1 = self._board_to_canvas_coords(row, col)
                fill_color = BLACK_DISC_FILL if cell == ReversiGame.BLACK else WHITE_DISC_FILL
                outline_color = BLACK_DISC_OUTLINE if cell == ReversiGame.BLACK else WHITE_DISC_OUTLINE

                self.canvas.create_oval(
                    x0 + DISC_MARGIN, y0 + DISC_MARGIN,
                    x1 - DISC_MARGIN, y1 - DISC_MARGIN,
                    fill=fill_color, outline=outline_color, width=DISC_OUTLINE_WIDTH
                )

    def _draw_last_move_highlight(self) -> None:
        """Draw a highlight around the last move made."""
        if self.game.last_move is not None:
            row, col = self.game.last_move
            x0, y0, x1, y1 = self._board_to_canvas_coords(row, col)
            self.canvas.create_rectangle(
                x0 + 2, y0 + 2, x1 - 2, y1 - 2,
                outline=LAST_MOVE_OUTLINE_COLOR, width=LAST_MOVE_OUTLINE_WIDTH
            )

    def _draw_valid_move_hints(self) -> None:
        """Draw hints for all valid moves available to the current player."""
        if not self.show_hints or self.game.current_player is None:
            return

        moves = self.game.get_valid_moves()
        hint_color = (
            HINT_COLOR_BLACK if self.game.current_player == ReversiGame.BLACK
            else HINT_COLOR_WHITE
        )

        for row, col in moves:
            x0, y0, x1, y1 = self._board_to_canvas_coords(row, col)
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            radius = CELL_SIZE * HINT_RADIUS_FACTOR

            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=hint_color, outline=""
            )

    def _board_to_canvas_coords(self, row: int, col: int) -> Tuple[int, int, int, int]:
        """Convert board cell coordinates to canvas rectangle coordinates.
        
        Args:
            row: The row index on the board.
            col: The column index on the board.
            
        Returns:
            A tuple of (x0, y0, x1, y1) representing the canvas rectangle.
        """
        x0 = col * CELL_SIZE
        y0 = row * CELL_SIZE
        x1 = x0 + CELL_SIZE
        y1 = y0 + CELL_SIZE
        return x0, y0, x1, y1

    def _show_pass_message(self, passed_player: Optional[int]) -> None:
        """Display a message indicating that a player had to pass.
        
        Args:
            passed_player: The player who had to pass (BLACK or WHITE), or None.
        """
        if passed_player is None:
            return

        player_name = "Black" if passed_player == ReversiGame.BLACK else "White"
        messagebox.showinfo(PASS_TITLE, PASS_MSG.format(player_name))
        logger.info(f"{player_name} passed")

    def _show_game_over(self) -> None:
        """Display the game-over dialog with the final result."""
        score = self.game.get_score()
        winner = self.game.get_winner()

        if winner == ReversiGame.BLACK:
            result_msg = BLACK_WINS_MSG
        elif winner == ReversiGame.WHITE:
            result_msg = WHITE_WINS_MSG
        else:
            result_msg = TIE_MSG

        final_msg = FINAL_SCORE_MSG.format(score['black'], score['white'], result_msg)
        messagebox.showinfo(GAME_OVER_TITLE, final_msg)
        logger.info(f"Game over. Winner: {result_msg}")