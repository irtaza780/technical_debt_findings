import logging
from flask import Flask, render_template, jsonify, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from puzzle import PuzzleBank, verify_merge

# Configuration constants
SECRET_KEY = "change-this-secret-in-production"
DEBUG_MODE = True
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000

# Session state structure constants
STATE_KEY = "state"
SOLVED_PHRASES_KEY = "solved_phrases"
USED_SEGMENTS_KEY = "used_segments"
COMPLETE_KEY = "complete"

# API response constants
STATUS_OK = "ok"
STATUS_PARTIAL = "partial"
STATUS_INVALID = "invalid"

# HTTP status codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = SECRET_KEY

bank = PuzzleBank()


def get_or_init_state():
    """
    Retrieve or initialize the session state dictionary.
    
    The state structure maps puzzle IDs to their progress:
    {
        puzzle_id: {
            "solved_phrases": [phrase_indices],
            "used_segments": [segment_ids],
            "complete": bool
        },
        ...
    }
    
    Returns:
        dict: The session state dictionary.
    """
    if STATE_KEY not in session:
        session[STATE_KEY] = {}
    return session[STATE_KEY]


def init_puzzle_state(puzzle_id):
    """
    Initialize or retrieve the state for a specific puzzle.
    
    Args:
        puzzle_id (str): The unique identifier for the puzzle.
    
    Returns:
        dict: The puzzle-specific state dictionary.
    """
    state = get_or_init_state()
    if puzzle_id not in state:
        state[puzzle_id] = {
            SOLVED_PHRASES_KEY: [],
            USED_SEGMENTS_KEY: [],
            COMPLETE_KEY: False,
        }
        session.modified = True
    return state[puzzle_id]


def get_puzzle_or_error(puzzle_id):
    """
    Retrieve a puzzle by ID or return an error response.
    
    Args:
        puzzle_id (str): The unique identifier for the puzzle.
    
    Returns:
        tuple: (puzzle_object, error_response) where one is None.
               If successful: (puzzle, None)
               If failed: (None, (error_dict, status_code))
    """
    if not puzzle_id:
        error_response = (jsonify({"error": "Missing puzzle_id"}), HTTP_BAD_REQUEST)
        return None, error_response
    
    puzzle = bank.get_by_id(puzzle_id)
    if not puzzle:
        error_response = (jsonify({"error": "Puzzle not found"}), HTTP_NOT_FOUND)
        return None, error_response
    
    return puzzle, None


def get_remaining_segments(puzzle, used_segment_ids):
    """
    Filter segments that have not yet been used.
    
    Args:
        puzzle: The puzzle object containing all segments.
        used_segment_ids (set): Set of segment IDs already used.
    
    Returns:
        list: List of dictionaries representing remaining segments.
    """
    return [
        seg.to_dict() for seg in puzzle.segments
        if seg.id not in used_segment_ids
    ]


def build_puzzle_response(puzzle, puzzle_state):
    """
    Construct the API response for a puzzle.
    
    Args:
        puzzle: The puzzle object.
        puzzle_state (dict): The current state of the puzzle.
    
    Returns:
        dict: The puzzle response data.
    """
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])
    remaining_segments = get_remaining_segments(puzzle, used_segment_ids)
    solved_phrase_indices = puzzle_state[SOLVED_PHRASES_KEY]
    solved_phrases = [puzzle.phrases[i] for i in solved_phrase_indices]
    
    return {
        "id": puzzle.id,
        "theme": puzzle.theme,
        "phrase_count": len(puzzle.phrases),
        "segments": remaining_segments,
        "solved": solved_phrases,
        "complete": puzzle_state[COMPLETE_KEY],
        "phrases_total": len(puzzle.phrases),
    }


def check_puzzle_completion(puzzle_state, puzzle):
    """
    Determine if the puzzle is fully solved.
    
    Args:
        puzzle_state (dict): The current state of the puzzle.
        puzzle: The puzzle object.
    
    Returns:
        bool: True if all phrases are solved, False otherwise.
    """
    return len(puzzle_state[SOLVED_PHRASES_KEY]) == len(puzzle.phrases)


def mark_phrase_solved(puzzle, puzzle_state, phrase_index):
    """
    Mark a phrase as solved and update used segments.
    
    Args:
        puzzle: The puzzle object.
        puzzle_state (dict): The current state of the puzzle.
        phrase_index (int): The index of the solved phrase.
    """
    if phrase_index not in puzzle_state[SOLVED_PHRASES_KEY]:
        puzzle_state[SOLVED_PHRASES_KEY].append(phrase_index)
        
        # Mark all segments of this phrase as used
        phrase_segment_ids = [
            seg.id for seg in puzzle.segments
            if seg.phrase_index == phrase_index
        ]
        puzzle_state[USED_SEGMENTS_KEY].extend(phrase_segment_ids)
        
        # Check if puzzle is now complete
        puzzle_state[COMPLETE_KEY] = check_puzzle_completion(puzzle_state, puzzle)
        session.modified = True


@app.route("/")
def index():
    """
    Render the main game page.
    
    Returns:
        str: Rendered HTML template for the game interface.
    """
    return render_template("index.html")


