import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable

from engine import StoryEngine, Choice
import story_data
import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UI Constants
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_TITLE = "Castle of Choices"
GAME_TITLE = "Castle of Choices"
GAME_SUBTITLE = "An interactive storytelling game"

# Font Constants
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)
FONT_SECTION_LARGE = ("Segoe UI", 12, "bold")
FONT_SECTION_SMALL = ("Segoe UI", 11, "bold")

# Layout Constants
PADDING_DEFAULT = 10
PADDING_LARGE = 20
PADDING_SMALL = 4
PADDING_MEDIUM = 8
SIDEBAR_WEIGHT = 1
CONTENT_WEIGHT = 3
TEXT_HEIGHT = 18
ITEMS_HEIGHT = 7
RELATIONSHIPS_HEIGHT = 7
VARIABLES_HEIGHT = 6

# Colors
COLOR_BACKGROUND = "#fafafa"
COLOR_TEXT_MUTED = "#333"

# UI Text
TEXT_STORY = "Story"
TEXT_CHOICES = "Choices"
TEXT_ITEMS = "Items"
TEXT_RELATIONSHIPS = "Relationships"
TEXT_VARIABLES = "Variables"
TEXT_NEW_GAME = "New Game"
TEXT_LOAD_GAME = "Load Game"
TEXT_SAVE = "Save"
TEXT_LOAD = "Load"
TEXT_RESTART = "Restart"
TEXT_PLAY_AGAIN = "Play Again"
TEXT_STORY_ENDING = "The story has reached an ending."
TEXT_CHOICE_ERROR = "Choice Error"
TEXT_CHOICE_ERROR_MSG = "That choice is no longer valid or the target node is missing."
TEXT_RESTART_CONFIRM = "Restart"
TEXT_RESTART_MSG = "Start a new game? Current progress will be lost."

# Keyboard shortcuts
SHORTCUT_SAVE = "<Control-s>"
SHORTCUT_LOAD = "<Control-o>"
SHORTCUT_RESTART = "<F5>"


class StartFrame(ttk.Frame):
    """
    Start menu frame with New Game and Load Game options.
    
    Attributes:
        on_new_game: Callback function for new game button.
        on_load_game: Callback function for load game button.
    """

    def __init__(
        self,
        master: tk.Widget,
        on_new_game: Callable[[], None],
        on_load_game: Callable[[], None],
    ) -> None:
        """
        Initialize the start frame.
        
        Args:
            master: Parent widget.
            on_new_game: Callback when new game is selected.
            on_load_game: Callback when load game is selected.
        """
        super().__init__(master, padding=PADDING_LARGE)
        self._build_ui(on_new_game, on_load_game)

    def _build_ui(
        self,
        on_new_game: Callable[[], None],
        on_load_game: Callable[[], None],
    ) -> None:
        """
        Build the UI components for the start frame.
        
        Args:
            on_new_game: Callback for new game button.
            on_load_game: Callback for load game button.
        """
        title = ttk.Label(self, text=GAME_TITLE, font=FONT_TITLE)
        subtitle = ttk.Label(self, text=GAME_SUBTITLE, font=FONT_SUBTITLE)
        btn_new = ttk.Button(self, text=TEXT_NEW_GAME, command=on_new_game)
        btn_load = ttk.Button(self, text=TEXT_LOAD_GAME, command=on_load_game)

        title.grid(row=0, column=0, pady=(0, PADDING_MEDIUM), sticky="w")
        subtitle.grid(row=1, column=0, pady=(0, PADDING_LARGE), sticky="w")
        btn_new.grid(row=2, column=0, sticky="ew")
        btn_load.grid(row=3, column=0, pady=(PADDING_MEDIUM, 0), sticky="ew")
        self.columnconfigure(0, weight=1)


