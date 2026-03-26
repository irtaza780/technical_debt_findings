import logging
from datetime import date as dt_date
from typing import List, Set, Dict

import random
import streamlit as st

from puzzle import generate_daily_puzzle, Puzzle
from utils import today_date_str

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page early (should be the first Streamlit call)
st.set_page_config(page_title="Daily 4x4 Connections", page_icon="🧩", layout="centered")

# Constants
MAX_MISTAKES = 4
GRID_COLUMNS = 4
FEEDBACK_SUCCESS = "success"
FEEDBACK_ERROR = "error"
BUTTON_PREFIX = "btn_"
SELECTION_MARKER = "• {} •"


# ---------- Session state management ----------

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
    logger.info(f"Daily puzzle reset for {date_obj}")


def set_feedback(kind: str, msg: str) -> None:
    """
    Store a feedback message to present on the next render.
    
    Args:
        kind: The feedback type ("success" or "error").
        msg: The feedback message text.
    """
    st.session_state.feedback = {"type": kind, "msg": msg}


def _ensure_state_key(key: str, default_value) -> None:
    """
    Ensure a session state key exists, initializing it if missing.
    
    Args:
        key: The session state key name.
        default_value: The default value if the key is missing.
    """
    if key not in st.session_state:
        st.session_state[key] = default_value


def init_state() -> None:
    """
    Initialize Streamlit session state for a new visit or roll over at midnight.
    
    Handles:
    - First-time initialization with today's puzzle
    - Daily rollover when the date changes
    - Recovery of missing state keys after Streamlit resets
    """
    today = dt_date.today()
    
    # First visit or date has changed
    if "puzzle_date" not in st.session_state or st.session_state.puzzle_date != today:
        reset_daily(today)
        return
    
    # Ensure all required keys exist
    _ensure_state_key("puzzle", generate_daily_puzzle(st.session_state.puzzle_date))
    _ensure_state_key("remaining", list(st.session_state.puzzle.words))
    _ensure_state_key("selected", set())
    _ensure_state_key("solved", [])
    _ensure_state_key("mistakes", 0)
    _ensure_state_key("locked", False)
    _ensure_state_key("feedback", {"type": "", "msg": ""})


# ---------- Game actions ----------

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


def _check_guess_validity(selected: Set[str]) -> tuple[bool, str]:
    """
    Validate that exactly four words are selected.
    
    Args:
        selected: The set of selected words.
    
    Returns:
        A tuple of (is_valid, error_message).
    """
    if len(selected) != 4:
        return False, "Select exactly four words before submitting."
    return True, ""


def _process_correct_guess(puzzle: Puzzle, selected: Set[str]) -> None:
    """
    Handle a correct guess by removing the group and recording it.
    
    Args:
        puzzle: The current puzzle object.
        selected: The set of selected words that form a correct group.
    """
    # Get the category index from any word in the selection
    category_idx = puzzle.word_to_category[next(iter(selected))]
    category = puzzle.categories[category_idx]
    
    # Remove solved words from remaining
    st.session_state.remaining = [
        w for w in st.session_state.remaining if w not in selected
    ]
    
    # Record solved category
    st.session_state.solved.append({
        "name": category.name,
        "words": list(category.words),
        "difficulty": category.difficulty,
        "color": category.color,
    })
    
    # Clear selection
    st.session_state.selected = set()
    
    # Provide feedback
    set_feedback(FEEDBACK_SUCCESS, f"Correct! {category.name} ({category.difficulty}).")
    logger.info(f"Correct guess: {category.name}")


def _process_incorrect_guess() -> None:
    """
    Handle an incorrect guess by incrementing mistakes and providing feedback.
    """
    st.session_state.mistakes += 1
    st.session_state.selected = set()
    
    remaining_tries = max(0, MAX_MISTAKES - st.session_state.mistakes)
    
    if st.session_state.mistakes >= MAX_MISTAKES:
        st.session_state.locked = True
        set_feedback(
            FEEDBACK_ERROR,
            f"Incorrect. You've reached the maximum mistakes ({MAX_MISTAKES}). Game over."
        )
        logger.info("Game over: maximum mistakes reached")
    else:
        set_feedback(
            FEEDBACK_ERROR,
            f"Incorrect. Try again. Mistakes left: {remaining_tries}"
        )
        logger.info(f"Incorrect guess. Mistakes: {st.session_state.mistakes}/{MAX_MISTAKES}")


