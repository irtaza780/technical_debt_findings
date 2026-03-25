import logging
import tkinter as tk
from tkinter import messagebox
from game import MinesweeperGame

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Game difficulty configurations
DIFFICULTY_CONFIGS = {
    "Beginner": (9, 9, 10),
    "Intermediate": (16, 16, 40),
    "Expert": (30, 16, 99),
}

# Cell number colors
NUMBER_COLORS = {
    1: "#1e90ff",
    2: "#228B22",
    3: "#dc143c",
    4: "#00008b",
    5: "#8b0000",
    6: "#008b8b",
    7: "#000000",
    8: "#696969",
}

# Cross-platform symbols
FLAG_CHAR = "F"
MINE_CHAR = "*"

# UI Constants
BG_COLOR_MAIN = "#e6e6e6"
BG_COLOR_HEADER = "#f2f2f2"
BG_COLOR_BOARD = "#bdbdbd"
BG_COLOR_CELL_HIDDEN = "#d0d0d0"
BG_COLOR_CELL_REVEALED = "#f2f2f2"
BG_COLOR_CELL_FLAGGED = "#ffd6d6"
BG_COLOR_MINE_EXPLODED = "#ff4d4d"
FG_COLOR_FLAG = "#d40000"
FG_COLOR_MINE = "#000000"
FG_COLOR_DISABLED = "#404040"
BUTTON_FONT = ("Arial", 12, "bold")
LABEL_FONT = ("Arial", 11, "bold")
BUTTON_WIDTH = 2
BUTTON_HEIGHT = 1
TIMER_INTERVAL_MS = 1000
PADDING_STANDARD = 8
PADDING_SMALL = 4


