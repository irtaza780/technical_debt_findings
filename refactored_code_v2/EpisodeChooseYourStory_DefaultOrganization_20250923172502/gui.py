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
PADDING_DEFAULT = 20
PADDING_SMALL = 10
PADDING_MEDIUM = 8
PADDING_LARGE = 10

# Sidebar Constants
SIDEBAR_ITEMS_HEIGHT = 7
SIDEBAR_RELATIONSHIPS_HEIGHT = 7
SIDEBAR_VARIABLES_HEIGHT = 6

# Text Widget Constants
NARRATIVE_TEXT_HEIGHT = 18
TEXT_WIDGET_BG = "#fafafa"
TEXT_WIDGET_WRAP = "word"

# Color Constants
TEXT_COLOR_MUTED = "#333"

# Layout Grid Constants
LAYOUT_CONTENT_WEIGHT = 3
LAYOUT_SIDEBAR_WEIGHT = 1
LAYOUT_CONTENT_COLUMN = 0
LAYOUT_SIDEBAR_COLUMN = 1
LAYOUT_CONTROLS_ROW = 1

# Control Button Constants
CONTROL_BUTTON_COUNT = 3

# Error Messages
ERROR_INVALID_CHOICE = "That choice is no longer valid or the target node is missing."
ERROR_THEME_FALLBACK = "Could not apply 'clam' theme, using default."

# Dialog Messages
RESTART_DIALOG_TITLE = "Restart"
RESTART_DIALOG_MESSAGE = "Start a new game? Current progress will be lost."

