import logging
from flask import Flask, render_template, jsonify, request, session
from uuid import uuid4

try:
    from strands.puzzle import default_puzzle
    from strands.game import GameState
except ModuleNotFoundError:
    from puzzle import default_puzzle
    from game import GameState

# Configuration constants
SECRET_KEY = "dev-secret-change-me"
SESSION_ID_KEY = "sid"
GAME_KEY = "game"
SPANGRAM_PREFIX = "(spangram) "

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app initialization
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
    if SESSION_ID_KEY not in session:
        session[SESSION_ID_KEY] = str(uuid4())
    
    sid = session[SESSION_ID_KEY]
    
    if sid not in _SESSIONS:
        _SESSIONS[sid] = {GAME_KEY: GameState(PUZZLE)}
    
    return sid


def _get_game_state(session_id: str) -> "GameState":
    """
    Retrieve the GameState for a given session ID.
    
    Args:
        session_id: The session ID to look up.
    
    Returns:
        GameState: The game state object for the session.
    """
    return _SESSIONS[session_id][GAME_KEY]


def _serialize_claimed_cells(game: "GameState") -> list[dict]:
    """
    Serialize the claimed cells from a GameState.
    
    Args:
        game: The GameState object to serialize from.
    
    Returns:
        list[dict]: List of claimed cell dictionaries with row, column, type, and word.
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


def _serialize_state(game: "GameState") -> dict:
    """
    Serialize the complete game state to a JSON-compatible dictionary.
    
    Args:
        game: The GameState object to serialize.
    
    Returns:
        dict: A dictionary containing all game state information for the client.
    """
    state = {
        "rows": game.puzzle.rows,
        "cols": game.puzzle.cols,
        "grid": game.puzzle.grid,
        "theme": game.puzzle.theme,
        "spangram": game.puzzle.spangram,
        "foundWords": sorted(list(game.found_words)),
        "hints": game.hints,
        "nonThemeCount": len(game.non_theme_words),
        "claimed": _serialize_claimed_cells(game),
        "totalTheme": len(game.puzzle.theme_words),
        "completed": game.is_completed(),
    }
    return state


def _parse_coordinates(coords_raw: list) -> list[tuple[int, int]]:
    """
    Parse and validate coordinate pairs from user input.
    
    Args:
        coords_raw: Raw coordinate data from request.
    
    Returns:
        list[tuple[int, int]]: List of validated (row, col) tuples.
    """
    normalized_coords = []
    for pair in coords_raw:
        try:
            row, col = int(pair[0]), int(pair[1])
            normalized_coords.append((row, col))
        except (ValueError, IndexError, TypeError):
            # Skip invalid coordinate pairs
            logger.debug(f"Skipped invalid coordinate pair: {pair}")
            continue
    return normalized_coords


def _build_remaining_words(game: "GameState") -> list[str]:
    """
    Build a list of remaining words not yet found in the game.
    
    Args:
        game: The GameState object to check.
    
    Returns:
        list[str]: List of remaining words, with spangram prefixed if not found.
    """
    remaining = [
        word for word in game.puzzle.theme_words
        if word not in game.found_words
    ]
    
    # Prepend spangram if not yet found
    if game.puzzle.spangram not in game.found_words:
        remaining.insert(0, f"{SPANGRAM_PREFIX}{game.puzzle.spangram}")
    
    return remaining


@app.get("/")
def index() -> str:
    """
    Render the main game page.
    
    Returns:
        str: Rendered HTML template for the game interface.
    """
    _ensure_session()
    return render_template("index.html")


@app.get("/state")
def state() -> dict:
    """
    Return the current game state for the session.
    
    Returns:
        dict: JSON-serialized game state.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    return jsonify(_serialize_state(game))


@app.post("/select")
def select() -> dict:
    """
    Attempt to commit a dragged letter selection as a word.
    
    Expects JSON payload with 'coords' key containing list of [row, col] pairs.
    
    Returns:
        dict: JSON response with result and updated game state.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    
    payload = request.get_json(silent=True) or {}
    coords_raw = payload.get("coords", [])
    
    # Parse and validate coordinates
    normalized_coords = _parse_coordinates(coords_raw)
    
    # Attempt to commit the selection
    result = game.try_commit_selection(normalized_coords)
    
    return jsonify({
        "result": result,
        "state": _serialize_state(game)
    })


@app.post("/hint")
def hint() -> dict:
    """
    Reveal a themed word or spangram by consuming a hint.
    
    Returns:
        dict: JSON response with revealed hint details and updated game state.
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
    
    return jsonify({
        "result": result,
        "state": _serialize_state(game)
    })


@app.post("/reset")
def reset() -> dict:
    """
    Reset the game state for the current session.
    
    Returns:
        dict: JSON response with fresh game state.
    """
    session_id = _ensure_session()
    _SESSIONS[session_id][GAME_KEY] = GameState(PUZZLE)
    
    return jsonify({
        "state": _serialize_state(_SESSIONS[session_id][GAME_KEY])
    })


@app.get("/remaining")
def remaining() -> dict:
    """
    Return the list of remaining words not yet found.
    
    Returns:
        dict: JSON response with list of remaining words.
    """
    session_id = _ensure_session()
    game = _get_game_state(session_id)
    
    remaining_words = _build_remaining_words(game)
    
    return jsonify({"remaining": remaining_words})


if __name__ == "__main__":
    app.run(debug=True)