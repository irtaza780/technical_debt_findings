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
NARRATIVE_HEIGHT = 18
ITEMS_LISTBOX_HEIGHT = 7
RELATIONSHIPS_LISTBOX_HEIGHT = 7
VARIABLES_LISTBOX_HEIGHT = 6

# Color Constants
COLOR_BACKGROUND = "#fafafa"
COLOR_TEXT_MUTED = "#333"

# Layout Weights
CONTENT_WEIGHT = 3
SIDEBAR_WEIGHT = 1

# Theme
DEFAULT_THEME = "clam"


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
        
        title = ttk.Label(self, text=GAME_TITLE, font=FONT_TITLE)
        subtitle = ttk.Label(self, text=GAME_SUBTITLE, font=FONT_SUBTITLE)
        btn_new = ttk.Button(self, text="New Game", command=on_new_game)
        btn_load = ttk.Button(self, text="Load Game", command=on_load_game)

        title.grid(row=0, column=0, pady=(0, PADDING_MEDIUM), sticky="w")
        subtitle.grid(row=1, column=0, pady=(0, PADDING_LARGE), sticky="w")
        btn_new.grid(row=2, column=0, sticky="ew")
        btn_load.grid(row=3, column=0, pady=(PADDING_MEDIUM, 0), sticky="ew")
        
        self.columnconfigure(0, weight=1)


