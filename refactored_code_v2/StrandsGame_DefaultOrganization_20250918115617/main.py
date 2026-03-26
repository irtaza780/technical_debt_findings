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
SOLVED_PHRASES_KEY = "solved_phrases"
USED_SEGMENTS_KEY = "used_segments"
COMPLETE_KEY = "complete"
STATE_KEY = "state"

# API response constants
STATUS_OK = "ok"
STATUS_PARTIAL = "partial"
STATUS_INVALID = "invalid"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
        dict: The puzzle state dictionary with solved_phrases, used_segments, and complete status.
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


def get_remaining_segments(puzzle, used_segment_ids):
    """
    Filter puzzle segments to exclude those already used.
    
    Args:
        puzzle: The puzzle object containing all segments.
        used_segment_ids (set): Set of segment IDs that have been used.
    
    Returns:
        list: List of dictionaries representing remaining segments.
    """
    return [
        seg.to_dict() for seg in puzzle.segments
        if seg.id not in used_segment_ids
    ]


def get_solved_phrases(puzzle, solved_phrase_indices):
    """
    Retrieve the actual phrase strings for solved phrase indices.
    
    Args:
        puzzle: The puzzle object containing all phrases.
        solved_phrase_indices (list): List of indices into puzzle.phrases.
    
    Returns:
        list: List of solved phrase strings.
    """
    return [puzzle.phrases[i] for i in solved_phrase_indices]


def validate_puzzle_exists(puzzle_id):
    """
    Validate that a puzzle exists in the bank.
    
    Args:
        puzzle_id (str): The puzzle ID to validate.
    
    Returns:
        tuple: (puzzle_object, error_response) where error_response is None if valid.
    """
    puzzle = bank.get_by_id(puzzle_id)
    if not puzzle:
        error_response = (jsonify({"error": "Puzzle not found"}), 404)
        return None, error_response
    return puzzle, None


def validate_submit_payload(data):
    """
    Validate the JSON payload for a submit request.
    
    Args:
        data (dict): The request JSON data.
    
    Returns:
        tuple: (puzzle_id, segment_ids, error_response) where error_response is None if valid.
    """
    puzzle_id = data.get("puzzle_id")
    selected_ids = data.get("segment_ids", [])

    if not puzzle_id or not isinstance(selected_ids, list) or not selected_ids:
        error_response = (jsonify({"error": "Invalid payload"}), 400)
        return None, None, error_response

    return puzzle_id, selected_ids, None


def mark_phrase_solved(puzzle, puzzle_state, phrase_index):
    """
    Mark a phrase as solved and update used segments.
    
    Args:
        puzzle: The puzzle object.
        puzzle_state (dict): The puzzle state to update.
        phrase_index (int): The index of the solved phrase.
    
    Returns:
        bool: True if puzzle is now complete, False otherwise.
    """
    if phrase_index not in puzzle_state[SOLVED_PHRASES_KEY]:
        puzzle_state[SOLVED_PHRASES_KEY].append(phrase_index)
        # Mark all segments of this phrase as used
        segments_to_use = [
            seg.id for seg in puzzle.segments
            if seg.phrase_index == phrase_index
        ]
        puzzle_state[USED_SEGMENTS_KEY].extend(segments_to_use)
        session.modified = True

    # Check if puzzle is complete
    is_complete = len(puzzle_state[SOLVED_PHRASES_KEY]) == len(puzzle.phrases)
    puzzle_state[COMPLETE_KEY] = is_complete
    return is_complete


@app.route("/")
def index():
    """
    Render the main game page.
    
    Returns:
        str: Rendered HTML template for the game interface.
    """
    logger.info("Serving index page")
    return render_template("index.html")


@app.get("/api/puzzle")
def api_puzzle():
    """
    Fetch puzzle data with segments, theme, and target phrase count.
    
    If a puzzle ID is provided via query parameter, that specific puzzle is loaded.
    Otherwise, a random puzzle is selected. Initializes session state if needed.
    
    Query Parameters:
        id (str, optional): Specific puzzle ID to load.
    
    Returns:
        dict: JSON response containing puzzle data and current progress.
    """
    puzzle_id = request.args.get("id")

    if puzzle_id:
        puzzle, error = validate_puzzle_exists(puzzle_id)
        if error:
            logger.warning(f"Puzzle not found: {puzzle_id}")
            return error
    else:
        puzzle = bank.random_puzzle()
        logger.info(f"Selected random puzzle: {puzzle.id}")

    # Initialize state for this puzzle
    puzzle_state = init_puzzle_state(puzzle.id)
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])

    # Build response with remaining segments
    remaining_segments = get_remaining_segments(puzzle, used_segment_ids)
    solved_phrases = get_solved_phrases(puzzle, puzzle_state[SOLVED_PHRASES_KEY])

    response = {
        "id": puzzle.id,
        "theme": puzzle.theme,
        "phrase_count": len(puzzle.phrases),
        "segments": remaining_segments,
        "solved": solved_phrases,
        "complete": puzzle_state[COMPLETE_KEY],
        "phrases_total": len(puzzle.phrases),
    }
    return jsonify(response)


