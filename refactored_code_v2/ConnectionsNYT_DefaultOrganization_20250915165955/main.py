import logging
import random
import sys
from datetime import date as dt_date
from typing import Dict, List, Set

from puzzle import Puzzle, generate_daily_puzzle
from utils import today_date_str

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Constants
MAX_MISTAKES = 4
WORDS_PER_GROUP = 4
GRID_COLUMNS = 4
FEEDBACK_SUCCESS = "success"
FEEDBACK_ERROR = "error"
PAGE_TITLE = "Daily 4x4 Connections"
PAGE_ICON = "🧩"

# Attempt to import Streamlit; provide graceful fallback if unavailable
try:
    import streamlit as st  # type: ignore
    HAS_STREAMLIT = True
except ModuleNotFoundError:
    st = None  # type: ignore
    HAS_STREAMLIT = False


def _initialize_session_state_defaults() -> Dict:
    """
    Create default session state values.
    
    Returns:
        Dictionary with default session state keys and values.
    """
    return {
        "puzzle_date": dt_date.today(),
        "puzzle": None,
        "remaining": [],
        "selected": set(),
        "solved": [],
        "mistakes": 0,
        "locked": False,
        "feedback": {"type": "", "msg": ""},
    }


def _ensure_session_state_key(key: str, default_value) -> None:
    """
    Ensure a session state key exists; initialize if missing.
    
    Args:
        key: The session state key name.
        default_value: The value to set if key is missing.
    """
    if key not in st.session_state:
        st.session_state[key] = default_value


