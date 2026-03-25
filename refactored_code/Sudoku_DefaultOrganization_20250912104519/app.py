import logging
import os
from flask import Flask, render_template, request, jsonify, session
from sudoku import generate_puzzle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GRID_SIZE = 9
MIN_CELL_VALUE = 0
MAX_CELL_VALUE = 9
DEFAULT_DIFFICULTY = "medium"
EMPTY_CELL_VALUES = (None, "", " ")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

app.secret_key = os.environ.get("SUDOKU_SECRET_KEY", "dev-secret-key-change-me")


def _create_givens_mask(puzzle):
    """
    Create a mask indicating which cells are given (non-zero) in the puzzle.
    
    Args:
        puzzle: 9x9 list of integers representing the puzzle grid.
        
    Returns:
        9x9 list of integers where 1 indicates a given cell, 0 indicates empty.
    """
    return [[1 if puzzle[r][c] != 0 else 0 for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]


def _store_puzzle_in_session(puzzle, solution):
    """
    Store puzzle, solution, and givens mask in the session.
    
    Args:
        puzzle: 9x9 list representing the puzzle grid.
        solution: 9x9 list representing the solved puzzle.
    """
    session["puzzle"] = puzzle
    session["solution"] = solution
    session["givens"] = _create_givens_mask(puzzle)


def _ensure_puzzle_in_session(difficulty=DEFAULT_DIFFICULTY):
    """
    Ensure a puzzle and its solution are present in the session.
    
    Args:
        difficulty: Puzzle difficulty level (default: "medium").
        
    Returns:
        Tuple of (puzzle, solution, givens_mask).
    """
    if "puzzle" not in session or "solution" not in session or "givens" not in session:
        puzzle, solution = generate_puzzle(difficulty=difficulty)
        _store_puzzle_in_session(puzzle, solution)
    
    return session["puzzle"], session["solution"], session["givens"]


def _normalize_board_value(value):
    """
    Normalize a single cell value to an integer in range [0, 9].
    
    Args:
        value: Cell value (can be int, string, None, etc.).
        
    Returns:
        Integer value in range [0, 9].
        
    Raises:
        ValueError: If value cannot be converted or is out of range.
    """
    if value in EMPTY_CELL_VALUES:
        return 0
    
    v = int(value)
    if v < MIN_CELL_VALUE or v > MAX_CELL_VALUE:
        raise ValueError(f"Board values must be {MIN_CELL_VALUE}..{MAX_CELL_VALUE}.")
    return v


def _normalize_board(board):
    """
    Validate and normalize a board to a 9x9 grid of integers [0, 9].
    
    Args:
        board: Potentially malformed board data.
        
    Returns:
        Normalized 9x9 board as list of lists.
        
    Raises:
        ValueError: If board format is invalid or contains non-numeric values.
    """
    if not isinstance(board, list) or len(board) != GRID_SIZE:
        raise ValueError("Invalid board format.")
    
    normalized = []
    for r in range(GRID_SIZE):
        if not isinstance(board[r], list) or len(board[r]) != GRID_SIZE:
            raise ValueError("Invalid board format.")
        
        row = []
        for c in range(GRID_SIZE):
            try:
                value = _normalize_board_value(board[r][c])
                row.append(value)
            except (ValueError, TypeError) as e:
                raise ValueError("Board contains non-numeric values.") from e
        
        normalized.append(row)
    
    return normalized


def _check_givens_integrity(board, solution, givens):
    """
    Verify that given cells have not been modified.
    
    Args:
        board: Current board state.
        solution: Solution grid.
        givens: Givens mask (1 = given, 0 = empty).
        
    Returns:
        Tuple of (is_valid, error_cells). error_cells is a list of dicts with
        "row" and "col" keys if invalid, empty list if valid.
    """
    error_cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if givens[r][c] == 1 and board[r][c] != solution[r][c]:
                error_cells.append({"row": r, "col": c})
    
    return len(error_cells) == 0, error_cells


def _find_incorrect_cells(board, solution):
    """
    Identify cells that don't match the solution.
    
    Args:
        board: Current board state.
        solution: Solution grid.
        
    Returns:
        List of dicts with "row" and "col" keys for incorrect cells.
    """
    incorrect = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] != 0 and board[r][c] != solution[r][c]:
                incorrect.append({"row": r, "col": c})
    return incorrect