@app.get("/api/state")
def api_state():
    """
    Retrieve the current session state for a specific puzzle.
    
    Query Parameters:
        id (str): The puzzle ID to retrieve state for.
    
    Returns:
        dict: JSON response containing puzzle state and solved phrases.
    """
    puzzle_id = request.args.get("id")
    if not puzzle_id:
        logger.warning("State request missing puzzle ID")
        return jsonify({"error": "Missing id"}), 400

    puzzle, error = validate_puzzle_exists(puzzle_id)
    if error:
        logger.warning(f"State request for non-existent puzzle: {puzzle_id}")
        return error

    puzzle_state = get_or_init_state().get(puzzle_id)
    if puzzle_state is None:
        logger.warning(f"No state found for puzzle: {puzzle_id}")
        return jsonify({"error": "No state for puzzle"}), 404

    solved_phrases = get_solved_phrases(puzzle, puzzle_state[SOLVED_PHRASES_KEY])

    return jsonify({
        "id": puzzle_id,
        "solved": solved_phrases,
        "complete": puzzle_state[COMPLETE_KEY],
        "used_segments": puzzle_state[USED_SEGMENTS_KEY],
    })


@app.post("/api/submit")
def api_submit():
    """
    Validate and process a proposed merge of segments.
    
    Checks if the selected segments form a valid phrase. On full match, marks
    the phrase as solved and removes all its segments. Returns feedback similar
    to NYT Strands: "ok" for valid full merge, "partial" for valid partial path,
    "invalid" otherwise with hints.
    
    JSON Payload:
        puzzle_id (str): The puzzle ID.
        segment_ids (list): List of segment IDs in proposed order.
    
    Returns:
        dict: JSON response with status, message, and updated game state.
    """
    data = request.get_json(force=True, silent=True) or {}

    puzzle_id, selected_ids, error = validate_submit_payload(data)
    if error:
        logger.warning(f"Invalid submit payload: {data}")
        return error

    puzzle, error = validate_puzzle_exists(puzzle_id)
    if error:
        logger.warning(f"Submit for non-existent puzzle: {puzzle_id}")
        return error

    # Load and validate session state
    puzzle_state = init_puzzle_state(puzzle_id)
    used_segment_ids = set(puzzle_state[USED_SEGMENTS_KEY])

    # Reject if any selected segment is already used
    if any(seg_id in used_segment_ids for seg_id in selected_ids):
        logger.info(f"Submit rejected: segments already used in puzzle {puzzle_id}")
        return jsonify({
            "status": STATUS_INVALID,
            "message": "One or more selected strands have already been used in a solved phrase.",
        }), 200

    # Verify the merge
    result = verify_merge(puzzle, selected_ids)

    if result["status"] == STATUS_OK:
        phrase_index = result["phrase_index"]
        is_complete = mark_phrase_solved(puzzle, puzzle_state, phrase_index)

        logger.info(f"Phrase solved in puzzle {puzzle_id}: {result['solved_phrase']}")

        # Return updated game state
        remaining_segments = get_remaining_segments(puzzle, set(puzzle_state[USED_SEGMENTS_KEY]))
        solved_phrases = get_solved_phrases(puzzle, puzzle_state[SOLVED_PHRASES_KEY])

        return jsonify({
            "status": STATUS_OK,
            "message": result["message"],
            "solved_phrase": result["solved_phrase"],
            "remaining_segments": remaining_segments,
            "solved": solved_phrases,
            "complete": is_complete,
        })

    # For partial or invalid, return verification result
    logger.info(f"Submit result for puzzle {puzzle_id}: {result['status']}")
    return jsonify(result)


@app.post("/api/reset")
def api_reset():
    """
    Reset the session state for a puzzle, starting it over from the beginning.
    
    JSON Payload:
        puzzle_id (str): The puzzle ID to reset.
    
    Returns:
        dict: JSON response confirming the reset.
    """
    data = request.get_json(force=True, silent=True) or {}
    puzzle_id = data.get("puzzle_id")

    if not puzzle_id:
        logger.warning("Reset request missing puzzle ID")
        return jsonify({"error": "Missing puzzle_id"}), 400

    puzzle, error = validate_puzzle_exists(puzzle_id)
    if error:
        logger.warning(f"Reset for non-existent puzzle: {puzzle_id}")
        return error

    state = get_or_init_state()
    state[puzzle_id] = {
        SOLVED_PHRASES_KEY: [],
        USED_SEGMENTS_KEY: [],
        COMPLETE_KEY: False,
    }
    session.modified = True

    logger.info(f"Puzzle reset: {puzzle_id}")
    return jsonify({"status": STATUS_OK, "message": "Puzzle reset."})


@app.get("/api/new")
def api_new():
    """
    Select a new random puzzle and initialize its state.
    
    Returns:
        dict: JSON response with the new puzzle ID.
    """
    puzzle = bank.random_puzzle()
    puzzle_state = init_puzzle_state(puzzle.id)

    logger.info(f"New puzzle selected: {puzzle.id}")
    return jsonify({"status": STATUS_OK, "id": puzzle.id})


if __name__ == "__main__":
    logger.info(f"Starting Strands game server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    app.run(debug=DEBUG_MODE, host=DEFAULT_HOST, port=DEFAULT_PORT)