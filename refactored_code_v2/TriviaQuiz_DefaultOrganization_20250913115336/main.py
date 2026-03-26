import logging
import os
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List

from question_bank import get_builtin_banks, load_bank_from_json
from quiz_manager import QuizSession
from models import Question

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# UI Constants
WINDOW_WIDTH = 820
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 720
WINDOW_MIN_HEIGHT = 520
HEADER_FONT = ("Segoe UI", 20, "bold")
TITLE_FONT = ("Segoe UI", 14, "bold")
QUESTION_FONT = ("Segoe UI", 12)
RESULT_FONT = ("Segoe UI", 16, "bold")
LABEL_FONT = ("Segoe UI", 11, "bold")
SPINBOX_MIN_QUESTIONS = 1
SPINBOX_MAX_QUESTIONS = 10
CORRECT_COLOR = "#0a7f20"
INCORRECT_COLOR = "#a01919"
DISABLED_TEXT_COLOR = "#555"
CANVAS_PADDING = 24
QUESTION_WRAPLENGTH = 760

# Quiz Constants
DEFAULT_QUESTION_COUNT = 5
MIN_QUESTION_COUNT = 1
CUSTOM_BANK_PREFIX = "Custom: "
NO_SELECTION_VALUE = -1


class QuizApp(tk.Tk):
    """Main application window for the Trivia Quiz GUI."""

    def __init__(self):
        """Initialize the Quiz application with frames and state."""
        super().__init__()
        self.title("Trivia Quiz")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Application state
        self.banks = get_builtin_banks()
        self.current_session: Optional[QuizSession] = None
        self.selected_bank_name: Optional[str] = None
        self.selected_questions: Optional[List[Question]] = None

        # Container for frames
        self._setup_frame_container()
        self._initialize_frames()
        self.show_frame("StartFrame")

    def _setup_frame_container(self) -> None:
        """Set up the main container frame for all screens."""
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.container = container

    def _initialize_frames(self) -> None:
        """Initialize all application frames."""
        self.frames = {}
        for frame_class in (StartFrame, QuizFrame, ResultFrame):
            frame = frame_class(parent=self.container, controller=self)
            self.frames[frame_class.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, name: str) -> None:
        """
        Display the specified frame.

        Args:
            name: The class name of the frame to display.
        """
        frame = self.frames[name]
        if name == "StartFrame":
            frame.refresh_banks()
        frame.tkraise()

    def get_bank_names(self) -> List[str]:
        """
        Get all available question bank names.

        Returns:
            List of bank names.
        """
        return list(self.banks.keys())

    def add_custom_bank(self, path: str, questions: List[Question]) -> str:
        """
        Add a custom question bank from a file path.

        Args:
            path: File path of the question bank.
            questions: List of Question objects.

        Returns:
            The display name assigned to the custom bank.
        """
        base_name = os.path.basename(path)
        display_name = f"{CUSTOM_BANK_PREFIX}{base_name}"
        suffix = 1

        # Ensure unique name
        while display_name in self.banks:
            suffix += 1
            display_name = f"{CUSTOM_BANK_PREFIX}{base_name} ({suffix})"

        self.banks[display_name] = questions
        logger.info(f"Added custom bank: {display_name} with {len(questions)} questions")
        return display_name

    def start_quiz(
        self,
        bank_name: str,
        count: int,
        shuffle: bool,
        show_answers: bool
    ) -> None:
        """
        Start a new quiz session.

        Args:
            bank_name: Name of the question bank to use.
            count: Number of questions to include.
            shuffle: Whether to shuffle the questions.
            show_answers: Whether to show answers after quiz completion.

        Raises:
            Shows error messagebox if bank not found.
        """
        if bank_name not in self.banks:
            messagebox.showerror("Error", "Selected question bank not found.")
            logger.error(f"Bank not found: {bank_name}")
            return

        questions = list(self.banks[bank_name])

        if shuffle:
            random.shuffle(questions)

        # Validate and constrain question count
        count = max(MIN_QUESTION_COUNT, min(count, len(questions)))
        questions = questions[:count]

        self.selected_bank_name = bank_name
        self.selected_questions = questions
        self.current_session = QuizSession(questions, show_answers=show_answers)

        logger.info(f"Started quiz: {bank_name} with {count} questions")

        # Prepare QuizFrame with the first question
        quiz_frame = self.frames["QuizFrame"]
        quiz_frame.reset()
        quiz_frame.load_question()
        self.show_frame("QuizFrame")

    def finish_quiz(self) -> None:
        """Finish the current quiz and show results."""
        self.show_frame("ResultFrame")
        result_frame = self.frames["ResultFrame"]
        result_frame.render_results()
        logger.info("Quiz finished, showing results")

    def restart(self) -> None:
        """Clear the current session and return to the start screen."""
        self.current_session = None
        self.selected_bank_name = None
        self.selected_questions = None
        self.show_frame("StartFrame")
        logger.info("Quiz restarted")


