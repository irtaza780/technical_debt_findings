import logging
from datetime import date as dt_date
from typing import List, Set, Dict
import random
import sys

from puzzle import generate_daily_puzzle, Puzzle
from utils import today_date_str

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
MAX_MISTAKES = 4
WORDS_PER_GROUP = 4
GRID_COLUMNS = 4
FEEDBACK_SUCCESS = "success"
FEEDBACK_ERROR = "error"
MISTAKES_LEFT_MESSAGE = "Mistakes left: {}"
CORRECT_MESSAGE = "Correct! {} ({})."
INCORRECT_MESSAGE = "Incorrect. Try again. Mistakes left: {}."
MAX_MISTAKES_MESSAGE = "Incorrect. You've reached the maximum mistakes ({}). Game over."
PUZZLE_COMPLETE_MESSAGE = "Puzzle complete! Great job."
SELECT_FOUR_MESSAGE = "Select exactly four words before submitting."
INVALID_SELECTION_MESSAGE = "All selected words must be from the remaining grid. Check spelling."
ENTER_FOUR_WORDS_MESSAGE = "Please enter exactly four words separated by commas."

# Attempt to import Streamlit; provide graceful fallback if unavailable
try:
    import streamlit as st  # type: ignore
    HAS_STREAMLIT = True
except ModuleNotFoundError:
    st = None  # type: ignore
    HAS_STREAMLIT = False