class GameFrame(ttk.Frame):
    """
    Main game interface displaying narrative, choices, and game state.
    
    Attributes:
        engine: Story engine instance managing game state.
        text: Text widget displaying narrative.
        choices_frame: Frame containing choice buttons.
        lst_items: Listbox displaying inventory items.
        lst_relationships: Listbox displaying relationship scores.
        lst_vars: Listbox displaying game variables.
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

        # Configure grid layout
        self.columnconfigure(0, weight=CONTENT_WEIGHT, uniform="cols")
        self.columnconfigure(1, weight=SIDEBAR_WEIGHT, uniform="cols")
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Create main content area
        self._create_content_area()
        
        # Create sidebar
        self._create_sidebar()
        
        # Create control buttons
        self._create_controls()

        self.update_ui()

    def _create_content_area(self) -> None:
        """Create the narrative text and choices display area."""
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_DEFAULT))
        
        # Narrative section
        lbl_story = ttk.Label(left_frame, text="Story", font=FONT_SECTION_LARGE)
        lbl_story.pack(anchor="w")
        
        self.text = tk.Text(
            left_frame,
            wrap="word",
            height=NARRATIVE_HEIGHT,
            state="disabled",
            bg=COLOR_BACKGROUND,
        )
        self.text.pack(fill="both", expand=True, pady=(0, PADDING_MEDIUM))
        
        # Choices section
        lbl_choices = ttk.Label(left_frame, text="Choices", font=FONT_SECTION_LARGE)
        lbl_choices.pack(anchor="w")
        
        self.choices_frame = ttk.Frame(left_frame)
        self.choices_frame.pack(fill="x", expand=False)

    def _create_sidebar(self) -> None:
        """Create the sidebar displaying items, relationships, and variables."""
        sidebar = ttk.Frame(self)
        sidebar.grid(row=0, column=1, sticky="nsew")
        
        # Items section
        self._create_listbox_section(
            sidebar,
            "Items",
            ITEMS_LISTBOX_HEIGHT,
            lambda: self.lst_items,
        )
        self.lst_items = tk.Listbox(sidebar, height=ITEMS_LISTBOX_HEIGHT)
        self.lst_items.pack(fill="x", pady=(0, PADDING_MEDIUM))
        
        # Relationships section
        lbl_rel = ttk.Label(sidebar, text="Relationships", font=FONT_SECTION_SMALL)
        lbl_rel.pack(anchor="w")
        
        self.lst_relationships = tk.Listbox(sidebar, height=RELATIONSHIPS_LISTBOX_HEIGHT)
        self.lst_relationships.pack(fill="x", pady=(0, PADDING_MEDIUM))
        
        # Variables section
        lbl_vars = ttk.Label(sidebar, text="Variables", font=FONT_SECTION_SMALL)
        lbl_vars.pack(anchor="w")
        
        self.lst_vars = tk.Listbox(sidebar, height=VARIABLES_LISTBOX_HEIGHT)
        self.lst_vars.pack(fill="x")

    def _create_listbox_section(
        self,
        parent: tk.Widget,
        title: str,
        height: int,
        listbox_getter: Callable[[], tk.Listbox],
    ) -> None:
        """
        Create a labeled listbox section.
        
        Args:
            parent: Parent widget.
            title: Section title.
            height: Listbox height.
            listbox_getter: Function returning the listbox widget.
        """
        lbl = ttk.Label(parent, text=title, font=FONT_SECTION_SMALL)
        lbl.pack(anchor="w")

    def _create_controls(self) -> None:
        """Create control buttons (Save, Load, Restart)."""
        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PADDING_DEFAULT, 0))
        
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)
        
        btn_save = ttk.Button(controls, text="Save", command=self.on_save)
        btn_load = ttk.Button(controls, text="Load", command=self.on_load)
        btn_restart = ttk.Button(controls, text="Restart", command=self.on_restart)
        
        btn_save.grid(row=0, column=0, sticky="ew")
        btn_load.grid(row=0, column=1, sticky="ew", padx=PADDING_DEFAULT)
        btn_restart.grid(row=0, column=2, sticky="ew")

    def set_story_text(self, text: str) -> None:
        """
        Update the narrative text display.
        
        Args:
            text: Narrative text to display.
        """
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")

    def _clear_choices_frame(self) -> None:
        """Remove all choice buttons from the choices frame."""
        for child in self.choices_frame.winfo_children():
            child.destroy()

    def _create_end_game_ui(self) -> None:
        """Create UI for story ending."""
        lbl = ttk.Label(
            self.choices_frame,
            text="The story has reached an ending.",
            foreground=COLOR_TEXT_MUTED,
        )
        lbl.pack(anchor="w", pady=(0, PADDING_MEDIUM))
        
        btn = ttk.Button(self.choices_frame, text="Play Again", command=self.on_restart)
        btn.pack(anchor="w")

    def _create_choice_buttons(self, choices: List[Choice]) -> None:
        """
        Create buttons for available choices.
        
        Args:
            choices: List of available choices.
        """
        for choice in choices:
            btn = ttk.Button(
                self.choices_frame,
                text=choice.text,
                command=lambda c=choice: self.on_choice_clicked(c),
            )
            btn.pack(anchor="w", pady=PADDING_SMALL)

    def build_choices(self, choices: List[Choice]) -> None:
        """
        Build and display choice buttons.
        
        Args:
            choices: List of available choices.
        """
        self._clear_choices_frame()

        if not choices:
            self._create_end_game_ui()
            return

        self._create_choice_buttons(choices)

    def on_choice_clicked(self, choice: Choice) -> None:
        """
        Handle choice selection.
        
        Args:
            choice: Selected choice.
        """
        ok = self.engine.choose(choice)
        if not ok:
            messagebox.showerror(
                "Choice Error",
                "That choice is no longer valid or the target node is missing.",
            )
            logger.error(f"Invalid choice selected: {choice.text}")
        self.update_ui()

    def _update_items_display(self) -> None:
        """Update the items listbox with current inventory."""
        self.lst_items.delete(0, "end")
        for item in sorted(list(self.engine.state.items)):
            self.lst_items.insert("end", f"- {item}")

    def _update_relationships_display(self) -> None:
        """Update the relationships listbox with current relationship scores."""
        self.lst_relationships.delete(0, "end")
        for name, score in sorted(self.engine.state.relationships.items()):
            self.lst_relationships.insert("end", f"{name}: {score}")

    def _update_variables_display(self) -> None:
        """Update the variables listbox with current game variables."""
        self.lst_vars.delete(0, "end")
        for name, value in sorted(self.engine.state.variables.items()):
            self.lst_vars.insert("end", f"{name}: {value}")

    def update_sidebar(self) -> None:
        """Update all sidebar displays (items, relationships, variables)."""
        self._update_items_display()
        self._update_relationships_display()
        self._update_variables_display()

    def update_ui(self) -> None:
        """Update entire game UI with current engine state."""
        node = self.engine.get_current_node()
        self.set_story_text(node.text)
        choices = self.engine.get_available_choices()
        self.build_choices(choices)
        self.update_sidebar()


class StoryApp(tk.Tk):
    """
    Root application window managing game flow and persistence.
    
    Attributes:
        engine: Story engine instance.
        container: Main container frame.
        start_frame: Start menu frame.
        game_frame: Game interface frame.
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
            style.theme_use(DEFAULT_THEME)
        except tk.TclError:
            logger.warning(f"Theme '{DEFAULT_THEME}' not available, using default")

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts for common actions."""
        self.bind("<Control-s>", lambda e: self.save_game_dialog())
        self.bind("<Control-o>", lambda e: self.load_game_dialog())
        self.bind("<F5>", lambda e: self.restart_game())

    def switch_to_game(self) -> None:
        """Switch from start screen to game screen."""
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
        self.engine.reset()
        logger.info("New game started")
        self.switch_to_game()

    def restart_game(self) -> None:
        """Restart the current game after confirmation."""
        if messagebox.askyesno(
            "Restart",
            "Start a new game? Current progress will be lost.",
        ):
            self.engine.reset()
            logger.info("Game restarted")
            if self.game_frame:
                self.game_frame.update_ui()
            else:
                self.switch_to_game()

    def save_game_dialog(self) -> None:
        """Open save game