class GameFrame(ttk.Frame):
    """
    Main game UI frame with narrative, choices, and sidebar information.
    
    Attributes:
        engine: The story engine instance.
        text: Text widget for narrative display.
        choices_frame: Frame containing choice buttons.
        lst_items: Listbox for inventory items.
        lst_relationships: Listbox for relationship scores.
        lst_vars: Listbox for game variables.
    """

    def __init__(
        self,
        master: tk.Widget,
        engine: StoryEngine,
        on_restart: Callable[[], None],
        on_save: Callable[[], None],
        on_load: Callable[[], None],
    ) -> None:
        """
        Initialize the game frame.
        
        Args:
            master: Parent widget.
            engine: Story engine instance.
            on_restart: Callback for restart button.
            on_save: Callback for save button.
            on_load: Callback for load button.
        """
        super().__init__(master, padding=PADDING_DEFAULT)
        self.engine = engine
        self.on_restart = on_restart
        self.on_save = on_save
        self.on_load = on_load

        self._configure_layout()
        self._build_content_area()
        self._build_sidebar()
        self._build_controls()
        self.update_ui()

    def _configure_layout(self) -> None:
        """Configure the grid layout for content and sidebar."""
        self.columnconfigure(0, weight=CONTENT_WEIGHT, uniform="cols")
        self.columnconfigure(1, weight=SIDEBAR_WEIGHT, uniform="cols")
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

    def _build_content_area(self) -> None:
        """Build the narrative text and choices area."""
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_MEDIUM))

        # Story text section
        lbl_story = ttk.Label(left_frame, text=TEXT_STORY, font=FONT_SECTION_LARGE)
        lbl_story.pack(anchor="w")
        self.text = tk.Text(
            left_frame,
            wrap="word",
            height=TEXT_HEIGHT,
            state="disabled",
            bg=COLOR_BACKGROUND,
        )
        self.text.pack(fill="both", expand=True, pady=(0, PADDING_MEDIUM))

        # Choices section
        lbl_choices = ttk.Label(left_frame, text=TEXT_CHOICES, font=FONT_SECTION_LARGE)
        lbl_choices.pack(anchor="w")
        self.choices_frame = ttk.Frame(left_frame)
        self.choices_frame.pack(fill="x", expand=False)

    def _build_sidebar(self) -> None:
        """Build the sidebar with inventory, relationships, and variables."""
        sidebar = ttk.Frame(self)
        sidebar.grid(row=0, column=1, sticky="nsew")

        # Items section
        lbl_inv = ttk.Label(sidebar, text=TEXT_ITEMS, font=FONT_SECTION_SMALL)
        lbl_inv.pack(anchor="w")
        self.lst_items = tk.Listbox(sidebar, height=ITEMS_HEIGHT)
        self.lst_items.pack(fill="x", pady=(0, PADDING_MEDIUM))

        # Relationships section
        lbl_rel = ttk.Label(sidebar, text=TEXT_RELATIONSHIPS, font=FONT_SECTION_SMALL)
        lbl_rel.pack(anchor="w")
        self.lst_relationships = tk.Listbox(sidebar, height=RELATIONSHIPS_HEIGHT)
        self.lst_relationships.pack(fill="x", pady=(0, PADDING_MEDIUM))

        # Variables section
        lbl_vars = ttk.Label(sidebar, text=TEXT_VARIABLES, font=FONT_SECTION_SMALL)
        lbl_vars.pack(anchor="w")
        self.lst_vars = tk.Listbox(sidebar, height=VARIABLES_HEIGHT)
        self.lst_vars.pack(fill="x")

    def _build_controls(self) -> None:
        """Build the control buttons at the bottom."""
        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PADDING_MEDIUM, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)

        btn_save = ttk.Button(controls, text=TEXT_SAVE, command=self.on_save)
        btn_load = ttk.Button(controls, text=TEXT_LOAD, command=self.on_load)
        btn_restart = ttk.Button(controls, text=TEXT_RESTART, command=self.on_restart)

        btn_save.grid(row=0, column=0, sticky="ew")
        btn_load.grid(row=0, column=1, sticky="ew", padx=PADDING_MEDIUM)
        btn_restart.grid(row=0, column=2, sticky="ew")

    def set_story_text(self, text: str) -> None:
        """
        Update the narrative text display.
        
        Args:
            text: The narrative text to display.
        """
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")

    def _clear_choices_frame(self) -> None:
        """Remove all choice buttons from the choices frame."""
        for child in self.choices_frame.winfo_children():
            child.destroy()

    def _build_ending_message(self) -> None:
        """Build the UI for story ending."""
        lbl = ttk.Label(
            self.choices_frame,
            text=TEXT_STORY_ENDING,
            foreground=COLOR_TEXT_MUTED,
        )
        lbl.pack(anchor="w", pady=(0, PADDING_MEDIUM))
        btn = ttk.Button(self.choices_frame, text=TEXT_PLAY_AGAIN, command=self.on_restart)
        btn.pack(anchor="w")

    def build_choices(self, choices: List[Choice]) -> None:
        """
        Build and display choice buttons.
        
        Args:
            choices: List of available choices.
        """
        self._clear_choices_frame()

        if not choices:
            self._build_ending_message()
            return

        for choice in choices:
            btn = ttk.Button(
                self.choices_frame,
                text=choice.text,
                command=lambda c=choice: self.on_choice_clicked(c),
            )
            btn.pack(anchor="w", pady=PADDING_SMALL)

    def on_choice_clicked(self, choice: Choice) -> None:
        """
        Handle choice selection.
        
        Args:
            choice: The selected choice.
        """
        ok = self.engine.choose(choice)
        if not ok:
            messagebox.showerror(TEXT_CHOICE_ERROR, TEXT_CHOICE_ERROR_MSG)
            logger.warning(f"Invalid choice selected: {choice.text}")
        self.update_ui()

    def _update_items_listbox(self) -> None:
        """Update the items listbox with current inventory."""
        self.lst_items.delete(0, "end")
        for item in sorted(list(self.engine.state.items)):
            self.lst_items.insert("end", f"- {item}")

    def _update_relationships_listbox(self) -> None:
        """Update the relationships listbox with current relationship scores."""
        self.lst_relationships.delete(0, "end")
        for name, score in sorted(self.engine.state.relationships.items()):
            self.lst_relationships.insert("end", f"{name}: {score}")

    def _update_variables_listbox(self) -> None:
        """Update the variables listbox with current game variables."""
        self.lst_vars.delete(0, "end")
        for name, value in sorted(self.engine.state.variables.items()):
            self.lst_vars.insert("end", f"{name}: {value}")

    def update_sidebar(self) -> None:
        """Update all sidebar information."""
        self._update_items_listbox()
        self._update_relationships_listbox()
        self._update_variables_listbox()

    def update_ui(self) -> None:
        """Update all UI elements to reflect current game state."""
        node = self.engine.get_current_node()
        self.set_story_text(node.text)
        choices = self.engine.get_available_choices()
        self.build_choices(choices)
        self.update_sidebar()