class StartFrame(ttk.Frame):
    """Frame for quiz configuration and startup."""

    def __init__(self, parent, controller: QuizApp):
        """
        Initialize the start frame.

        Args:
            parent: Parent widget.
            controller: Reference to the main QuizApp.
        """
        super().__init__(parent)
        self.controller = controller

        # Variables
        self.bank_var = tk.StringVar(value="")
        self.show_answers_var = tk.BooleanVar(value=True)
        self.shuffle_var = tk.BooleanVar(value=True)
        self.count_var = tk.IntVar(value=DEFAULT_QUESTION_COUNT)
        self.current_bank_size = 0

        self._build_layout()
        self.refresh_banks()

    def _build_layout(self) -> None:
        """Build the UI layout for the start frame."""
        self._build_header()
        content = ttk.Frame(self)
        content.pack(fill="x", padx=20)
        self._build_bank_selection(content)
        self._build_options(content)
        self._build_action_buttons()

    def _build_header(self) -> None:
        """Build the header section."""
        header = ttk.Label(self, text="Trivia Quiz", font=HEADER_FONT)
        header.pack(pady=(20, 10))

        desc = ttk.Label(
            self,
            text="Choose a question bank, configure options, and click Start to begin."
        )
        desc.pack(pady=(0, 15))

    def _build_bank_selection(self, parent: ttk.Frame) -> None:
        """
        Build the bank selection section.

        Args:
            parent: Parent frame.
        """
        bank_frame = ttk.LabelFrame(parent, text="Question Bank")
        bank_frame.pack(fill="x", padx=10, pady=10)

        self.bank_menu = ttk.Combobox(
            bank_frame,
            textvariable=self.bank_var,
            state="readonly"
        )
        self.bank_menu.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        self.bank_menu.bind("<<ComboboxSelected>>", self.on_bank_change)

        load_btn = ttk.Button(bank_frame, text="Load from JSON...", command=self.on_load_json)
        load_btn.pack(side="left", padx=10, pady=10)

    def _build_options(self, parent: ttk.Frame) -> None:
        """
        Build the options section.

        Args:
            parent: Parent frame.
        """
        options_frame = ttk.LabelFrame(parent, text="Options")
        options_frame.pack(fill="x", padx=10, pady=10)

        show_chk = ttk.Checkbutton(
            options_frame,
            text="Show correct answers after quiz",
            variable=self.show_answers_var
        )
        show_chk.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        shuffle_chk = ttk.Checkbutton(
            options_frame,
            text="Shuffle questions",
            variable=self.shuffle_var
        )
        shuffle_chk.grid(row=1, column=0, sticky="w", padx=10, pady=8)

        count_lbl = ttk.Label(options_frame, text="Number of questions:")
        count_lbl.grid(row=0, column=1, sticky="e", padx=(30, 5), pady=8)

        self.count_spin = tk.Spinbox(
            options_frame,
            from_=SPINBOX_MIN_QUESTIONS,
            to=SPINBOX_MAX_QUESTIONS,
            textvariable=self.count_var,
            width=6,
            justify="center"
        )
        self.count_spin.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=8)

        self.bank_size_label = ttk.Label(options_frame, text="Bank contains: 0 questions")
        self.bank_size_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=(30, 5), pady=8)

        for i in range(3):
            options_frame.grid_columnconfigure(i, weight=1)

    def _build_action_buttons(self) -> None:
        """Build the action buttons section."""
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=20)

        start_btn = ttk.Button(action_frame, text="Start Quiz", command=self.on_start)
        start_btn.pack()

    def refresh_banks(self) -> None:
        """Refresh the list of available banks in the combobox."""
        names = self.controller.get_bank_names()
        self.bank_menu["values"] = names

        # Select first bank by default if current selection is invalid
        if names and (self.bank_var.get() not in names):
            self.bank_var.set(names[0])
            self.update_bank_size()

    def on_bank_change(self, event=None) -> None:
        """
        Handle bank selection change.

        Args:
            event: Tkinter event (unused).
        """
        self.update_bank_size()

    def on_load_json(self) -> None:
        """Handle loading a custom question bank from JSON file."""
        path = filedialog.askopenfilename(
            title="Load Question Bank (JSON)",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            questions = load_bank_from_json(path)
            if not questions:
                raise ValueError("No valid questions found in the file.")

            name = self.controller.add_custom_bank(path, questions)
            self.refresh_banks()
            self.bank_var.set(name)
            self.update_bank_size()

            messagebox.showinfo(
                "Loaded",
                f"Loaded {len(questions)} questions from:\n{os.path.basename(path)}"
            )
            logger.info(f"Successfully loaded {len(questions)} questions from {path}")

        except (ValueError, FileNotFoundError, IOError) as e:
            messagebox.showerror("Load Error", f"Failed to load bank:\n{e}")
            logger.error(f"Failed to load bank from {path}: {e}")

    def update_bank_size(self) -> None:
        """Update the displayed bank size and adjust spinbox constraints."""
        name = self.bank_var.get()
        count = len(self.controller.banks.get(name, []))
        self.current_bank_size = count

        self.bank_size_label.config(text=f"Bank contains: {count} questions")

        # Update spinbox max value
        max_value = max(MIN_QUESTION_COUNT, count if count > 0 else MIN_QUESTION_COUNT)
        self.count_spin.config(to=max_value)

        # Adjust current value if it exceeds the new maximum
        current_value = self.count_var.get()
        if current_value > max_value:
            self.count_var.set(max_value)
        elif current_value < MIN_QUESTION_COUNT:
            self.count_var.set(MIN_QUESTION_COUNT)

    def on_start(self) -> None:
        """Handle quiz start button click."""
        bank_name = self.bank_var.get()

        if not bank_name:
            messagebox.showwarning("Select Bank", "Please select a question bank.")
            return

        if bank_name not in self.controller.banks:
            messagebox.showerror("Error", "Selected question bank not found.")
            logger.error(f"Selected bank not found: {bank_name}")
            return

        if self.current_bank_size == 0:
            messagebox.showwarning("Empty Bank", "The selected bank has no questions.")
            return

        try:
            count = int(self.count_var.get())
        except ValueError:
            count = MIN_QUESTION_COUNT
            logger.warning("Invalid question count, using minimum")

        self.controller.start_quiz(
            bank_name=bank_name,
            count=count,
            shuffle=self.shuffle_var.get(),
            show_answers=self.show_answers_var.get()
        )


class QuizFrame(ttk.Frame):
    """Frame for displaying and answering quiz questions."""

    def __init__(self, parent, controller: QuizApp):
        """
        Initialize the quiz frame.

        Args:
            parent: Parent widget.
            controller: Reference to the main QuizApp.
        """
        super().__init__(parent)
        self.controller = controller

        # Answer tracking variables
        self.mcq_var = tk.IntVar(value=NO_SELECTION_VALUE)
        self.mcq_vars: List[tk.BooleanVar] = []
        self.short_var = tk.StringVar(value="")

        # UI components
        self.question_label: Optional[ttk.Label] = None
        self.progress_label: Optional[ttk.Label] = None
        self.content_frame: Optional[ttk.Frame] = None
        self.nav_button: Optional[ttk.Button] = None

        self._build_layout()

    def _build_layout(self) -> None:
        """Build the UI layout for the quiz frame."""
        self._build_header()
        self._build_question_display()
        self._build_content_area()
        self._build_navigation()

    def _build_header