def _check_win_condition() -> None:
    """
    Check if the puzzle is complete and lock the game if so.
    """
    if len(st.session_state.remaining) == 0:
        st.session_state.locked = True
        set_feedback(FEEDBACK_SUCCESS, "Puzzle complete! Great job.")
        logger.info("Puzzle completed successfully")


def submit_guess() -> None:
    """
    Check the current selection, update solved groups or mistakes, and provide feedback.
    
    Validates the selection, checks if it matches a category, and updates game state accordingly.
    """
    if st.session_state.locked:
        return
    
    selected = st.session_state.selected
    
    # Validate selection
    is_valid, error_msg = _check_guess_validity(selected)
    if not is_valid:
        set_feedback(FEEDBACK_ERROR, error_msg)
        return
    
    puzzle: Puzzle = st.session_state.puzzle
    
    # Check if all selected words belong to the same category
    category_indices = {puzzle.word_to_category[word] for word in selected}
    
    if len(category_indices) == 1:
        # Correct guess
        _process_correct_guess(puzzle, selected)
        _check_win_condition()
    else:
        # Incorrect guess
        _process_incorrect_guess()


def shuffle_remaining() -> None:
    """Shuffle the remaining words to change their layout."""
    if st.session_state.locked:
        return
    random.shuffle(st.session_state.remaining)
    logger.info("Words shuffled")


# ---------- UI helpers ----------

def render_header() -> None:
    """Render the app title and meta information."""
    st.title("🧩 Daily 4x4 Connections")
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
        words_display = ", ".join(word.title() for word in group["words"])
        
        html_content = (
            f'<div style="background:{background_color};padding:10px;border-radius:6px;color:white">'
            f'<strong>{group["name"]}</strong> — {group["difficulty"].title()}<br/>'
            f'{words_display}'
            f"</div>"
        )
        st.markdown(html_content, unsafe_allow_html=True)


def render_status() -> None:
    """Show mistakes remaining, shuffle control, and feedback messages."""
    mistakes_left = max(0, MAX_MISTAKES - st.session_state.mistakes)
    
    cols = st.columns([1, 1, 2])
    with cols[0]:
        st.metric("Mistakes Left", mistakes_left)
    with cols[1]:
        st.button(
            "Shuffle",
            on_click=shuffle_remaining,
            disabled=st.session_state.locked
        )
    with cols[2]:
        st.caption(
            "Hint: Select four words that fit the same hidden category, then click Submit."
        )
    
    # Display feedback messages
    feedback = st.session_state.feedback
    if feedback["type"] == FEEDBACK_SUCCESS:
        st.success(feedback["msg"])
    elif feedback["type"] == FEEDBACK_ERROR:
        st.error(feedback["msg"])


def _render_word_button(word: str, is_selected: bool, is_locked: bool, column) -> None:
    """
    Render a single word button in the given column.
    
    Args:
        word: The word to display.
        is_selected: Whether the word is currently selected.
        is_locked: Whether the game is locked.
        column: The Streamlit column to render in.
    """
    label = word.title()
    if is_selected:
        label = SELECTION_MARKER.format(label)
    
    column.button(
        label,
        key=f"{BUTTON_PREFIX}{word}",
        on_click=toggle_word,
        args=(word,),
        use_container_width=True,
        disabled=is_locked,
    )


def render_grid() -> None:
    """
    Render the 4x4 word grid with selectable buttons.
    
    Dynamically adjusts the number of rows based on remaining words.
    """
    st.subheader("Words")
    remaining = st.session_state.remaining
    selected = st.session_state.selected
    is_locked = st.session_state.locked
    
    # Calculate number of rows needed (4 columns per row)
    num_rows = (len(remaining) + GRID_COLUMNS - 1) // GRID_COLUMNS
    word_iterator = iter(remaining)
    
    for _ in range(num_rows):
        columns = st.columns(GRID_COLUMNS)
        for column in columns:
            try:
                word = next(word_iterator)
            except StopIteration:
                break
            
            is_selected = word in selected
            _render_word_button(word, is_selected, is_locked, column)
    
    # Submit button (enabled only when exactly 4 are selected and game not locked)
    st.button(
        "Submit Guess",
        on_click=submit_guess,
        disabled=(len(selected) != GRID_COLUMNS or is_locked),
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


# ---------- Main app ----------

def main() -> None:
    """Initialize and render the complete game interface."""
    init_state()
    render_header()
    render_solved()
    render_status()
    render_grid()
    render_footer()


if __name__ == "__main__":
    main()