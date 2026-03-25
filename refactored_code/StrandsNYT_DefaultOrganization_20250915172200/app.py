import logging
from flask import Flask, render_template, jsonify, request, session
from uuid import uuid4
from strands.puzzle import default_puzzle
from strands.game import GameState

# Configuration constants
SECRET_KEY = "dev-secret-change-me"
DEBUG_MODE = True

# Game constants
SPANGRAM_PREFIX = "(spangram) "

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY

# Single shared puzzle instance (read-only)
PUZZLE = default_puzzle()

# In-memory game state storage keyed by session id
_SESSIONS = {}


def _ensure_session() -> str:
    """
    Ensure a session exists for the current user.
    
    Creates a new session ID if one doesn't exist, and initializes
    a GameState for that session if needed.
    
    Returns:
        str: The session ID for the current user.
    """
    if "sid" not in session:
        session["sid"] = str(uuid4())
    
    sid = session["sid"]
    
    # Initialize game state for new sessions
    if sid not in _SESSIONS:
        _SESSIONS[sid] = {"game": GameState(PUZZLE)}
        logger.info(f"Created new game session: {sid}")
    
    return sid


def _get_game_state(session_id: str) -> GameState:
    """
    Retrieve the GameState for a given session ID.
    
    Args:
        session_id (str): The session ID.
    
    Returns:
        GameState: The game state object for the session.
    """
    return _SESSIONS[session_id]["game"]


def _serialize_claimed_cells(game: GameState) -> list:
    """
    Serialize claimed cells from the game state.
    
    Args:
        game (GameState): The current game state.
    
    Returns:
        list: List of dictionaries containing claimed cell information.
    """
    claimed_list = []
    for (row, col), metadata in game.claimed.items():
        claimed_list.append({
            "r": row,
            "c": col,
            "type": metadata["type"],
            "word": metadata["word"]
        })
    return claimed_list


def _serialize_state(game: GameState) -> dict:
    """
    Serialize the complete game state to a JSON-compatible dictionary.
    
    Args:
        game (GameState): The current game state.
    
    Returns:
        dict: Serialized game state containing grid, found words, hints, and completion status.
    """
    claimed_cells = _serialize_claimed_cells(game)
    
    state = {
        "rows": game.puzzle.rows,
        "cols": game.puzzle.cols,
        "grid": game.puzzle.grid,
        "theme": game.puzzle.theme,
        "spangram": game.puzzle.spangram,
        "foundWords": sorted(list(game.found_words)),
        "hints": game.hints,
        "nonThemeCount": len(game.non_theme_words),
        "claimed": claimed_cells,
        "totalTheme": len(game.puzzle.theme_words),
        "completed": game.is_completed(),
    }
    return state


def _parse_coordinates(coords_data: list) -> list:
    """
    Parse and validate coordinate pairs from request data.
    
    Converts coordinate pairs to tuples of integers, skipping invalid entries.
    
    Args:
        coords_data (list): List of coordinate pairs [row, col].
    
    Returns:
        list: List of validated (row, col) tuples.
    """
    normalized_coords = []
    for pair in coords_data:
        try:
            row, col = int(pair[0]), int(pair[1])
            normalized_coords.append((row, col))
        except (ValueError, IndexError, TypeError):
            logger.warning(f"Invalid coordinate pair: {pair}")
            continue
    return normalized_coords


def _get_remaining_words(game: GameState) -> list:
    """
    Get the list of words not yet found in the game.
    
    Args:
        game (GameState): The current game state.
    
    Returns:
        list: List of remaining words, with spangram prefixed if not found.
    """
    remaining = [
        word for word in game.puzzle.theme_words
        if word not in game.found_words
    ]
    
    # Add spangram to the front if not yet found
    if game.puzzle.spangram not in game.found_words:
        remaining.insert(0, f"{SPANGRAM_PREFIX}{game.puzzle.spangram}")
    
    return remaining


@app.get("/")
def index():
    """
    Render the main game page.
    
    Returns:
        str: Rendered HTML template for the game interface.
    """
    _ensure_session()
    return render_template("index.html")


@app.get("/state")
def state():
    """
    Return the current game state for the session.
    
    Returns:
        Response: JSON object containing the serialized game state.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    return jsonify(_serialize_state(game))


@app.post("/select")
def select():
    """
    Attempt to commit a dragged letter selection as a word.
    
    Expects JSON payload with 'coords' key containing list of [row, col] pairs.
    
    Returns:
        Response: JSON object with result and updated game state.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    
    payload = request.get_json(silent=True) or {}
    coords_data = payload.get("coords", [])
    
    # Parse and validate coordinates
    normalized_coords = _parse_coordinates(coords_data)
    
    # Attempt to commit the selection
    result = game.try_commit_selection(normalized_coords)
    logger.info(f"Selection attempt: {result}")
    
    return jsonify({
        "result": result,
        "state": _serialize_state(game)
    })


@app.post("/hint")
def hint():
    """
    Reveal a themed word or spangram by consuming a hint.
    
    Returns:
        Response: JSON object with revealed hint information and updated game state.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    
    revealed = game.reveal_hint()
    
    if revealed:
        word, coords, hint_type = revealed
        result = {
            "type": hint_type,
            "word": word,
            "coords": coords
        }
    else:
        result = {
            "type": "none",
            "word": None,
            "coords": []
        }
    
    logger.info(f"Hint revealed: {result['type']}")
    
    return jsonify({
        "result": result,
        "state": _serialize_state(game)
    })


@app.post("/reset")
def reset():
    """
    Reset the game state for the current session.
    
    Returns:
        Response: JSON object with the new game state.
    """
    session_id = _ensure_session()
    _SESSIONS[session_id]["game"] = GameState(PUZZLE)
    logger.info(f"Game reset for session: {session_id}")
    
    return jsonify({
        "state": _serialize_state(_SESSIONS[session_id]["game"])
    })


@app.get("/remaining")
def remaining():
    """
    Return the list of remaining words not yet found.
    
    Returns:
        Response: JSON object with list of remaining words.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    
    remaining_words = _get_remaining_words(game)
    
    return jsonify({"remaining": remaining_words})


if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)