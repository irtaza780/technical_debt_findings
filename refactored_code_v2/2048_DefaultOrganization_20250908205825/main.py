import logging
import os
from flask import Flask, render_template, request, session, jsonify
from game import Game2048

# Configuration constants
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-2048')
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
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
            return new_game()
    else:
        return new_game()


def save_game_to_session(game: Game2048) -> None:
    """
    Persist the game state to the session.
    
    Args:
        game: The Game2048 instance to persist.
    """
    session[SESSION_GAME_STATE_KEY] = game.to_state()


def new_game() -> Game2048:
    """
    Create and store a fresh game in the session.
    
    Returns:
        Game2048: A newly initialized game instance.
    """
    game = Game2048()
    save_game_to_session(game)
    logger.info("New game created and saved to session.")
    return game


def build_game_state_response(game: Game2048) -> dict:
    """
    Build a standardized game state response dictionary.
    
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


def build_success_response(state: dict, **kwargs) -> dict:
    """
    Build a standardized success response with game state.
    
    Args:
        state: The game state dictionary.
        **kwargs: Additional fields to include in the response.
    
    Returns:
        dict: A response dictionary with 'ok' set to True and the provided state and kwargs.
    """
    response = {'ok': True, 'state': state}
    response.update(kwargs)
    return response


def build_error_response(error_message: str, status_code: int = 400) -> tuple:
    """
    Build a standardized error response.
    
    Args:
        error_message: The error message to include.
        status_code: The HTTP status code (default: 400).
    
    Returns:
        tuple: A tuple of (response_dict, status_code).
    """
    return jsonify({'ok': False, 'error': error_message}), status_code


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
        Response: JSON response containing the new game state.
    """
    game = new_game()
    game_state = build_game_state_response(game)
    return jsonify(build_success_response(game_state))


@app.route('/state', methods=['GET'])
def state():
    """
    Retrieve the current game state without making any moves.
    
    Returns:
        Response: JSON response containing the current game state.
    """
    game = get_game_from_session()
    game_state = build_game_state_response(game)
    return jsonify(build_success_response(game_state))


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
                 or error response if direction is invalid.
    """
    payload = request.get_json(silent=True) or {}
    direction = payload.get('dir')
    
    # Validate direction input
    if direction not in VALID_DIRECTIONS:
        logger.warning(f"Invalid move direction received: {direction}")
        return build_error_response('Invalid direction', 400)

    game = get_game_from_session()

    # Check if game is already over
    if not game.can_move():
        logger.info("Move attempted on finished game.")
        game_state = build_game_state_response(game)
        save_game_to_session(game)
        return jsonify(build_success_response(game_state, changed=False))

    # Execute the move
    changed, gained = game.move(direction)
    if changed:
        game.add_random_tile()

    # Persist the updated game state
    save_game_to_session(game)
    game_state = build_game_state_response(game)
    
    return jsonify(build_success_response(
        game_state,
        changed=changed,
        gained=gained
    ))


if __name__ == '__main__':
    logger.info(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)