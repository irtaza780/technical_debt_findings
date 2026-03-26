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
WORDS_PER_ROW = 4
GRID_PADDING = "10px"
GRID_BORDER_RADIUS = "6px"
SELECTION_MARKER = "•"
FEEDBACK_TYPE_SUCCESS = "success"
FEEDBACK_TYPE_ERROR = "error"


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


def set_feedback(feedback_type: str, message: str) -> None:
    """
    Store a feedback message to present on the next render.

    Args:
        feedback_type: Type of feedback ("success" or "error").
        message: The feedback message to display.
    """
    st.session_state.feedback = {"type": feedback_type, "msg": message}


def _initialize_missing_state_keys() -> None:
    """Initialize any missing session state keys with default values."""
    if "puzzle" not in st.session_state:
        st.session_state.puzzle = generate_daily_puzzle(st.session_state.puzzle_date)
    if "remaining" not in st.session_state:
        st.session_state.remaining: List[str] = list(st.session_state.puzzle.words)
    if "selected" not in st.session_state:
        st.session_state.selected: Set[str] = set()
    if "solved" not in st.session_state:
        st.session_state.solved: List[Dict] = []
    if "mistakes" not in st.session_state:
        st.session_state.mistakes: int = 0
    if "locked" not in st.session_state:
        st.session_state.locked: bool = False
    if "feedback" not in st.session_state:
        st.session_state.feedback: Dict[str, str] = {"type": "", "msg": ""}


def init_state() -> None:
    """
    Initialize Streamlit session state for a new visit or roll over at midnight.

    Handles:
    - First-time initialization
    - Daily puzzle rollover when date changes
    - Recovery of missing state keys
    """
    today = dt_date.today()

    if "puzzle_date" not in st.session_state:
        reset_daily(today)
        return

    # Roll to new daily puzzle if a day has passed
    if st.session_state.puzzle_date != today:
        reset_daily(today)
        return

    # Initialize any missing keys
    _initialize_missing_state_keys()


def toggle_word(word: str) -> None:
    """
    Toggle selection of a word when its button is clicked.

    Args:
        word: The word to toggle selection for.
    """
    if st.session_state.locked:
        return
    if word not in st.session_state.remaining:
        return

    if word in st.session_state.selected:
        st.session_state.selected.remove(word)
    else:
        st.session_state.selected.add(word)


def _is_correct_guess(selected_words: Set[str], puzzle: Puzzle) -> bool:
    """
    Check if the selected words belong to the same category.

    Args:
        selected_words: Set of selected words.
        puzzle: The puzzle object containing category mappings.

    Returns:
        True if all selected words belong to the same category, False otherwise.
    """
    category_indices = {puzzle.word_to_category[word] for word in selected_words}
    return len(category_indices) == 1


def _record_solved_group(category_index: int, puzzle: Puzzle) -> None:
    """
    Record a solved category group in session state.

    Args:
        category_index: Index of the solved category.
        puzzle: The puzzle object containing category information.
    """
    category = puzzle.categories[category_index]
    st.session_state.solved.append({
        "name": category.name,
        "words": list(category.words),
        "difficulty": category.difficulty,
        "color": category.color,
    })


def _handle_correct_guess(selected_words: Set[str], puzzle: Puzzle) -> None:
    """
    Handle a correct guess by removing words, recording the group, and checking win condition.

    Args:
        selected_words: The selected words that form a correct group.
        puzzle: The puzzle object.
    """
    category_index = next(iter({puzzle.word_to_category[w] for w in selected_words}))
    category = puzzle.categories[category_index]

    # Remove solved words from remaining
    st.session_state.remaining = [
        w for w in st.session_state.remaining if w not in selected_words
    ]

    # Record the solved group
    _record_solved_group(category_index, puzzle)

    # Clear selection
    st.session_state.selected = set()

    set_feedback(FEEDBACK_TYPE_SUCCESS, f"Correct! {category.name} ({category.difficulty}).")

    # Check win condition
    if len(st.session_state.remaining) == 0:
        st.session_state.locked = True
        set_feedback(FEEDBACK_TYPE_SUCCESS, "Puzzle complete! Great job.")
        logger.info("Puzzle completed successfully")


