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
        9x9 list of integers where 1 indicates a given cell, 0 otherwise.
    """
    return [
        [1 if puzzle[row][col] != 0 else 0 for col in range(GRID_SIZE)]
        for row in range(GRID_SIZE)
    ]


def _store_puzzle_in_session(puzzle, solution, difficulty):
    """
    Store puzzle, solution, and givens mask in the session.
    
    Args:
        puzzle: 9x9 list representing the puzzle grid.
        solution: 9x9 list representing the solved puzzle.
        difficulty: String indicating puzzle difficulty level.
    """
    givens = _create_givens_mask(puzzle)
    session["puzzle"] = puzzle
    session["solution"] = solution
    session["givens"] = givens
    session["difficulty"] = difficulty
    logger.info(f"Puzzle stored in session with difficulty: {difficulty}")


def _ensure_puzzle_in_session(difficulty=DEFAULT_DIFFICULTY):
    """
    Ensure a puzzle and its solution are present in the session.
    
    Args:
        difficulty: String indicating desired puzzle difficulty level.
        
    Returns:
        Tuple of (puzzle, solution, givens_mask) from session.
    """
    if "puzzle" not in session or "solution" not in session or "givens" not in session:
        logger.info(f"Generating new puzzle with difficulty: {difficulty}")
        puzzle, solution = generate_puzzle(difficulty=difficulty)
        _store_puzzle_in_session(puzzle, solution, difficulty)
    
    return session["puzzle"], session["solution"], session["givens"]


def _normalize_board_value(value):
    """
    Normalize a single cell value to an integer in range [0, 9].
    
    Args:
        value: Cell value (int, string, None, or empty string).
        
    Returns:
        Integer in range [0, 9].
        
    Raises:
        ValueError: If value cannot be converted to valid integer.
    """
    if value in EMPTY_CELL_VALUES:
        return 0
    
    try:
        int_value = int(value)
        if int_value < MIN_CELL_VALUE or int_value > MAX_CELL_VALUE:
            raise ValueError(f"Value {int_value} out of range [0, 9]")
        return int_value
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to normalize board value: {value}, error: {e}")
        raise ValueError(f"Invalid board value: {value}") from e


def _normalize_board(board):
    """
    Normalize all board values to integers in range [0, 9].
    
    Args:
        board: 9x9 list of cell values.
        
    Returns:
        9x9 list of normalized integers.
        
    Raises:
        ValueError: If board format is invalid or contains non-numeric values.
    """
    if not isinstance(board, list) or len(board) != GRID_SIZE:
        raise ValueError("Board must be a list of 9 rows")
    
    normalized = []
    for row_idx, row in enumerate(board):
        if not isinstance(row, list) or len(row) != GRID_SIZE:
            raise ValueError(f"Row {row_idx} must be a list of {GRID_SIZE} columns")
        
        normalized_row = []
        for col_idx, value in enumerate(row):
            try:
                normalized_row.append(_normalize_board_value(value))
            except ValueError as e:
                logger.warning(f"Invalid value at [{row_idx}][{col_idx}]: {value}")
                raise ValueError(f"Invalid value at [{row_idx}][{col_idx}]: {value}") from e
        
        normalized.append(normalized_row)
    
    return normalized


def _check_givens_integrity(board, givens, solution):
    """
    Verify that given cells have not been modified.
    
    Args:
        board: 9x9 list of current board values.
        givens: 9x9 mask indicating given cells.
        solution: 9x9 list of correct solution.
        
    Returns:
        Tuple of (is_valid, error_cell) where error_cell is None if valid,
        or a dict with row/col if a given was modified.
    """
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if givens[row][col] == 1 and board[row][col] != solution[row][col]:
                logger.warning(f"Given cell modified at [{row}][{col}]")
                return False, {"row": row, "col": col}
    
    return True, None


def _find_incorrect_cells(board, solution):
    """
    Identify cells that don't match the solution.
    
    Args:
        board: 9x9 list of current board values.
        solution: 9x9 list of correct solution.
        
    Returns:
        List of dicts with row/col for each incorrect cell.
    """
    incorrect = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] != 0 and board[row][col] != solution[row][col]:
                incorrect.append({"row": row, "col": col})
    
    return incorrect


def _check_board_completion(board):
    """
    Check if board is completely filled (no empty cells).
    
    Args:
        board: 9x9 list of board values.
        
    Returns:
        Boolean indicating if board is complete.
    """
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] == 0:
                return False
    
    return True


def _generate_verification_message(is_complete, is_solved):
    """
    Generate appropriate message based on board state.
    
    Args:
        is_complete: Boolean indicating if board is fully filled.
        is_solved: Boolean indicating if board matches solution.
        
    Returns:
        String message for the user.
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
    Render the Sudoku game page with current puzzle.
    
    Returns:
        Rendered HTML template with puzzle and givens mask.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving index page")
    return render_template("index.html", puzzle=puzzle, givens=givens)


@app.route("/api/puzzle", methods=["POST"])
def api_puzzle():
    """
    Return the current puzzle and givens from session.
    
    Returns:
        JSON response with puzzle and givens mask.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving current puzzle via API")
    return jsonify({"puzzle": puzzle, "givens": givens})


@app.route("/api/new", methods=["POST"])
def api_new():
    """
    Generate a new puzzle with specified difficulty.
    
    Request JSON (optional):
        {"difficulty": "easy|medium|hard"}
    
    Returns:
        JSON response with new puzzle, givens mask, and difficulty.
    """
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", DEFAULT_DIFFICULTY)
    
    logger.info(f"Generating new puzzle with difficulty: {difficulty}")
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    _store_puzzle_in_session(puzzle, solution, difficulty)
    
    return jsonify({
        "puzzle": puzzle,
        "givens": session["givens"],
        "difficulty": difficulty
    })


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """
    Verify the submitted board against the solution.
    
    Request JSON:
        {"board": [[int x9] x9]}
    
    Returns:
        JSON response with verification results:
        {
            "complete": bool,
            "solved": bool,
            "incorrect_cells": [{"row": int, "col": int}, ...],
            "message": str
        }
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
        logger.warning(f"Board validation failed: {e}")
        return jsonify({"error": str(e)}), 400

    solution = session["solution"]
    givens = session["givens"]

    # Check that givens haven't been modified
    givens_valid, error_cell = _check_givens_integrity(board, givens, solution)
    if not givens_valid:
        logger.info(f"Given cell modified at {error_cell}")
        return jsonify({
            "complete": False,
            "solved": False,
            "incorrect_cells": [error_cell],
            "message": "You modified a given cell, which is not allowed."
        }), 200

    # Check board completion and correctness
    is_complete = _check_board_completion(board)
    incorrect_cells = _find_incorrect_cells(board, solution)
    is_solved = is_complete and len(incorrect_cells) == 0

    message = _generate_verification_message(is_complete, is_solved)

    logger.info(f"Board verification: complete={is_complete}, solved={is_solved}")

    return jsonify({
        "complete": is_complete,
        "solved": is_solved,
        "incorrect_cells": incorrect_cells,
        "message": message
    })


if __name__ == "__main__":
    logger.info(f"Starting Sudoku app on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)