import logging
import os
from flask import Flask, render_template, request, jsonify, session
from sudoku import generate_puzzle

# Configuration constants
GRID_SIZE = 9
MIN_CELL_VALUE = 0
MAX_CELL_VALUE = 9
DEFAULT_DIFFICULTY = "medium"
EMPTY_CELL_VALUES = (None, "", " ")
SECRET_KEY = os.environ.get("SUDOKU_SECRET_KEY", "dev-secret-key-change-me")
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
app.secret_key = SECRET_KEY


def _create_givens_mask(puzzle):
    """
    Create a mask indicating which cells are given (non-zero) in the puzzle.
    
    Args:
        puzzle: 9x9 list of integers representing the puzzle grid.
    
    Returns:
        9x9 list of integers where 1 indicates a given cell, 0 indicates empty.
    """
    return [[1 if puzzle[row][col] != 0 else 0 
             for col in range(GRID_SIZE)] 
            for row in range(GRID_SIZE)]


def _normalize_board(board):
    """
    Normalize and validate a board from client input.
    
    Converts empty values (None, "", " ") to 0 and validates all values are integers
    in the range [0, 9].
    
    Args:
        board: 9x9 list potentially containing mixed types.
    
    Returns:
        Normalized 9x9 list of integers, or None if validation fails.
    
    Raises:
        ValueError: If board contains non-numeric values or invalid dimensions.
        TypeError: If board structure is invalid.
    """
    if not isinstance(board, list) or len(board) != GRID_SIZE:
        raise TypeError("Board must be a list of 9 rows.")
    
    normalized = []
    for row_idx, row in enumerate(board):
        if not isinstance(row, list) or len(row) != GRID_SIZE:
            raise TypeError(f"Row {row_idx} must be a list of {GRID_SIZE} columns.")
        
        normalized_row = []
        for col_idx, cell_value in enumerate(row):
            # Convert empty values to 0
            if cell_value in EMPTY_CELL_VALUES:
                normalized_row.append(0)
            else:
                try:
                    numeric_value = int(cell_value)
                    if numeric_value < MIN_CELL_VALUE or numeric_value > MAX_CELL_VALUE:
                        raise ValueError(
                            f"Cell [{row_idx}][{col_idx}] value {numeric_value} "
                            f"must be between {MIN_CELL_VALUE} and {MAX_CELL_VALUE}."
                        )
                    normalized_row.append(numeric_value)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Cell [{row_idx}][{col_idx}] contains non-numeric value: {cell_value}"
                    ) from e
        
        normalized.append(normalized_row)
    
    return normalized


def _ensure_puzzle_in_session(difficulty=DEFAULT_DIFFICULTY):
    """
    Ensure a puzzle and its solution are present in the session.
    
    If no puzzle exists in the session, generates a new one with the specified difficulty.
    
    Args:
        difficulty: Puzzle difficulty level (default: "medium").
    
    Returns:
        Tuple of (puzzle, solution, givens_mask) where each is a 9x9 list.
    """
    if "puzzle" not in session or "solution" not in session or "givens" not in session:
        logger.info(f"Generating new puzzle with difficulty: {difficulty}")
        puzzle, solution = generate_puzzle(difficulty=difficulty)
        givens = _create_givens_mask(puzzle)
        session["puzzle"] = puzzle
        session["solution"] = solution
        session["givens"] = givens
    
    return session["puzzle"], session["solution"], session["givens"]


def _store_puzzle_in_session(puzzle, solution):
    """
    Store a puzzle and its solution in the session.
    
    Args:
        puzzle: 9x9 list representing the puzzle grid.
        solution: 9x9 list representing the solution grid.
    """
    givens = _create_givens_mask(puzzle)
    session["puzzle"] = puzzle
    session["solution"] = solution
    session["givens"] = givens


def _validate_givens_unchanged(board, solution, givens):
    """
    Validate that given cells have not been modified.
    
    Args:
        board: Current board state from client.
        solution: Solution grid from session.
        givens: Givens mask from session.
    
    Returns:
        Tuple of (is_valid, error_cell) where error_cell is {"row": r, "col": c} if invalid.
    """
    for row_idx in range(GRID_SIZE):
        for col_idx in range(GRID_SIZE):
            # Check if this is a given cell that was modified
            if givens[row_idx][col_idx] == 1 and board[row_idx][col_idx] != solution[row_idx][col_idx]:
                return False, {"row": row_idx, "col": col_idx}
    
    return True, None


