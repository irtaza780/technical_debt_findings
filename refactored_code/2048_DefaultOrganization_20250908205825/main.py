import logging
import os

from flask import Flask, jsonify, render_template, request, session

from game import Game2048

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_SECRET_KEY = "dev-secret-2048"
VALID_DIRECTIONS = frozenset({"up", "down", "left", "right"})
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
SESSION_GAME_STATE_KEY = "game_state"

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)
app.secret_key = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)


# ---------------------------------------------------------------------------
# Game state helpers
# ---------------------------------------------------------------------------


def build_game_state_payload(game: Game2048) -> dict:
    """
    Serialize a Game2048 instance into a JSON-serialisable dictionary.

    Args:
        game: The active Game2048 instance.

    Returns:
        A dictionary containing board, score, max_tile, size, and game_over.
    """
    return {
        "board": game.board,
        "score": game.score,
        "max_tile": game.max_tile,
        "size": game.size,
        "game_over": not game.can_move(),
    }


def new_game() -> Game2048:
    """
    Create a fresh Game2048 instance and persist it to the session.

    Returns:
        A newly initialised Game2048 object.
    """
    game = Game2048()
    save_game_to_session(game)
    logger.info("New game created and saved to session.")
    return game


def save_game_to_session(game: Game2048) -> None:
    """
    Persist the current game state into the Flask session.

    Args:
        game: The Game2048 instance whose state should be saved.
    """
    session[SESSION_GAME_STATE_KEY] = game.to_state()


def get_game_from_session() -> Game2048:
    """
    Retrieve the current game from the session, creating a new one if absent
    or if the stored state is corrupted.

    Returns:
        A Game2048 instance representing the current game.
    """
    raw_state = session.get(SESSION_GAME_STATE_KEY)

    if raw_state is None:
        logger.info("No game state found in session; starting a new game.")
        return new_game()

    try:
        return Game2048.from_state(raw_state)
    except (KeyError, ValueError, TypeError) as exc:
        # Corrupted or incompatible session data — fall back to a fresh game.
        logger.warning("Failed to restore game from session (%s); starting fresh.", exc)
        return new_game()


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    """Render the main game page."""
    return render_template("index.html")


@app.route("/init", methods=["POST"])
def init_game():
    """
    Start a brand-new game, replacing any existing session state.

    Returns:
        JSON response with ok=True and the initial game state.
    """
    game = new_game()
    logger.info("Game initialised via /init endpoint.")
    return jsonify({"ok": True, "state": build_game_state_payload(game)})


@app.route("/state", methods=["GET"])
def get_state():
    """
    Return the current game state without modifying it.

    Returns:
        JSON response with ok=True and the current game state.
    """
    game = get_game_from_session()
    return jsonify({"ok": True, "state": build_game_state_payload(game)})


def _handle_game_over(game: Game2048):
    """
    Build the JSON response for a move request when the game is already over.

    Persists the unchanged state to the session before responding.

    Args:
        game: The Game2048 instance that has no remaining moves.

    Returns:
        A Flask JSON response indicating the game is over and nothing changed.
    """
    save_game_to_session(game)
    state_payload = build_game_state_payload(game)
    # Ensure game_over is explicitly True regardless of can_move result.
    state_payload["game_over"] = True
    return jsonify({"ok": True, "changed": False, "state": state_payload})


def _handle_valid_move(game: Game2048, direction: str):
    """
    Apply a move in the given direction, spawn a new tile if the board changed,
    and persist the updated state.

    Args:
        game:      The active Game2048 instance.
        direction: One of 'up', 'down', 'left', 'right'.

    Returns:
        A Flask JSON response with the move outcome and updated game state.
    """
    changed, points_gained = game.move(direction)

    if changed:
        # Only add a random tile when the board actually shifted.
        game.add_random_tile()

    # Always persist so that score updates are not lost.
    save_game_to_session(game)

    logger.info(
        "Move '%s' applied — changed=%s, points_gained=%s, score=%s.",
        direction,
        changed,
        points_gained,
        game.score,
    )

    return jsonify(
        {
            "ok": True,
            "changed": changed,
            "gained": points_gained,
            "state": build_game_state_payload(game),
        }
    )


@app.route("/move", methods=["POST"])
def move():
    """
    Process a move request from the client.

    Expects a JSON body with a 'dir' key whose value is one of
    'up', 'down', 'left', or 'right'.

    Returns:
        JSON response describing whether the board changed and the new state,
        or a 400 error if the direction is invalid.
    """
    payload = request.get_json(silent=True) or {}
    direction = payload.get("dir")

    if direction not in VALID_DIRECTIONS:
        logger.warning("Invalid direction received: %r", direction)
        return jsonify({"ok": False, "error": "Invalid direction"}), 400

    game = get_game_from_session()

    if not game.can_move():
        logger.info("Move requested but game is already over.")
        return _handle_game_over(game)

    return _handle_valid_move(game, direction)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Flask development server on %s:%s.", SERVER_HOST, SERVER_PORT)
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)