if HAS_STREAMLIT:
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")

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
            kind: The feedback type ("success" or "error").
            msg: The feedback message text.
        """
        st.session_state.feedback = {"type": kind, "msg": msg}

    def init_state() -> None:
        """
        Initialize Streamlit session state for a new visit or roll over at midnight.
        
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
        
        # Recover missing keys (e.g., after Streamlit state clear)
        defaults = _initialize_session_state_defaults()
        for key, default_value in defaults.items():
            _ensure_session_state_key(key, default_value)

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

    def submit_guess() -> None:
        """
        Check the current selection, update solved groups or mistakes, and provide feedback.
        
        Validates that exactly 4 words are selected, checks if they form a valid group,
        and updates game state accordingly.
        """
        if st.session_state.locked:
            return
        
        selected = st.session_state.selected
        
        # Validate selection count
        if len(selected) != WORDS_PER_GROUP:
            set_feedback(FEEDBACK_ERROR, f"Select exactly {WORDS_PER_GROUP} words before submitting.")
            return
        
        puzzle: Puzzle = st.session_state.puzzle
        
        # Determine which categories the selected words belong to
        category_indices = {puzzle.word_to_category[w] for w in selected}
        
        if len(category_indices) == 1:
            # Correct guess: all words belong to the same category
            _handle_correct_guess(puzzle, category_indices, selected)
        else:
            # Incorrect guess: words belong to different categories
            _handle_incorrect_guess()

    def _handle_correct_guess(puzzle: Puzzle, category_indices: Set[int], selected: Set[str]) -> None:
        """
        Handle a correct guess by updating solved groups and checking win condition.
        
        Args:
            puzzle: The current puzzle object.
            category_indices: Set containing the single category index.
            selected: Set of selected words.
        """
        category_idx = next(iter(category_indices))
        category = puzzle.categories[category_idx]
        
        # Remove solved words from remaining
        st.session_state.remaining = [w for w in st.session_state.remaining if w not in selected]
        
        # Record solved category
        st.session_state.solved.append({
            "name": category.name,
            "words": list(category.words),
            "difficulty": category.difficulty,
            "color": category.color,
        })
        
        # Clear selection
        st.session_state.selected = set()
        set_feedback(FEEDBACK_SUCCESS, f"Correct! {category.name} ({category.difficulty}).")
        
        # Check win condition
        if len(st.session_state.remaining) == 0:
            st.session_state.locked = True
            set_feedback(FEEDBACK_SUCCESS, "Puzzle complete! Great job.")

    def _handle_incorrect_guess() -> None:
        """
        Handle an incorrect guess by incrementing mistakes and checking loss condition.
        """
        st.session_state.mistakes += 1
        remaining_tries = max(0, MAX_MISTAKES - st.session_state.mistakes)
        
        if st.session_state.mistakes >= MAX_MISTAKES:
            st.session_state.locked = True
            set_feedback(FEEDBACK_ERROR, f"Incorrect. You've reached the maximum mistakes ({MAX_MISTAKES}). Game over.")
        else:
            set_feedback(FEEDBACK_ERROR, f"Incorrect. Try again. Mistakes left: {remaining_tries}")
        
        # Clear selection to prompt rethinking
        st.session_state.selected = set()

    def shuffle_remaining() -> None:
        """Shuffle the remaining words to change layout."""
        if st.session_state.locked:
            return
        random.shuffle(st.session_state.remaining)

    def render_header() -> None:
        """Render the app title and meta information."""
        st.title(f"{PAGE_ICON} {PAGE_TITLE}")
        st.caption(
            f"Date: {today_date_str()} — Group the 16 words into four categories of four."
        )

    def render_solved() -> None:
        """Display solved groups with category name and color-coded difficulty."""
        if not st.session_state.solved:
            return
        
        st.subheader("Solved Groups")
        for group in st.session_state.solved:
            background_color = group["color"]
            words_display = ", ".join(w.title() for w in group["words"])
            st.markdown(
                f'<div style="background:{background_color};padding:10px;border-radius:6px;color:white">'
                f'<strong>{group["name"]}</strong> — {group["difficulty"].title()}<br/>{words_display}'
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

    def render_grid() -> None:
        """
        Render the word grid with selectable buttons.
        
        Dynamically adjusts grid size based on remaining words (4x4 initially,
        fewer rows as groups are solved).
        """
        st.subheader("Words")
        remaining = st.session_state.remaining
        selected = st.session_state.selected
        locked = st.session_state.locked
        
        # Calculate grid dimensions
        word_count = len(remaining)
        row_count = (word_count + GRID_COLUMNS - 1) // GRID_COLUMNS
        
        word_iterator = iter(remaining)
        for _ in range(row_count):
            columns = st.columns(GRID_COLUMNS)
            for column in columns:
                try:
                    word = next(word_iterator)
                except StopIteration:
                    break
                
                is_selected = word in selected
                button_label = word.title()
                
                # Visually mark selected words
                if is_selected:
                    button_label = f"• {button_label} •"
                
                column.button(
                    button_label,
                    key=f"btn_{word}",
                    on_click=toggle_word,
                    args=(word,),
                    use_container_width=True,
                    disabled=locked,
                )
        
        # Submit button enabled only when exactly 4 words selected and game not locked
        submit_enabled = len(selected) == WORDS_PER_GROUP and not locked
        st.button(
            "Submit Guess",
            on_click=submit_guess,
            disabled=not submit_enabled,
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
        """Main Streamlit application entry point."""
        init_state()
        render_header()
        render_solved()
        render_status()
        render_grid()
        render_footer()

else:
    def _display_grid_cli(remaining: List[str]) -> None:
        """
        Display the word grid in CLI format.
        
        Args:
            remaining: List of remaining words to display.
        """
        word_count = len(remaining)
        row_count = (word_count + GRID_COLUMNS - 1) // GRID_COLUMNS
        logger.info("\nWords:")
        
        word_iterator = iter(remaining)
        for _ in range(row_count):
            row_words = []
            for _ in range(GRID_COLUMNS):
                try:
                    row_words.append(next(word_iterator).title())
                except StopIteration:
                    break
            logger.info("  " + " | ".join(f"{w:>12}" for w in row_words))

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
        Validate that selected words are valid and in the remaining list.
        
        Args:
            selected_words: List of selected words.
            remaining: List of remaining words in the puzzle.
            
        Returns:
            True if all selected words are valid, False otherwise.
        """
        if len(selected_words) != WORDS_PER_GROUP:
            logger.info(f"Please enter exactly {WORDS_PER_GROUP} words separated by commas.")
            return False
        
        if any(word not in remaining for word in selected_words):
            logger.info("All selected words must be from the remaining grid. Check spelling.")
            return False
        
        return True

    def _process_guess(selected_words: List[str], puzzle: Puzzle, remaining: List[str]) -> tuple[bool, List[str]]:
        """
        Process a guess and return whether it was correct and updated remaining words.
        
        Args:
            selected_words: List of selected words.
            puzzle: The puzzle object.
            remaining: List of remaining words.
            
        Returns:
            Tuple of (is_correct, updated_remaining_list).
        """
        category_indices = {puzzle.word_to_category[w] for w in selected_words}
        
        if len(category_indices) == 1:
            # Correct guess
            category_idx = next(iter(category_indices))
            category = puzzle.categories[category_idx]
            updated_remaining = [w for w in remaining if w not in selected_words]
            logger.info(f"Correct! {category.name} ({category.difficulty}).")
            return True, updated_remaining
        else:
            # Incorrect guess
            logger.info(f"Incorrect. Try again. Mistakes left: {max(0, MAX_MISTAKES - 1)}")
            return False, remaining

    def main_cli() -> int:
        """
        Console fallback game loop if Streamlit isn't installed.
        
        Returns:
            Exit code (0 for success).
        """
        logger.info(f"{PAGE_ICON} Daily 4x4 Connections (CLI fallback)")
        logger.info(f"Date: {today_date_str()}")
        logger.info("Tip: Install Streamlit for the full web experience: pip install streamlit")
        
        puzzle = generate_daily_puzzle(dt_date.today())
        remaining = list(puzzle.words)
        mistakes = 0

        while True:
            # Check win condition
            if len(remaining) == 0:
                logger.info("\nPuzzle complete! Great job.")
                break
            
            # Check loss condition
            if mistakes >= MAX_MISTAKES:
                logger.info(f"\nIncorrect. You've reached the maximum mistakes ({MAX_MISTAKES}). Game over.")
                logger.info("\nSolution categories:")
                for category in puzzle.categories:
                    words_str = ", ".join(w.title() for w in category.words)
                    logger.info(f"- {category.name} ({category.difficulty