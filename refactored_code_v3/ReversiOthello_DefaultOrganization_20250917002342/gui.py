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
LAST_MOVE_HIGHLIGHT_MARGIN = 2
LAST_MOVE_HIGHLIGHT_WIDTH = 3
GRID_LINE_WIDTH = 2

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
DISC_OUTLINE_WIDTH = 2
INFO_TEXT_COLOR = "#333333"

# Font constants
TITLE_FONT = ("Arial", 16, "bold")
LABEL_FONT = ("Arial", 12)
INFO_FONT = ("Arial", 11)

# Button constants
BUTTON_WIDTH = 18
BUTTON_PADY_FIRST = (0, 8)
BUTTON_PADY_DEFAULT = 8

# Padding constants
TOP_FRAME_PADX = 10
TOP_FRAME_PADY = 8
CANVAS_PADX = 10
CANVAS_PADY = 10
SIDE_FRAME_PADX = 10
SIDE_FRAME_PADY = 10
LABEL_PADX = 15


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
        self._setup_status_labels()
        self._setup_buttons()
        self._bind_events()
        self.update_all()

    def _setup_frames(self) -> None:
        """Set up the main frame layout."""
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=TOP_FRAME_PADX, pady=TOP_FRAME_PADY)

        self.canvas = tk.Canvas(
            self.root,
            width=BOARD_PIXEL_SIZE,
            height=BOARD_PIXEL_SIZE,
            bg=BOARD_BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, padx=CANVAS_PADX, pady=CANVAS_PADY)

        self.side_frame = tk.Frame(self.root)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y, padx=SIDE_FRAME_PADX, pady=SIDE_FRAME_PADY)

    def _setup_status_labels(self) -> None:
        """Set up status display labels."""
        self.current_player_var = tk.StringVar()
        self.score_var = tk.StringVar()
        self.info_var = tk.StringVar()

        tk.Label(self.top_frame, text="Reversi (Othello)", font=TITLE_FONT).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.current_player_var, font=LABEL_FONT, padx=LABEL_PADX).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.score_var, font=LABEL_FONT, padx=LABEL_PADX).pack(side=tk.LEFT)
        tk.Label(self.top_frame, textvariable=self.info_var, font=INFO_FONT, fg=INFO_TEXT_COLOR).pack(side=tk.RIGHT)

    def _setup_buttons(self) -> None:
        """Set up control buttons."""
        self.new_game_btn = tk.Button(
            self.side_frame, text="New Game", width=BUTTON_WIDTH, command=self.new_game
        )
        self.undo_btn = tk.Button(
            self.side_frame, text="Undo Move", width=BUTTON_WIDTH, command=self.undo_move
        )
        self.quit_btn = tk.Button(
            self.side_frame, text="Quit", width=BUTTON_WIDTH, command=self.root.destroy
        )
        
        self.new_game_btn.pack(pady=BUTTON_PADY_FIRST)
        self.undo_btn.pack(pady=BUTTON_PADY_DEFAULT)
        self.quit_btn.pack(pady=BUTTON_PADY_DEFAULT)

    def _bind_events(self) -> None:
        """Bind keyboard and mouse events."""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.root.bind("<n>", lambda e: self.new_game())
        self.root.bind("<u>", lambda e: self.undo_move())

    def new_game(self) -> None:
        """Reset the game and refresh the UI."""
        self.game.reset()
        self.update_all()
        self.info_var.set("New game started. Black moves first.")
        logger.info("New game started")

    def undo_move(self) -> None:
        """Undo the last move if possible."""
        if self.game.can_undo():
            self.game.undo()
            self.update_all()
            self.info_var.set("Last move undone.")
            logger.info("Move undone")
        else:
            self.info_var.set("Nothing to undo.")
            logger.info("Undo attempted but no moves to undo")

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle a click on the board to place a disc if the move is valid.
        
        Args:
            event: The Tkinter click event containing coordinates.
        """
        if self.game.current_player is None:
            # Game is over
            return

        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE

        # Validate coordinates are within board bounds
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        result = self.game.apply_move(row, col)
        if not result["moved"]:
            self.info_var.set("Invalid move. Choose a highlighted cell.")
            self.root.bell()
            logger.info(f"Invalid move attempted at ({row}, {col})")
            return

        logger.info(f"Valid move placed at ({row}, {col})")
        self.update_all()

        if result["pass_occurred"]:
            passed_player = (
                self.game.opponent(result["current_player"])
                if result["current_player"] is not None
                else None
            )
            self._show_pass_message(passed_player)

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
        self.score_var.set(f"Score — Black: {score['black']}  White: {score['white']}")

        # Update current player display
        if self.game.current_player == ReversiGame.BLACK:
            self.current_player_var.set("Current: Black")
        elif self.game.current_player == ReversiGame.WHITE:
            self.current_player_var.set("Current: White")
        else:
            self.current_player_var.set("Game Over")

        # Update move availability info
        if self.game.current_player is not None:
            moves = self.game.get_valid_moves()
            if len(moves) == 0:
                self.info_var.set("No valid moves. Turn will be passed.")
            else:
                self.info_var.set(f"{len(moves)} valid move(s) available.")
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
        
        # Draw vertical and horizontal grid lines
        for i in range(BOARD_SIZE + 1):
            position = i * CELL_SIZE
            self.canvas.create_line(
                position, 0, position, BOARD_PIXEL_SIZE,
                fill=GRID_COLOR, width=GRID_LINE_WIDTH
            )
            self.canvas.create_line(
                0, position, BOARD_PIXEL_SIZE, position,
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
                
                # Determine disc color based on player
                if cell == ReversiGame.BLACK:
                    fill_color = BLACK_DISC_FILL
                    outline_color = BLACK_DISC_OUTLINE
                else:
                    fill_color = WHITE_DISC_FILL
                    outline_color = WHITE_DISC_OUTLINE

                self.canvas.create_oval(
                    x0 + DISC_MARGIN, y0 + DISC_MARGIN,
                    x1 - DISC_MARGIN, y1 - DISC_MARGIN,
                    fill=fill_color, outline=outline_color, width=DISC_OUTLINE_WIDTH
                )

    def _draw_last_move_highlight(self) -> None:
        """Draw a highlight around the last move made."""
        if self.game.last_move is None:
            return

        row, col = self.game.last_move
        x0, y0, x1, y1 = self._board_to_canvas_coords(row, col)
        self.canvas.create_rectangle(
            x0 + LAST_MOVE_HIGHLIGHT_MARGIN, y0 + LAST_MOVE_HIGHLIGHT_MARGIN,
            x1 - LAST_MOVE_HIGHLIGHT_MARGIN, y1 - LAST_MOVE_HIGHLIGHT_MARGIN,
            outline=LAST_MOVE_OUTLINE_COLOR, width=LAST_MOVE_HIGHLIGHT_WIDTH
        )

    def _draw_valid_move_hints(self) -> None:
        """Draw visual hints for all valid moves available to the current player."""
        if not self.show_hints or self.game.current_player is None:
            return

        moves = self.game.get_valid_moves()
        hint_color = (
            HINT_COLOR_BLACK
            if self.game.current_player == ReversiGame.BLACK
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
            passed_player: The player who had to pass, or None if game is over.
        """
        if passed_player is None:
            return

        player_name = "Black" if passed_player == ReversiGame.BLACK else "White"
        messagebox.showinfo("Pass", f"{player_name} has no valid moves and must pass.")
        logger.info(f"{player_name} passed")

    def _show_game_over(self) -> None:
        """Display the game-over dialog with the final result."""
        score = self.game.get_score()
        winner = self.game.get_winner()

        if winner == ReversiGame.BLACK:
            result_msg = "Black wins!"
        elif winner == ReversiGame.WHITE:
            result_msg = "White wins!"
        else:
            result_msg = "It's a tie!"

        messagebox.showinfo(
            "Game Over",
            f"Final Score:\nBlack: {score['black']}   White: {score['white']}\n\n{result_msg}"
        )
        logger.info(f"Game over. {result_msg} Final score - Black: {score['black']}, White: {score['white']}")