class MinesweeperApp(tk.Frame):
    """
    Main Tkinter application for Minesweeper game.
    
    Manages the game interface including difficulty selection, board display,
    user interactions, and game status updates.
    """

    def __init__(self, master=None):
        """
        Initialize the Minesweeper application.
        
        Args:
            master: Parent Tkinter widget.
        """
        super().__init__(master, bg=BG_COLOR_MAIN)
        self.master = master
        self.pack(fill="both", expand=True)
        
        self.current_difficulty = tk.StringVar(value="Beginner")
        self.game = None
        self.buttons = []
        self.timer_id = None
        
        self._build_controls()
        self._new_game()
        logger.info("Minesweeper application initialized")

    def _build_controls(self):
        """Build the control panel with difficulty selector, buttons, and status labels."""
        self._build_header()
        self._build_board_frame()
        self._build_footer()

    def _build_header(self):
        """Build the top control panel with difficulty selector and status labels."""
        header = tk.Frame(self, bg=BG_COLOR_HEADER, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        header.pack(side="top", fill="x")

        # Difficulty selector
        tk.Label(header, text="Difficulty:", bg=BG_COLOR_HEADER).pack(side="left")
        diff_menu = tk.OptionMenu(
            header,
            self.current_difficulty,
            *DIFFICULTY_CONFIGS.keys(),
            command=lambda _: self._new_game(),
        )
        diff_menu.config(width=12)
        diff_menu.pack(side="left", padx=(PADDING_SMALL, 12))

        # New game button
        reset_btn = tk.Button(header, text="New Game", command=self._new_game)
        reset_btn.pack(side="left")

        # Spacer
        tk.Label(header, text="   ", bg=BG_COLOR_HEADER).pack(side="left")

        # Mines remaining label
        self.mines_label = tk.Label(
            header,
            text="Mines: 0",
            font=LABEL_FONT,
            bg=BG_COLOR_HEADER
        )
        self.mines_label.pack(side="left")

        # Spacer
        tk.Label(header, text="   ", bg=BG_COLOR_HEADER).pack(side="left")

        # Timer label
        self.timer_label = tk.Label(
            header,
            text="Time: 0",
            font=LABEL_FONT,
            bg=BG_COLOR_HEADER
        )
        self.timer_label.pack(side="left")

    def _build_board_frame(self):
        """Build the game board container frame."""
        self.board_frame = tk.Frame(
            self,
            bg=BG_COLOR_BOARD,
            padx=PADDING_STANDARD,
            pady=PADDING_STANDARD
        )
        self.board_frame.pack(side="top", expand=True)

    def _build_footer(self):
        """Build the footer with instructions."""
        footer = tk.Frame(self, bg=BG_COLOR_HEADER, padx=PADDING_STANDARD, pady=PADDING_SMALL)
        footer.pack(side="bottom", fill="x")
        instructions = (
            "Left-click: reveal | Right-click / Middle-click / Ctrl+Click: flag/unflag"
        )
        tk.Label(footer, text=instructions, bg=BG_COLOR_HEADER).pack(side="left")

    def _new_game(self):
        """Initialize a new game with the selected difficulty."""
        self._cancel_timer()
        
        width, height, mines = DIFFICULTY_CONFIGS[self.current_difficulty.get()]
        self.game = MinesweeperGame(width, height, mines)
        logger.info(f"New game started: {self.current_difficulty.get()} ({width}x{height}, {mines} mines)")
        
        self._rebuild_board(width, height)
        self._update_mines_label()
        self._update_timer_label(force_zero=True)

    def _rebuild_board(self, width, height):
        """
        Rebuild the game board grid with buttons.
        
        Args:
            width: Number of columns.
            height: Number of rows.
        """
        # Clear existing buttons
        for child in self.board_frame.winfo_children():
            child.destroy()
        
        self.buttons = [[None for _ in range(width)] for _ in range(height)]

        # Create button grid
        for y in range(height):
            for x in range(width):
                btn = self._create_cell_button(x, y)
                btn.grid(row=y, column=x, sticky="nsew")
                self.buttons[y][x] = btn

        # Configure grid weights for responsiveness
        for y in range(height):
            self.board_frame.rowconfigure(y, weight=1)
        for x in range(width):
            self.board_frame.columnconfigure(x, weight=1)

    def _create_cell_button(self, x, y):
        """
        Create a single cell button with event bindings.
        
        Args:
            x: Column index.
            y: Row index.
            
        Returns:
            Configured tk.Button widget.
        """
        btn = tk.Button(
            self.board_frame,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            text="",
            relief="raised",
            bg=BG_COLOR_CELL_HIDDEN,
            activebackground="#c8c8c8",
            font=BUTTON_FONT,
            disabledforeground=FG_COLOR_DISABLED,
        )
        
        # Bind click events
        btn.bind("<Button-1>", lambda e, cx=x, cy=y: self._on_left_click(cx, cy))
        btn.bind("<Button-3>", lambda e, cx=x, cy=y: self._on_right_click(cx, cy))
        btn.bind("<Button-2>", lambda e, cx=x, cy=y: self._on_right_click(cx, cy))
        btn.bind("<Control-Button-1>", lambda e, cx=x, cy=y: self._on_right_click(cx, cy))
        
        return btn

    def _on_left_click(self, x, y):
        """
        Handle left-click (reveal cell) event.
        
        Args:
            x: Column index.
            y: Row index.
        """
        if self.game.state != "playing":
            return
        
        result, changed, exploded_at = self.game.left_click(x, y)

        # Start timer on first reveal
        if self.game.started and self.timer_id is None and self.game.state == "playing":
            self._schedule_timer_tick()

        self._refresh_cells(changed, exploded_at)
        self._update_mines_label()

        # Handle game end conditions
        if result == "lost":
            self._reveal_all()
            logger.info("Game lost - mine hit")
            messagebox.showinfo("Minesweeper", "Boom! You hit a mine. Game over.")
        elif result == "won":
            self._reveal_all()
            logger.info("Game won - board cleared")
            messagebox.showinfo("Minesweeper", "Congratulations! You cleared the board.")

    def _on_right_click(self, x, y):
        """
        Handle right-click (flag/unflag cell) event.
        
        Args:
            x: Column index.
            y: Row index.
        """
        if self.game.state != "playing":
            return
        
        self.game.right_click(x, y)
        self._refresh_cells({(x, y)}, None)
        self._update_mines_label()

    def _refresh_cells(self, coords, exploded_at):
        """
        Update the visual appearance of specified cells.
        
        Args:
            coords: Set of (x, y) tuples representing cells to update.
            exploded_at: Optional (x, y) tuple of the cell that triggered game loss.
        """
        for x, y in coords:
            cell = self.game.board.get_cell(x, y)
            btn = self.buttons[y][x]
            
            if cell.revealed:
                self._update_revealed_cell(btn, cell, x, y, exploded_at)
            else:
                self._update_hidden_cell(btn, cell)

    def _update_revealed_cell(self, btn, cell, x, y, exploded_at):
        """
        Update the appearance of a revealed cell.
        
        Args:
            btn: The button widget.
            cell: The cell object.
            x: Column index.
            y: Row index.
            exploded_at: Optional (x, y) of exploded mine.
        """
        btn.config(relief="sunken", bg=BG_COLOR_CELL_REVEALED, state="disabled")
        
        if cell.has_mine:
            btn.config(text=MINE_CHAR, disabledforeground=FG_COLOR_MINE)
            if exploded_at == (x, y):
                btn.config(bg=BG_COLOR_MINE_EXPLODED)
        else:
            adjacent_count = cell.adjacent
            if adjacent_count > 0:
                btn.config(
                    text=str(adjacent_count),
                    disabledforeground=NUMBER_COLORS.get(adjacent_count, FG_COLOR_MINE)
                )
            else:
                btn.config(text="")

    def _update_hidden_cell(self, btn, cell):
        """
        Update the appearance of a hidden cell.
        
        Args:
            btn: The button widget.
            cell: The cell object.
        """
        btn.config(relief="raised", state="normal")
        
        if cell.flagged:
            btn.config(text=FLAG_CHAR, fg=FG_COLOR_FLAG, bg=BG_COLOR_CELL_FLAGGED)
        else:
            btn.config(text="", bg=BG_COLOR_CELL_HIDDEN)

    def _reveal_all(self):
        """Reveal all cells to show the final game state."""
        width, height = self.game.board.width, self.game.board.height
        
        # Mark all mines as revealed
        for y in range(height):
            for x in range(width):
                cell = self.game.board.get_cell(x, y)
                if cell.has_mine:
                    cell.revealed = True
        
        # Refresh all cells
        all_coords = {(x, y) for y in range(height) for x in range(width)}
        self._refresh_cells(all_coords, exploded_at=self.game.exploded_at)

    def _update_mines_label(self):
        """Update the mines remaining label."""
        remaining = self.game.board.num_mines - self.game.board.flag_count()
        self.mines_label.config(text=f"Mines: {remaining}")

    def _cancel_timer(self):
        """Cancel the active timer if one exists."""
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def _schedule_timer_tick(self):
        """
        Schedule the next timer update.
        
        Continues scheduling while game is playing, stops when game ends.
        """
        if self.game.state != "playing":
            self.timer_id = None
            self._update_timer_label()
            return
        
        self._update_timer_label()
        self.timer_id = self.after(TIMER_INTERVAL_MS, self._schedule_timer_tick)

    def _update_timer_label(self, force_zero=False):
        """
        Update the timer display label.
        
        Args:
            force_zero: If True, reset timer to 0.
        """
        if force_zero:
            self.timer_label.config(text="Time: 0")
            return
        
        elapsed = int(self.game.elapsed_time())
        self.timer_label.config(text=f"Time: {elapsed}")


def main():
    """Launch the Minesweeper application."""
    root = tk.Tk()
    root.title("Minesweeper")
    root.geometry("600x600")
    app = MinesweeperApp(master=root)
    root.mainloop()


if __name__ == "__main__":
    main()