@app.get("/api/puzzle")
def api_puzzle():
    """
    Fetch puzzle data with segments and theme.
    
    Query Parameters:
        id (str, optional): Specific puzzle ID. If omitted, a random puzzle is selected.
    
    Returns:
        dict: Puzzle data including segments, theme, and current progress.
    """
    puzzle_id = request.args.get("id")
    
    if puzzle_id:
        puzzle = bank.get_by_id(puzzle_id)
        if not puzzle:
            return jsonify({"error": "Puzzle not found"}), HTTP_NOT_FOUND
    else:
        puzzle = bank.random_puzzle()
    
    puzzle_state = init_puzzle_state(puzzle.id)
    response = build_puzzle_response(puzzle, puzzle_state)
    
    return jsonify(response)


@app.get("/api/state")
def api_state():
    """
    Retrieve the current session state for a puzzle.
    
    Query Parameters:
        id (str): The puzzle ID.
    
    Returns:
        dict: Current puzzle state including solved phrases and completion status.
    """
    puzzle_id = request.args.get("id")
    
    puzzle, error = get_puzzle_or_error(puzzle_id)
    if error:
        return error
    
    state = get_or_init_state().get(puzzle_id)
    if state is None:
        return jsonify({"error": "No state for puzzle"}), HTTP_NOT_FOUND
    
    solved_phrase_indices = state[SOLVED_PHRASES_KEY]
    solved_phrases = [puzzle.phrases[i] for i in solved_phrase_indices]
    
    return jsonify({
        "id": puzzle_id,
        "solved": solved_phrases,
        "complete": state[COMPLETE_KEY],
        "used_segments": state[USED_SEGMENTS_KEY],
    })


@app.post("/api/submit")
def api_submit():
    """
    Validate and process a merge submission.
    
    JSON Payload:
        puzzle_id (str): The puzzle ID.
        segment_ids (list): Ordered list of segment IDs to merge.
    
    Returns:
        dict: Validation result with status ("ok", "partial", or "invalid"),
              message, and updated puzzle state if successful.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
    except ValueError as e:
        logger.warning(f"Invalid JSON in submit request: {e}")
        return jsonify({"error": "Invalid JSON"}), HTTP_BAD_REQUEST
    
    puzzle_id = data.get("puzzle_id")
    selected_ids = data.get("segment_ids", [])
    
    # Validate request payload
    if not puzzle_id or not isinstance(selected_ids, list) or not selected_ids:
        return jsonify({"error": "Invalid payload"}), HTTP_BAD_REQUEST
    
    puzzle, error = get_puzzle_or_error(puzzle_id)
    if error:
        return error
    
    puzzle_state = init_puzzle_state(puzzle_id)
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])
    
    # Check if any selected segment is already used
    if any(seg_id in used_segment_ids for seg_id in selected_ids):
        return jsonify({
            "status": STATUS_INVALID,
            "message": "One or more selected strands have already been used in a solved phrase.",
        }), HTTP_OK
    
    # Verify the merge
    result = verify_merge(puzzle, selected_ids)
    
    if result["status"] == STATUS_OK:
        phrase_index = result["phrase_index"]
        mark_phrase_solved(puzzle, puzzle_state, phrase_index)
        
        # Build response with remaining segments
        updated_used_ids = set(puzzle_state[USED_SEGMENTS_KEY])
        remaining_segments = get_remaining_segments(puzzle, updated_used_ids)
        solved_phrase_indices = puzzle_state[SOLVED_PHRASES_KEY]
        solved_phrases = [puzzle.phrases[i] for i in solved_phrase_indices]
        
        return jsonify({
            "status": STATUS_OK,
            "message": result["message"],
            "solved_phrase": result["solved_phrase"],
            "remaining_segments": remaining_segments,
            "solved": solved_phrases,
            "complete": puzzle_state[COMPLETE_KEY],
        })
    
    # Return partial or invalid feedback as-is
    return jsonify(result)


@app.post("/api/reset")
def api_reset():
    """
    Reset the session state for a puzzle to its initial state.
    
    JSON Payload:
        puzzle_id (str): The puzzle ID to reset.
    
    Returns:
        dict: Confirmation message.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
    except ValueError as e:
        logger.warning(f"Invalid JSON in reset request: {e}")
        return jsonify({"error": "Invalid JSON"}), HTTP_BAD_REQUEST
    
    puzzle_id = data.get("puzzle_id")
    
    puzzle, error = get_puzzle_or_error(puzzle_id)
    if error:
        return error
    
    state = get_or_init_state()
    state[puzzle_id] = {
        SOLVED_PHRASES_KEY: [],
        USED_SEGMENTS_KEY: [],
        COMPLETE_KEY: False,
    }
    session.modified = True
    
    logger.info(f"Puzzle {puzzle_id} reset by user")
    return jsonify({"status": STATUS_OK, "message": "Puzzle reset."})


@app.get("/api/new")
def api_new():
    """
    Load a new random puzzle and initialize its state.
    
    Returns:
        dict: Status confirmation and the new puzzle ID.
    """
    puzzle = bank.random_puzzle()
    state = get_or_init_state()
    state[puzzle.id] = {
        SOLVED_PHRASES_KEY: [],
        USED_SEGMENTS_KEY: [],
        COMPLETE_KEY: False,
    }
    session.modified = True
    
    logger.info(f"New puzzle loaded: {puzzle.id}")
    return jsonify({"status": STATUS_OK, "id": puzzle.id})


if __name__ == "__main__":
    logger.info(f"Starting Strands game server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    app.run(debug=DEBUG_MODE, host=DEFAULT_HOST, port=DEFAULT_PORT)