def _check_board_completion(board, solution):
    """
    Check board completion and identify incorrect cells.
    
    Args:
        board: Current board state.
        solution: Solution grid.
    
    Returns:
        Tuple of (is_complete, incorrect_cells) where incorrect_cells is a list of dicts.
    """
    incorrect_cells = []
    is_complete = True
    
    for row_idx in range(GRID_SIZE):
        for col_idx in range(GRID_SIZE):
            cell_value = board[row_idx][col_idx]
            
            if cell_value == 0:
                is_complete = False
            elif cell_value != solution[row_idx][col_idx]:
                incorrect_cells.append({"row": row_idx, "col": col_idx})
    
    return is_complete, incorrect_cells


def _generate_verification_message(is_complete, incorrect_cells):
    """
    Generate a user-friendly message based on verification results.
    
    Args:
        is_complete: Whether the board is completely filled.
        incorrect_cells: List of cells with incorrect values.
    
    Returns:
        String message describing the board state.
    """
    if is_complete and not incorrect_cells:
        return "Congratulations! You solved the puzzle."
    elif is_complete:
        return "Board is complete but has mistakes. Please review highlighted cells."
    else:
        return "Progress saved. Keep going!"


@app.route("/", methods=["GET"])
def index():
    """
    Render the Sudoku game page.
    
    Ensures an active puzzle exists in the session and renders the game interface.
    The solution is not exposed to the client.
    
    Returns:
        Rendered HTML template with puzzle and givens data.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Rendering index page with active puzzle")
    return render_template("index.html", puzzle=puzzle, givens=givens)


@app.route("/api/puzzle", methods=["POST"])
def api_puzzle():
    """
    Return the current puzzle and givens from the session.
    
    Returns:
        JSON object with keys "puzzle" and "givens", each a 9x9 list.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Returning current puzzle via API")
    return jsonify({"puzzle": puzzle, "givens": givens})


@app.route("/api/new", methods=["POST"])
def api_new():
    """
    Generate a new puzzle and store it in the session.
    
    Accepts optional difficulty parameter in request JSON.
    
    Request JSON:
        {
            "difficulty": str (optional, default: "medium")
        }
    
    Returns:
        JSON object with keys "puzzle", "givens", and "difficulty".
    """
    request_data = request.get_json(silent=True) or {}
    difficulty = request_data.get("difficulty", DEFAULT_DIFFICULTY)
    
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
    
    Validates that the board format is correct, given cells are unchanged,
    and compares the board against the stored solution.
    
    Request JSON:
        {
            "board": [[int x9] x9]
        }
    
    Response JSON:
        {
            "complete": bool,
            "solved": bool,
            "incorrect_cells": [{"row": int, "col": int}, ...],
            "message": str
        }
    
    Returns:
        JSON response with verification results, or error response with 400 status.
    """
    # Check session state
    if "solution" not in session or "givens" not in session:
        logger.warning("Verify request received without active puzzle in session")
        return jsonify({"error": "No active puzzle found."}), 400
    
    # Extract and validate board from request
    request_data = request.get_json(silent=True) or {}
    board = request_data.get("board")
    
    try:
        board = _normalize_board(board)
    except (TypeError, ValueError) as e:
        logger.warning(f"Board validation failed: {e}")
        return jsonify({"error": str(e)}), 400
    
    solution = session["solution"]
    givens = session["givens"]
    
    # Validate givens are unchanged
    givens_valid, error_cell = _validate_givens_unchanged(board, solution, givens)
    if not givens_valid:
        logger.info(f"Given cell modified at {error_cell}")
        return jsonify({
            "complete": False,
            "solved": False,
            "incorrect_cells": [error_cell],
            "message": "You modified a given cell, which is not allowed."
        }), 200
    
    # Check board completion and correctness
    is_complete, incorrect_cells = _check_board_completion(board, solution)
    is_solved = is_complete and not incorrect_cells
    message = _generate_verification_message(is_complete, incorrect_cells)
    
    logger.info(f"Board verification: complete={is_complete}, solved={is_solved}")
    
    return jsonify({
        "complete": is_complete,
        "solved": is_solved,
        "incorrect_cells": incorrect_cells,
        "message": message
    })


if __name__ == "__main__":
    logger.info(f"Starting Sudoku app on {SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)