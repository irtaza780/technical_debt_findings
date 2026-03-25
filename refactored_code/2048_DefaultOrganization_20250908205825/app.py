import logging
import os

from flask import Flask, render_template, request, session, jsonify

from game import Game2048

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_SECRET_KEY = "dev-secret-2048"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
SESSION_GAME_STATE_KEY = "game_state"
VALID_DIRECTIONS = frozenset({"up", "down", "left", "right"})

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)
app.secret_key = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)


# ---------------------------------------------------------------------------
# Game-state helpers
# ---------------------------------------------------------------------------


def build_state_payload(game: Game2048) -> dict:
    """Return a serialisable dict representing the current game state.

    Args:
        game: The active :class:`Game2048` instance.

    Returns:
        A dictionary containing board layout, score, maximum tile value,
        board size, and whether the game is over.
    """
    return {
        "board": game.board,
        "score": game.score,
        "max_tile": game.max_tile,
        "size": game.size,
        "game_over": not game.can_move(),
    }


def new_game() -> Game2048:
    """Create a fresh :class:`Game2048` instance and persist it to the session.

    Returns:
        A newly initialised game object.
    """
    game = Game2048()
    save_game_to_session(game)
    logger.info("New game created and saved to session.")
    return game


def save_game_to_session(game: Game2048) -> None:
    """Serialise and persist *game* state into the Flask session.

    Args:
        game: The :class:`Game2048` instance whose state should be saved.
    """
    session[SESSION_GAME_STATE_KEY] = game.to_state()


def get_game_from_session() -> Game2048:
    """Load the current game from the session, falling back to a new game.

    If the session contains no game state, or if the stored state is
    corrupted / incompatible, a brand-new game is created and stored.

    Returns:
        The active :class:`Game2048` instance.
    """
    raw_state = session.get(SESSION_GAME_STATE_KEY)

    if raw_state is None:
        logger.info("No game state in session; starting a new game.")
        return new_game()

    try:
        return Game2048.from_state(raw_state)
    except (KeyError, ValueError, TypeError) as exc:
        # Session data is present but cannot be deserialised — reset cleanly.
        logger.warning("Corrupted session state (%s); starting a new game.", exc)
        return new_game()


# ---------------------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------------------


def _ok_response(game: Game2048, **extra) -> dict:
    """Build a standard success JSON payload for *game*.

    Args:
        game: The active :class:`Game2048` instance.
        **extra: Additional top-level keys merged into the response dict.

    Returns:
        A dictionary ready to be passed to :func:`flask.jsonify`.
    """
    payload = {"ok": True, "state": build_state_payload(game)}
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    """Render the main game page.

    Returns:
        The rendered ``index.html`` template.
    """
    return render_template("index.html")


@app.route("/init", methods=["POST"])
def init_game():
    """Initialise (or reset) a game and return its starting state.

    Returns:
        JSON response containing ``ok`` and the initial ``state`` payload.
    """
    game = new_game()
    logger.info("Game initialised via /init.")
    return jsonify(_ok_response(game))


@app.route("/state", methods=["GET"])
def state():
    """Return the current game state without mutating it.

    Returns:
        JSON response containing ``ok`` and the current ``state`` payload.
    """
    game = get_game_from_session()
    return jsonify(_ok_response(game))


def _handle_game_over(game: Game2048):
    """Persist and return a response indicating the game is already over.

    Args:
        game: The finished :class:`Game2048` instance.

    Returns:
        A Flask JSON response with ``changed`` set to ``False``.
    """
    save_game_to_session(game)
    logger.info("Move requested but game is already over.")
    return jsonify(_ok_response(game, changed=False))


def _handle_valid_move(game: Game2048, direction: str):
    """Apply *direction* to *game*, spawn a tile if the board changed, and persist.

    Args:
        game: The active :class:`Game2048` instance.
        direction: One of ``"up"``, ``"down"``, ``"left"``, ``"right"``.

    Returns:
        A Flask JSON response with ``changed`` and ``gained`` fields.
    """
    changed, gained = game.move(direction)

    if changed:
        # Only spawn a new tile when the board actually shifted.
        game.add_random_tile()

    # Persist regardless so that score updates are never lost.
    save_game_to_session(game)

    logger.info(
        "Move '%s' applied — changed=%s, gained=%s, score=%s.",
        direction,
        changed,
        gained,
        game.score,
    )
    return jsonify(_ok_response(game, changed=changed, gained=gained))


@app.route("/move", methods=["POST"])
def move():
    """Process a move request and return the updated game state.

    Expects a JSON body with a ``dir`` key whose value is one of
    ``"up"``, ``"down"``, ``"left"``, or ``"right"``.

    Returns:
        JSON response with ``ok``, ``changed``, ``gained``, and ``state``,
        or a 400 error response if the direction is invalid.
    """
    payload = request.get_json(silent=True) or {}
    direction = payload.get("dir")

    if direction not in VALID_DIRECTIONS:
        logger.warning("Invalid direction received: %r", direction)
        return jsonify({"ok": False, "error": "Invalid direction"}), 400

    game = get_game_from_session()

    if not game.can_move():
        return _handle_game_over(game)

    return _handle_valid_move(game, direction)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Flask development server on %s:%s.", SERVER_HOST, SERVER_PORT)
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)