def _handle_incorrect_guess() -> None:
    """Handle an incorrect guess by incrementing mistakes and providing feedback."""
    st.session_state.mistakes += 1
    remaining_tries = max(0, MAX_MISTAKES - st.session_state.mistakes)

    if st.session_state.mistakes >= MAX_MISTAKES:
        st.session_state.locked = True
        set_feedback(
            FEEDBACK_TYPE_ERROR,
            f"Incorrect. You've reached the maximum mistakes ({MAX_MISTAKES}). Game over."
        )
        logger.info("Game over: maximum mistakes reached")
    else:
        set_feedback(
            FEEDBACK_TYPE_ERROR,
            f"Incorrect. Try again. Mistakes left: {remaining_tries}"
        )

    # Clear selection after wrong guess
    st.session_state.selected = set()


def submit_guess() -> None:
    """
    Check the current selection, update solved groups or mistakes, and provide feedback.

    Validates that exactly 4 words are selected, checks if they form a valid group,
    and updates game state accordingly.
    """
    if st.session_state.locked:
        return

    selected = st.session_state.selected

    if len(selected) != MAX_MISTAKES:
        set_feedback(FEEDBACK_TYPE_ERROR, "Select exactly four words before submitting.")
        return

    puzzle: Puzzle = st.session_state.puzzle

    if _is_correct_guess(selected, puzzle):
        _handle_correct_guess(selected, puzzle)
    else:
        _handle_incorrect_guess()


def shuffle_remaining() -> None:
    """Shuffle the remaining words to change their layout."""
    if st.session_state.locked:
        return
    random.shuffle(st.session_state.remaining)
    logger.info("Words shuffled")


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
        words_string = ", ".join(word.title() for word in group["words"])
        html_content = (
            f'<div style="background:{background_color};padding:{GRID_PADDING};'
            f'border-radius:{GRID_BORDER_RADIUS};color:white">'
            f'<strong>{group["name"]}</strong> — {group["difficulty"].title()}<br/>'
            f'{words_string}</div>'
        )
        st.markdown(html_content, unsafe_allow_html=True)


def render_status() -> None:
    """Display mistakes remaining, shuffle button, hint, and feedback messages."""
    mistakes_left = max(0, MAX_MISTAKES - st.session_state.mistakes)
    columns = st.columns([1, 1, 2])

    with columns[0]:
        st.metric("Mistakes Left", mistakes_left)

    with columns[1]:
        st.button(
            "Shuffle",
            on_click=shuffle_remaining,
            disabled=st.session_state.locked
        )

    with columns[2]:
        st.caption(
            "Hint: Select four words that fit the same hidden category, then click Submit."
        )

    # Display feedback messages
    feedback = st.session_state.feedback
    if feedback["type"] == FEEDBACK_TYPE_SUCCESS:
        st.success(feedback["msg"])
    elif feedback["type"] == FEEDBACK_TYPE_ERROR:
        st.error(feedback["msg"])


def _render_word_button(word: str, is_selected: bool, is_locked: bool, column) -> None:
    """
    Render a single word button in the given column.

    Args:
        word: The word to display.
        is_selected: Whether the word is currently selected.
        is_locked: Whether the game is locked.
        column: The Streamlit column to render the button in.
    """
    label = word.title()
    if is_selected:
        label = f"{SELECTION_MARKER} {label} {SELECTION_MARKER}"

    column.button(
        label,
        key=f"btn_{word}",
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

    # Calculate number of rows needed for remaining words
    num_words = len(remaining)
    num_rows = (num_words + WORDS_PER_ROW - 1) // WORDS_PER_ROW

    word_iterator = iter(remaining)
    for _ in range(num_rows):
        columns = st.columns(WORDS_PER_ROW)
        for column in columns:
            try:
                word = next(word_iterator)
            except StopIteration:
                break

            is_selected = word in selected
            _render_word_button(word, is_selected, is_locked, column)

    # Submit button enabled only when exactly 4 words selected and game not locked
    st.button(
        "Submit Guess",
        on_click=submit_guess,
        disabled=(len(selected) != MAX_MISTAKES or is_locked),
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
    """Main application entry point. Initialize state and render all UI components."""
    init_state()
    render_header()
    render_solved()
    render_status()
    render_grid()
    render_footer()


if __name__ == "__main__":
    main()