# ---------- Streamlit implementation ----------
if HAS_STREAMLIT:
    st.set_page_config(page_title="Daily 4x4 Connections", page_icon="🧩", layout="centered")

    def reset_daily(date_obj: dt_date) -> None:
        """
        Reset session state for a given date and regenerate the daily puzzle.
        
        Args:
            date_obj: The date for which to generate the puzzle.
        """
        st.session_state.puzzle_date = date_obj
        st.session_state.puzzle = generate_daily_puzzle(date_obj)
        st.session_state.remaining = list(st.session_state.puzzle.words)
        st.session_state.selected = set()
        st.session_state.solved = []
        st.session_state.mistakes = 0
        st.session_state.locked = False
        st.session_state.feedback = {"type": "", "msg": ""}

    def set_feedback(kind: str, msg: str) -> None:
        """
        Store a feedback message to present on the next render.
        
        Args:
            kind: Type of feedback ("success" or "error").
            msg: The feedback message text.
        """
        st.session_state.feedback = {"type": kind, "msg": msg}

    def _initialize_missing_state_keys() -> None:
        """Initialize any missing session state keys with default values."""
        defaults = {
            "puzzle": lambda: generate_daily_puzzle(st.session_state.puzzle_date),
            "remaining": lambda: list(st.session_state.puzzle.words),
            "selected": set,
            "solved": list,
            "mistakes": int,
            "locked": lambda: False,
            "feedback": lambda: {"type": "", "msg": ""},
        }
        for key, default_factory in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_factory() if callable(default_factory) else default_factory()

    def init_state() -> None:
        """
        Initialize Streamlit session state for a new visit and handle daily rollover.
        
        Handles:
        - First-time initialization with today's puzzle
        - Rollover to new puzzle when date changes
        - Recovery of missing state keys
        """
        today = dt_date.today()
        
        # First visit: initialize with today's puzzle
        if "puzzle_date" not in st.session_state:
            reset_daily(today)
            return
        
        # Date has changed: roll to new daily puzzle
        if st.session_state.puzzle_date != today:
            reset_daily(today)
            return
        
        # Recover any missing keys
        _initialize_missing_state_keys()

    def toggle_word(word: str) -> None:
        """
        Toggle selection of a word when its button is clicked.
        
        Args:
            word: The word to toggle.
        """
        if st.session_state.locked:
            return
        if word not in st.session_state.remaining:
            return
        
        if word in st.session_state.selected:
            st.session_state.selected.remove(word)
        else:
            st.session_state.selected.add(word)

    def _check_guess_correctness(selected: Set[str], puzzle: Puzzle) -> bool:
        """
        Check if selected words belong to the same category.
        
        Args:
            selected: Set of selected words.
            puzzle: The current puzzle.
            
        Returns:
            True if all words belong to the same category, False otherwise.
        """
        cat_idxs = {puzzle.word_to_category[w] for w in selected}
        return len(cat_idxs) == 1

    def _handle_correct_guess(selected: Set[str], puzzle: Puzzle) -> None:
        """
        Process a correct guess: remove words, record category, check win condition.
        
        Args:
            selected: Set of correctly guessed words.
            puzzle: The current puzzle.
        """
        cat_idx = next(iter({puzzle.word_to_category[w] for w in selected}))
        cat = puzzle.categories[cat_idx]
        
        # Remove solved words from remaining
        st.session_state.remaining = [w for w in st.session_state.remaining if w not in selected]
        
        # Record solved category
        st.session_state.solved.append({
            "name": cat.name,
            "words": list(cat.words),
            "difficulty": cat.difficulty,
            "color": cat.color,
        })
        
        # Clear selection and provide feedback
        st.session_state.selected = set()
        set_feedback(FEEDBACK_SUCCESS, CORRECT_MESSAGE.format(cat.name, cat.difficulty))
        
        # Check win condition
        if len(st.session_state.remaining) == 0:
            st.session_state.locked = True
            set_feedback(FEEDBACK_SUCCESS, PUZZLE_COMPLETE_MESSAGE)

    def _handle_incorrect_guess() -> None:
        """Process an incorrect guess: increment mistakes, check loss condition."""
        st.session_state.mistakes += 1
        remaining_tries = max(0, MAX_MISTAKES - st.session_state.mistakes)
        
        if st.session_state.mistakes >= MAX_MISTAKES:
            st.session_state.locked = True
            set_feedback(FEEDBACK_ERROR, MAX_MISTAKES_MESSAGE.format(MAX_MISTAKES))
        else:
            set_feedback(FEEDBACK_ERROR, INCORRECT_MESSAGE.format(remaining_tries))
        
        # Clear selection to prompt rethinking
        st.session_state.selected = set()

    def submit_guess() -> None:
        """
        Check the current selection, update solved groups or mistakes, and provide feedback.
        """
        if st.session_state.locked:
            return
        
        selected = st.session_state.selected
        
        # Validate selection count
        if len(selected) != WORDS_PER_GROUP:
            set_feedback(FEEDBACK_ERROR, SELECT_FOUR_MESSAGE)
            return
        
        puzzle: Puzzle = st.session_state.puzzle
        
        # Check correctness and handle accordingly
        if _check_guess_correctness(selected, puzzle):
            _handle_correct_guess(selected, puzzle)
        else:
            _handle_incorrect_guess()

    def shuffle_remaining() -> None:
        """Shuffle the remaining words to change layout."""
        if st.session_state.locked:
            return
        random.shuffle(st.session_state.remaining)

    def render_header() -> None:
        """Render the app title and meta information."""
        st.title("🧩 Daily 4x4 Connections")
        st.caption(f"Date: {today_date_str()} — Group the 16 words into four categories of four.")

    def render_solved() -> None:
        """Display solved groups with category name and color-coded difficulty."""
        if not st.session_state.solved:
            return
        
        st.subheader("Solved Groups")
        for group in st.session_state.solved:
            bg_color = group["color"]
            words_str = ", ".join(w.title() for w in group["words"])
            st.markdown(
                f'<div style="background:{bg_color};padding:10px;border-radius:6px;color:white">'
                f'<strong>{group["name"]}</strong> — {group["difficulty"].title()}<br/>{words_str}'
                f"</div>",
                unsafe_allow_html=True,
            )

    def render_status() -> None:
        """Show mistakes info, controls, and feedback messages."""
        mistakes_left = max(0, MAX_MISTAKES - st.session_state.mistakes)
        cols = st.columns([1, 1, 2])
        
        with cols[0]:
            st.metric("Mistakes Left", mistakes_left)
        with cols[1]:
            st.button("Shuffle", on_click=shuffle_remaining, disabled=st.session_state.locked)
        with cols[2]:
            st.caption("Hint: Select four words that fit the same hidden category, then click Submit.")
        
        # Display feedback messages
        feedback = st.session_state.feedback
        if feedback["type"] == FEEDBACK_SUCCESS:
            st.success(feedback["msg"])
        elif feedback["type"] == FEEDBACK_ERROR:
            st.error(feedback["msg"])

    def _render_word_grid_row(word_iter, cols) -> None:
        """
        Render a single row of the word grid.
        
        Args:
            word_iter: Iterator over remaining words.
            cols: Streamlit columns to populate.
        """
        selected = st.session_state.selected
        locked = st.session_state.locked
        
        for col in cols:
            try:
                word = next(word_iter)
            except StopIteration:
                break
            
            is_selected = word in selected
            label = word.title()
            
            # Visually mark selected words
            if is_selected:
                label = f"• {label} •"
            
            col.button(
                label,
                key=f"btn_{word}",
                on_click=toggle_word,
                args=(word,),
                use_container_width=True,
                disabled=locked,
            )

    def render_grid() -> None:
        """Render the 4x4 word grid with selectable buttons."""
        st.subheader("Words")
        remaining = st.session_state.remaining
        selected = st.session_state.selected
        locked = st.session_state.locked
        
        # Calculate grid dimensions based on remaining words
        num_words = len(remaining)
        num_rows = (num_words + GRID_COLUMNS - 1) // GRID_COLUMNS
        word_iter = iter(remaining)
        
        # Render each row
        for _ in range(num_rows):
            cols = st.columns(GRID_COLUMNS)
            _render_word_grid_row(word_iter, cols)
        
        # Submit button (enabled only when exactly 4 are selected and game not locked)
        st.button(
            "Submit Guess",
            on_click=submit_guess,
            disabled=(len(selected) != WORDS_PER_GROUP or locked),
            type="primary",
        )

    def render_footer() -> None:
        """Render help section with game instructions."""
        with st.expander("How to play"):
            st.write(
                "- Tap words to select exactly four that share a common category.\n"
                "- Click Submit Guess to check. Correct groups disappear and reveal their category.\n"
                f"- You can make up to {MAX_MISTAKES} mistakes.\n"
                "- Click Shuffle to rearrange the remaining words.\n"
                "- A new puzzle is generated daily."
            )

    def main() -> None:
        """Main Streamlit app entry point."""
        init_state()
        render_header()
        render_solved()
        render_status()
        render_grid()
        render_footer()

