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

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = SECRET_KEY

bank = PuzzleBank()


def get_or_init_state():
    """
    Retrieve or initialize the session state dictionary.
    
    The state structure is:
    {
        puzzle_id: {
            "solved_phrases": [indices],
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
               If error: (None, (error_dict, status_code))
    """
    if not puzzle_id:
        error = jsonify({"error": "Missing puzzle_id"}), 400
        return None, error
    
    puzzle = bank.get_by_id(puzzle_id)
    if not puzzle:
        error = jsonify({"error": "Puzzle not found"}), 404
        return None, error
    
    return puzzle, None


def get_remaining_segments(puzzle, used_segment_ids):
    """
    Filter and return segments that have not yet been used.
    
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
    Build a complete puzzle response with current state.
    
    Args:
        puzzle: The puzzle object.
        puzzle_state (dict): The current state for this puzzle.
    
    Returns:
        dict: Response dictionary with puzzle data and state.
    """
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])
    segments = get_remaining_segments(puzzle, used_segment_ids)
    solved_phrases = [
        puzzle.phrases[i] for i in puzzle_state[SOLVED_PHRASES_KEY]
    ]
    
    return {
        "id": puzzle.id,
        "theme": puzzle.theme,
        "phrase_count": len(puzzle.phrases),
        "segments": segments,
        "solved": solved_phrases,
        "complete": puzzle_state[COMPLETE_KEY],
        "phrases_total": len(puzzle.phrases),
    }


def mark_phrase_solved(puzzle, puzzle_state, phrase_index):
    """
    Mark a phrase as solved and update used segments.
    
    Args:
        puzzle: The puzzle object.
        puzzle_state (dict): The puzzle state to update.
        phrase_index (int): Index of the phrase to mark as solved.
    """
    if phrase_index not in puzzle_state[SOLVED_PHRASES_KEY]:
        puzzle_state[SOLVED_PHRASES_KEY].append(phrase_index)
        
        # Mark all segments of this phrase as used
        segments_to_use = [
            seg.id for seg in puzzle.segments
            if seg.phrase_index == phrase_index
        ]
        puzzle_state[USED_SEGMENTS_KEY].extend(segments_to_use)
        
        # Check if puzzle is complete
        puzzle_state[COMPLETE_KEY] = (
            len(puzzle_state[SOLVED_PHRASES_KEY]) == len(puzzle.phrases)
        )
        session.modified = True


def validate_submit_payload(data):
    """
    Validate the payload structure for a submit request.
    
    Args:
        data (dict): The request data to validate.
    
    Returns:
        tuple: (is_valid, error_response) where error_response is None if valid.
    """
    puzzle_id = data.get("puzzle_id")
    selected_ids = data.get("segment_ids", [])
    
    if (not puzzle_id or
        not isinstance(selected_ids, list) or
        not selected_ids):
        error = jsonify({"error": "Invalid payload"}), 400
        return False, error
    
    return True, None


def check_segments_not_used(selected_ids, used_segment_ids):
    """
    Check if any selected segments have already been used.
    
    Args:
        selected_ids (list): List of segment IDs being submitted.
        used_segment_ids (set): Set of already-used segment IDs.
    
    Returns:
        tuple: (is_valid, error_response) where error_response is None if valid.
    """
    for segment_id in selected_ids:
        if segment_id in used_segment_ids:
            error = jsonify({
                "status": STATUS_INVALID,
                "message": (
                    "One or more selected strands have already been used "
                    "in a solved phrase."
                ),
            }), 200
            return False, error
    
    return True, None


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
    Fetch puzzle data with segments, theme, and target phrase count.
    
    Query Parameters:
        id (str, optional): Specific puzzle ID. If not provided, a random puzzle is selected.
    
    Returns:
        dict: JSON response with puzzle data and current session state.
    """
    puzzle_id = request.args.get("id")
    
    if puzzle_id:
        puzzle = bank.get_by_id(puzzle_id)
        if not puzzle:
            return jsonify({"error": "Puzzle not found"}), 404
    else:
        puzzle = bank.random_puzzle()
    
    puzzle_state = init_puzzle_state(puzzle.id)
    response = build_puzzle_response(puzzle, puzzle_state)
    
    return jsonify(response)


@app.get("/api/state")
def api_state():
    """
    Retrieve the current session state for a specific puzzle.
    
    Query Parameters:
        id (str): The puzzle ID.
    
    Returns:
        dict: JSON response with puzzle state including solved phrases and completion status.
    """
    puzzle_id = request.args.get("id")
    
    puzzle, error = get_puzzle_or_error(puzzle_id)
    if error:
        return error
    
    state = get_or_init_state().get(puzzle_id)
    if state is None:
        return jsonify({"error": "No state for puzzle"}), 404
    
    solved_phrases = [
        puzzle.phrases[i] for i in state[SOLVED_PHRASES_KEY]
    ]
    
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
    
    Request JSON:
        puzzle_id (str): The puzzle ID.
        segment_ids (list): List of segment IDs in order.
    
    Returns:
        dict: JSON response with validation result and updated puzzle state.
              Status can be "ok", "partial", or "invalid".
    """
    data = request.get_json(force=True, silent=True) or {}
    
    # Validate payload structure
    is_valid, error = validate_submit_payload(data)
    if not is_valid:
        return error
    
    puzzle_id = data.get("puzzle_id")
    selected_ids = data.get("segment_ids")
    
    # Fetch puzzle
    puzzle, error = get_puzzle_or_error(puzzle_id)
    if error:
        return error
    
    # Initialize and load puzzle state
    puzzle_state = init_puzzle_state(puzzle_id)
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])
    
    # Check if segments are already used
    is_valid, error = check_segments_not_used(selected_ids, used_segment_ids)
    if not is_valid:
        return error
    
    # Verify the merge
    result = verify_merge(puzzle, selected_ids)
    
    if result["status"] == STATUS_OK:
        phrase_index = result["phrase_index"]
        mark_phrase_solved(puzzle, puzzle_state, phrase_index)
        
        # Build response with remaining segments
        remaining_segments = get_remaining_segments(
            puzzle,
            set(puzzle_state[USED_SEGMENTS_KEY])
        )
        solved_phrases = [
            puzzle.phrases[i] for i in puzzle_state[SOLVED_PHRASES_KEY]
        ]
        
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
    
    Request JSON:
        puzzle_id (str): The puzzle ID to reset.
    
    Returns:
        dict: JSON response confirming the reset.
    """
    data = request.get_json(force=True, silent=True) or {}
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
    Load a new random puzzle and initialize its session state.
    
    Returns:
        dict: JSON response with the new puzzle ID.
    """
    puzzle = bank.random_puzzle()
    puzzle_state = init_puzzle_state(puzzle.id)
    
    logger.info(f"New puzzle loaded: {puzzle.id}")
    return jsonify({"status": STATUS_OK, "id": puzzle.id})


if __name__ == "__main__":
    logger.info(
        f"Starting Strands game server at http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    )
    app.run(debug=DEBUG_MODE, host=DEFAULT_HOST, port=DEFAULT_PORT)