# UI Text Constants
TEXT_STORY = "Story"
TEXT_CHOICES = "Choices"
TEXT_ITEMS = "Items"
TEXT_RELATIONSHIPS = "Relationships"
TEXT_VARIABLES = "Variables"
TEXT_ENDING_MESSAGE = "The story has reached an ending."
TEXT_PLAY_AGAIN = "Play Again"
TEXT_SAVE = "Save"
TEXT_LOAD = "Load"
TEXT_RESTART = "Restart"
TEXT_NEW_GAME = "New Game"
TEXT_LOAD_GAME = "Load Game"


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
        super().__init__(master, padding=PADDING_DEFAULT)
        
        self._create_widgets(on_new_game, on_load_game)

    def _create_widgets(
        self,
        on_new_game: Callable[[], None],
        on_load_game: Callable[[], None],
    ) -> None:
        """
        Create and layout all widgets for the start frame.
        
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
    Main game UI frame containing narrative, choices, and sidebar information.
    
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
        super().__init__(master, padding=PADDING_SMALL)
        self.engine = engine
        self.on_restart = on_restart
        self.on_save = on_save
        self.on_load = on_load

        self._configure_layout()
        self._create_content_area()
        self._create_sidebar()
        self._create_controls()
        
        self.update_ui()

    def _configure_layout(self) -> None:
        """Configure the grid layout for the game frame."""
        self.columnconfigure(LAYOUT_CONTENT_COLUMN, weight=LAYOUT_CONTENT_WEIGHT, uniform="cols")
        self.columnconfigure(LAYOUT_SIDEBAR_COLUMN, weight=LAYOUT_SIDEBAR_WEIGHT, uniform="cols")
        self.rowconfigure(0, weight=1)
        self.rowconfigure(LAYOUT_CONTROLS_ROW, weight=0)

    def _create_content_area(self) -> None:
        """Create the narrative text and choices area."""
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=LAYOUT_CONTENT_COLUMN, sticky="nsew", padx=(0, PADDING_SMALL))

        lbl_story = ttk.Label(left_frame, text=TEXT_STORY, font=FONT_SECTION_LARGE)
        lbl_story.pack(anchor="w")
        
        self.text = tk.Text(
            left_frame,
            wrap=TEXT_WIDGET_WRAP,
            height=NARRATIVE_TEXT_HEIGHT,
            state="disabled",
            bg=TEXT_WIDGET_BG,
        )
        self.text.pack(fill="both", expand=True, pady=(0, PADDING_MEDIUM))

        lbl_choices = ttk.Label(left_frame, text=TEXT_CHOICES, font=FONT_SECTION_LARGE)
        lbl_choices.pack(anchor="w")
        
        self.choices_frame = ttk.Frame(left_frame)
        self.choices_frame.pack(fill="x", expand=False)

    def _create_sidebar(self) -> None:
        """Create the sidebar with inventory, relationships, and variables."""
        sidebar = ttk.Frame(self)
        sidebar.grid(row=0, column=LAYOUT_SIDEBAR_COLUMN, sticky="nsew")

        self._create_sidebar_section(
            sidebar,
            TEXT_ITEMS,
            SIDEBAR_ITEMS_HEIGHT,
            0,
        )
        self.lst_items = tk.Listbox(sidebar, height=SIDEBAR_ITEMS_HEIGHT)
        self.lst_items.pack(fill="x", pady=(0, PADDING_MEDIUM))

        self._create_sidebar_section(
            sidebar,
            TEXT_RELATIONSHIPS,
            SIDEBAR_RELATIONSHIPS_HEIGHT,
            2,
        )
        self.lst_relationships = tk.Listbox(sidebar, height=SIDEBAR_RELATIONSHIPS_HEIGHT)
        self.lst_relationships.pack(fill="x", pady=(0, PADDING_MEDIUM))

        self._create_sidebar_section(
            sidebar,
            TEXT_VARIABLES,
            SIDEBAR_VARIABLES_HEIGHT,
            4,
        )
        self.lst_vars = tk.Listbox(sidebar, height=SIDEBAR_VARIABLES_HEIGHT)
        self.lst_vars.pack(fill="x")

    def _create_sidebar_section(
        self,
        parent: ttk.Frame,
        title: str,
        height: int,
        row: int,
    ) -> None:
        """
        Create a labeled section in the sidebar.
        
        Args:
            parent: Parent frame.
            title: Section title.
            height: Height of the listbox.
            row: Grid row position.
        """
        lbl = ttk.Label(parent, text=title, font=FONT_SECTION_SMALL)
        lbl.pack(anchor="w")

    def _create_controls(self) -> None:
        """Create the control buttons at the bottom of the frame."""
        controls = ttk.Frame(self)
        controls.grid(
            row=LAYOUT_CONTROLS_ROW,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(PADDING_LARGE, 0),
        )
        
        # Configure equal column weights for buttons
        for col in range(CONTROL_BUTTON_COUNT):
            controls.columnconfigure(col, weight=1)

        btn_save = ttk.Button(controls, text=TEXT_SAVE, command=self.on_save)
        btn_load = ttk.Button(controls, text=TEXT_LOAD, command=self.on_load)
        btn_restart = ttk.Button(controls, text=TEXT_RESTART, command=self.on_restart)

        btn_save.grid(row=0, column=0, sticky="ew")
        btn_load.grid(row=0, column=1, sticky="ew", padx=PADDING_SMALL)
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

    def build_choices(self, choices: List[Choice]) -> None:
        """
        Build and display choice buttons.
        
        Args:
            choices: List of available choices.
        """
        # Clear previous choice buttons
        for child in self.choices_frame.winfo_children():
            child.destroy()

        if not choices:
            self._display_ending_state()
            return

        for choice in choices:
            btn = ttk.Button(
                self.choices_frame,
                text=choice.text,
                command=lambda c=choice: self.on_choice_clicked(c),
            )
            btn.pack(anchor="w", pady=PADDING_MEDIUM)

    def _display_ending_state(self) -> None:
        """Display the ending message and play again button."""
        lbl = ttk.Label(
            self.choices_frame,
            text=TEXT_ENDING_MESSAGE,
            foreground=TEXT_COLOR_MUTED,
        )
        lbl.pack(anchor="w", pady=(0, PADDING_MEDIUM))
        
        btn = ttk.Button(self.choices_frame, text=TEXT_PLAY_AGAIN, command=self.on_restart)
        btn.pack(anchor="w")

    def on_choice_clicked(self, choice: Choice) -> None:
        """
        Handle a choice selection.
        
        Args:
            choice: The selected choice.
        """
        ok = self.engine.choose(choice)
        if not ok:
            messagebox.showerror("Choice Error", ERROR_INVALID_CHOICE)
            logger.warning(f"Invalid choice selected: {choice.text}")
        self.update_ui()

    def _update_listbox(
        self,
        listbox: tk.Listbox,
        items: dict | set,
        format_func: Callable[[str, any], str] = None,
    ) -> None:
        """
        Update a listbox with items.
        
        Args:
            listbox: The listbox widget to update.
            items: Dictionary or set of items to display.
            format_func: Optional function to format each item.
        """
        listbox.delete(0, "end")
        
        if isinstance(items, dict):
            sorted_items = sorted(items.items())
            for key, value in sorted_items:
                if format_func:
                    text = format_func(key, value)
                else:
                    text = f"{key}: {value}"
                listbox.insert("end", text)
        else:
            sorted_items = sorted(list(items))
            for item in sorted_items:
                if format_func:
                    text = format_func(item, None)
                else:
                    text = f"- {item}"
                listbox.insert("end", text)

    def update_sidebar(self) -> None:
        """Update all sidebar information displays."""
        self._update_listbox(
            self.lst_items,
            self.engine.state.items,
            lambda item, _: f"- {item}",
        )
        self._update_listbox(
            self.lst_relationships,
            self.engine.state.relationships,
        )
        self._update_listbox(
            self.lst_vars,
            self.engine.state.variables,
        )

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
        """Apply the application theme."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            logger.warning(ERROR_THEME_FALLBACK)

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts for