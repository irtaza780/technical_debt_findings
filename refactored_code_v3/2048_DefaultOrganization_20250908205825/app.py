import logging
import os
from flask import Flask, render_template, request, session, jsonify
from game import Game2048

# Configuration constants
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-2048')
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
DEBUG_MODE = True
SESSION_GAME_STATE_KEY = 'game_state'
VALID_DIRECTIONS = {'up', 'down', 'left', 'right'}

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)
app.secret_key = SECRET_KEY


def get_game_from_session() -> Game2048:
    """
    Load the current game from the session or create a new one if missing.
    
    Returns:
        Game2048: The current game instance, either restored from session or newly created.
    """
    state = session.get(SESSION_GAME_STATE_KEY)
    if state:
        try:
            return Game2048.from_state(state)
        except ValueError as e:
            # If session data is corrupted, start a new game
            logger.warning(f"Failed to restore game state: {e}. Starting new game.")
            return _create_and_save_new_game()
    else:
        return _create_and_save_new_game()


def _create_and_save_new_game() -> Game2048:
    """
    Create a fresh game instance and persist it to the session.
    
    Returns:
        Game2048: A newly initialized game instance.
    """
    game = Game2048()
    _save_game_to_session(game)
    return game


def _save_game_to_session(game: Game2048) -> None:
    """
    Persist the game state to the session.
    
    Args:
        game: The Game2048 instance to save.
    """
    session[SESSION_GAME_STATE_KEY] = game.to_state()


def _build_game_state_response(game: Game2048) -> dict:
    """
    Build a standardized game state dictionary for API responses.
    
    Args:
        game: The Game2048 instance to serialize.
    
    Returns:
        dict: A dictionary containing board, score, max_tile, size, and game_over status.
    """
    return {
        'board': game.board,
        'score': game.score,
        'max_tile': game.max_tile,
        'size': game.size,
        'game_over': not game.can_move(),
    }


@app.route('/', methods=['GET'])
def index():
    """
    Serve the main game page.
    
    Returns:
        str: Rendered HTML template for the game interface.
    """
    return render_template('index.html')


@app.route('/init', methods=['POST'])
def init_game():
    """
    Initialize a new game and return its initial state.
    
    Returns:
        Response: JSON response with success status and initial game state.
    """
    game = _create_and_save_new_game()
    return jsonify({
        'ok': True,
        'state': _build_game_state_response(game)
    })


@app.route('/state', methods=['GET'])
def state():
    """
    Retrieve the current game state without making any moves.
    
    Returns:
        Response: JSON response with success status and current game state.
    """
    game = get_game_from_session()
    return jsonify({
        'ok': True,
        'state': _build_game_state_response(game)
    })


@app.route('/move', methods=['POST'])
def move():
    """
    Process a player move in the specified direction.
    
    Expected JSON payload:
        {
            'dir': str - One of 'up', 'down', 'left', 'right'
        }
    
    Returns:
        Response: JSON response with move result and updated game state,
                 or 400 error if direction is invalid.
    """
    payload = request.get_json(silent=True) or {}
    direction = payload.get('dir')
    
    # Validate direction input
    if direction not in VALID_DIRECTIONS:
        logger.warning(f"Invalid move direction received: {direction}")
        return jsonify({'ok': False, 'error': 'Invalid direction'}), 400

    game = get_game_from_session()

    # Check if game is already over
    if not game.can_move():
        logger.info("Move attempted on finished game")
        _save_game_to_session(game)
        return jsonify({
            'ok': True,
            'changed': False,
            'state': _build_game_state_response(game)
        })

    # Execute the move and spawn new tile if board changed
    changed, gained = game.move(direction)
    if changed:
        game.add_random_tile()
    
    # Persist game state regardless of move outcome
    _save_game_to_session(game)

    return jsonify({
        'ok': True,
        'changed': changed,
        'gained': gained,
        'state': _build_game_state_response(game)
    })


if __name__ == '__main__':
    logger.info(f"Starting 2048 game server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=DEBUG_MODE)