# ---------- CLI fallback implementation (no Streamlit) ----------
else:
    def _display_cli_grid(remaining: List[str]) -> None:
        """
        Display the word grid in CLI format.
        
        Args:
            remaining: List of remaining words to display.
        """
        num_words = len(remaining)
        num_rows = (num_words + GRID_COLUMNS - 1) // GRID_COLUMNS
        logger.info("Words:")
        
        word_iter = iter(remaining)
        for _ in range(num_rows):
            row = []
            for _ in range(GRID_COLUMNS):
                try:
                    row.append(next(word_iter).title())
                except StopIteration:
                    break
            logger.info("  " + " | ".join(f"{w:>12}" for w in row))

    def _parse_user_input(user_input: str) -> List[str]:
        """
        Parse comma-separated user input into a list of words.
        
        Args:
            user_input: Raw user input string.
            
        Returns:
            List of parsed words (lowercased).
        """
        parts = [p.strip().lower() for p in user_input.split(",") if p.strip()]
        return parts

    def _validate_selection(selected_words: List[str], remaining: List[str]) -> bool:
        """
        Validate that selected words are in the remaining grid.
        
        Args:
            selected_words: Words selected by user.
            remaining: Words currently in the grid.
            
        Returns:
            True if all selected words are valid, False otherwise.
        """
        return all(word in remaining for word in selected_words)

    def _handle_cli_correct_guess(selected_words: List[str], puzzle: Puzzle, remaining: List[str]) -> List[str]:
        """
        Process a correct CLI guess.
        
        Args:
            selected_words: Correctly guessed words.
            puzzle: The current puzzle.
            remaining: Current remaining words.
            
        Returns:
            Updated remaining words list.
        """
        cat_idx = next(iter({puzzle.word_to_category[w] for w in selected_words}))
        cat = puzzle.categories[cat_idx]
        logger.info(CORRECT_MESSAGE.format(cat.name, cat.difficulty))
        return [w for w in remaining if w not in selected_words]

    def _reveal_solution(puzzle: Puzzle) -> None:
        """
        Reveal all remaining categories (game over).
        
        Args:
            puzzle: The current puzzle.
        """
        logger.info("\nSolution categories:")
        for cat in puzzle.categories:
            words_str = ", ".join(w.title() for w in cat.words)
            logger.info(f"- {cat.name} ({cat.difficulty}): {words_str}")

    def main_cli() -> int:
        """
        Console fallback game loop if Streamlit isn't installed.
        
        Returns:
            Exit code (0 for success).
        """
        logger.info("🧩 Daily 4x4 Connections (CLI fallback)")
        logger.info(f"Date: {today_date_str()}")
        logger.info("Tip: Install Streamlit for the full web experience: pip install streamlit")
        
        puzzle = generate_daily_puzzle(dt_date.today())
        remaining = list(puzzle.words)
        mistakes = 0

        while True:
            # Check win condition
            if len(remaining) == 0:
                logger.info("\n" + PUZZLE_COMPLETE_MESSAGE)
                break
            
            # Check loss condition
            if mistakes >= MAX_MISTAKES:
                logger.info("\n" + MAX_MISTAKES_MESSAGE.format(MAX_MISTAKES))
                _reveal_solution(puzzle)
                break

            _display_cli_grid(