import logging
import os
from flask import Flask, render_template, request, jsonify, session
from sudoku import generate_puzzle

# Constants
GRID_SIZE = 9
EMPTY_CELL = 0
MIN_CELL_VALUE = 0
MAX_CELL_VALUE = 9
DEFAULT_DIFFICULTY = "medium"
DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
EMPTY_CELL_REPRESENTATIONS = (None, "", " ")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return [
        [1 if puzzle[row][col] != EMPTY_CELL else 0 
         for col in range(GRID_SIZE)]
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
    Normalize a single cell value to an integer in range 0..9.
    
    Args:
        value: Cell value (int, string, None, or empty string).
    
    Returns:
        Integer in range 0..9.
    
    Raises:
        ValueError: If value cannot be converted to valid integer.
    """
    if value in EMPTY_CELL_REPRESENTATIONS:
        return EMPTY_CELL
    
    int_value = int(value)
    if int_value < MIN_CELL_VALUE or int_value > MAX_CELL_VALUE:
        raise ValueError(f"Value {int_value} outside valid range 0..9")
    
    return int_value


def _normalize_board(board):
    """
    Validate and normalize a board to 9x9 grid of integers 0..9.
    
    Args:
        board: Potentially unvalidated board data.
    
    Returns:
        Normalized 9x9 list of integers.
    
    Raises:
        ValueError: If board format is invalid or contains non-numeric values.
    """
    if not isinstance(board, list) or len(board) != GRID_SIZE:
        raise ValueError("Board must be a list of 9 rows")
    
    normalized = []
    for row_idx, row in enumerate(board):
        if not isinstance(row, list) or len(row) != GRID_SIZE:
            raise ValueError(f"Row {row_idx} must contain exactly 9 cells")
        
        normalized_row = []
        for col_idx, value in enumerate(row):
            try:
                normalized_row.append(_normalize_board_value(value))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Cell [{row_idx}][{col_idx}] contains invalid value: {value}"
                ) from e
        
        normalized.append(normalized_row)
    
    return normalized


def _check_givens_integrity(board, solution, givens):
    """
    Verify that given cells have not been modified.
    
    Args:
        board: Current board state.
        solution: Correct solution.
        givens: Mask indicating which cells are given.
    
    Returns:
        Tuple of (is_valid, error_cells) where error_cells is list of modified givens.
    """
    error_cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if givens[row][col] == 1 and board[row][col] != solution[row][col]:
                error_cells.append({"row": row, "col": col})
    
    return len(error_cells) == 0, error_cells


def _find_incorrect_cells(board, solution):
    """
    Identify cells that don't match the solution.
    
    Args:
        board: Current board state.
        solution: Correct solution.
    
    Returns:
        List of dicts with row and col keys for incorrect cells.
    """
    incorrect = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] != EMPTY_CELL and board[row][col] != solution[row][col]:
                incorrect.append({"row": row, "col": col})
    
    return incorrect


def _is_board_complete(board):
    """
    Check if board has no empty cells.
    
    Args:
        board: 9x9 grid of integers.
    
    Returns:
        Boolean indicating if board is complete.
    """
    return all(
        board[row][col] != EMPTY_CELL
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
    )


def _generate_verification_response(board, solution, givens):
    """
    Generate verification response for a submitted board.
    
    Args:
        board: Submitted board state.
        solution: Correct solution.
        givens: Mask of given cells.
    
    Returns:
        Dict with verification results and message.
    """
    # Check if givens were modified
    givens_valid, modified_givens = _check_givens_integrity(board, solution, givens)
    if not givens_valid:
        return {
            "complete": False,
            "solved": False,
            "incorrect_cells": modified_givens,
            "message": "You modified a given cell, which is not allowed."
        }
    
    # Check for incorrect cells and completion
    incorrect_cells = _find_incorrect_cells(board, solution)
    is_complete = _is_board_complete(board)
    is_solved = is_complete and len(incorrect_cells) == 0
    
    # Generate appropriate message
    if is_solved:
        message = "Congratulations! You solved the puzzle."
    elif is_complete:
        message = "Board is complete but has mistakes. Please review highlighted cells."
    else:
        message = "Progress saved. Keep going!"
    
    return {
        "complete": is_complete,
        "solved": is_solved,
        "incorrect_cells": incorrect_cells,
        "message": message
    }


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
        JSON response with new puzzle, givens, and difficulty.
    """
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", DEFAULT_DIFFICULTY)
    
    logger.info(f"Generating new puzzle with difficulty: {difficulty}")
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    _store_puzzle_in_session(puzzle, solution, difficulty)
    
    givens = session["givens"]
    return jsonify({"puzzle": puzzle, "givens": givens, "difficulty": difficulty})


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """
    Verify submitted board against the solution.
    
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
        logger.warning(f"Invalid board submission: {e}")
        return jsonify({"error": str(e)}), 400
    
    # Generate verification response
    solution = session["solution"]
    givens = session["givens"]
    response = _generate_verification_response(board, solution, givens)
    
    logger.info(f"Board verified - Solved: {response['solved']}, Complete: {response['complete']}")
    return jsonify(response)


if __name__ == "__main__":
    logger.info(f"Starting Sudoku app on {DEFAULT_HOST}:{DEFAULT_PORT}")
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)