class StoryApp(tk.Tk):
    """
    Root application window managing frames and game state.
    
    Attributes:
        engine: The story engine instance.
        start_frame: The start menu frame.
        game_frame: The main game frame.
    """

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._apply_theme()
        self.engine = StoryEngine(story_data.STORY)
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.start_frame = StartFrame(
            self.container,
            on_new_game=self.new_game,
            on_load_game=self.load_game_dialog,
        )
        self.start_frame.pack(fill="both", expand=True)

        self.game_frame: Optional[GameFrame] = None

        self._bind_keyboard_shortcuts()

    def _apply_theme(self) -> None:
        """Apply theme to the application."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            logger.debug("Theme 'clam' not available, using default theme")

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts to their respective functions."""
        self.bind(SHORTCUT_SAVE, lambda e: self.save_game_dialog())
        self.bind(SHORTCUT_LOAD, lambda e: self.load_game_dialog())
        self.bind(SHORTCUT_RESTART, lambda e: self.restart_game())

    def switch_to_game(self) -> None:
        """Switch from start frame to game frame."""
        if self.start_frame:
            self.start_frame.pack_forget()

        if not self.game_frame:
            self.game_frame = GameFrame(
                self.container,
                engine=self.engine,
                on_restart=self.restart_game,
                on_save=self.save_game_dialog,
                on_load=self.load_game_dialog,
            )
            self.game_frame.pack(fill="both", expand=True)
        else:
            self.game_frame.pack(fill="both", expand=True)
            self.game_frame.update_ui()

    def new_game(self) -> None:
        """Start a new game."""
        logger.info("Starting new game")
        self.engine.reset()
        self.switch_to_game()

    def restart_game(self) -> None:
        """Restart the current game after confirmation."""
        if messagebox.askyesno(TEXT_