def _is_board_complete(board):
    """
    Check if the board has no empty cells.
    
    Args:
        board: Current board state.
        
    Returns:
        True if board is complete, False otherwise.
    """
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return False
    return True


def _generate_verification_message(is_complete, is_solved):
    """
    Generate a user-friendly message based on board state.
    
    Args:
        is_complete: Whether the board is completely filled.
        is_solved: Whether the board matches the solution.
        
    Returns:
        Message string.
    """
    if is_solved:
        return "Congratulations! You solved the puzzle."
    elif is_complete:
        return "Board is complete but has mistakes. Please review highlighted cells."
    else:
        return "Progress saved. Keep going!"


@app.route("/", methods=["GET"])
def index():
    """
    Render the Sudoku game page with a puzzle.
    
    Returns:
        Rendered HTML template with puzzle and givens mask.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving index page with puzzle")
    return render_template("index.html", puzzle=puzzle, givens=givens)


@app.route("/api/puzzle", methods=["POST"])
def api_puzzle():
    """
    Return the current puzzle and givens from the session.
    
    Returns:
        JSON object with "puzzle" and "givens" keys.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving current puzzle via API")
    return jsonify({"puzzle": puzzle, "givens": givens})


@app.route("/api/new", methods=["POST"])
def api_new():
    """
    Generate a new puzzle and store it in session.
    
    Request JSON (optional):
        {"difficulty": "easy|medium|hard"}
    
    Returns:
        JSON object with "puzzle", "givens", and "difficulty" keys.
    """
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", DEFAULT_DIFFICULTY)
    
    logger.info(f"Generating new puzzle with difficulty: {difficulty}")
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    _store_puzzle_in_session(puzzle, solution)
    
    return jsonify({
        "puzzle": puzzle,
        "givens": session["givens"],
        "difficulty": difficulty
    })


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """
    Verify the current board against the solution.
    
    Request JSON:
        {"board": [[int x9] x9]}
    
    Returns:
        JSON object with:
            - complete: bool (True if no zeros on board)
            - solved: bool (True if board matches solution exactly)
            - incorrect_cells: list of {"row": r, "col": c}
            - message: str (user-friendly feedback)
    """
    if "solution" not in session or "givens" not in session:
        logger.warning("Verify request with no active puzzle")
        return jsonify({"error": "No active puzzle found."}), 400

    data = request.get_json(silent=True) or {}
    board = data.get("board")

    # Validate and normalize board
    try:
        board = _normalize_board(board)
    except ValueError as e:
        logger.warning(f"Invalid board submission: {e}")
        return jsonify({"error": str(e)}), 400

    solution = session["solution"]
    givens = session["givens"]

    # Check givens integrity
    givens_valid, error_cells = _check_givens_integrity(board, solution, givens)
    if not givens_valid:
        logger.info("User modified a given cell")
        return jsonify({
            "complete": False,
            "solved": False,
            "incorrect_cells": error_cells,
            "message": "You modified a given cell, which is not allowed."
        }), 200

    # Check board completion and correctness
    is_complete = _is_board_complete(board)
    incorrect_cells = _find_incorrect_cells(board, solution)
    is_solved = is_complete and len(incorrect_cells) == 0

    message = _generate_verification_message(is_complete, is_solved)

    if is_solved:
        logger.info("Puzzle solved successfully")

    return jsonify({
        "complete": is_complete,
        "solved": is_solved,
        "incorrect_cells": incorrect_cells,
        "message": message
    })


if __name__ == "__main__":
    logger.info(f"Starting Sudoku app on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)