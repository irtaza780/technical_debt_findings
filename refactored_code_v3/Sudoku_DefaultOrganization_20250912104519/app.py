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
SECRET_KEY = os.environ.get("SUDOKU_SECRET_KEY", "dev-secret-key-change-me")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

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
    return [[1 if puzzle[row][col] != 0 else 0 for col in range(GRID_SIZE)] 
            for row in range(GRID_SIZE)]


def _generate_and_store_puzzle(difficulty=DEFAULT_DIFFICULTY):
    """
    Generate a new puzzle and store it in the session.
    
    Args:
        difficulty: Puzzle difficulty level (default: "medium").
    
    Returns:
        Tuple of (puzzle, solution, givens_mask).
    """
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    givens = _create_givens_mask(puzzle)
    session["puzzle"] = puzzle
    session["solution"] = solution
    session["givens"] = givens
    logger.info(f"Generated new puzzle with difficulty: {difficulty}")
    return puzzle, solution, givens


def _ensure_puzzle_in_session(difficulty=DEFAULT_DIFFICULTY):
    """
    Ensure a puzzle and its solution are present in the session.
    
    Args:
        difficulty: Puzzle difficulty level if generating new puzzle.
    
    Returns:
        Tuple of (puzzle, solution, givens_mask).
    """
    if "puzzle" not in session or "solution" not in session or "givens" not in session:
        return _generate_and_store_puzzle(difficulty)
    return session["puzzle"], session["solution"], session["givens"]


def _normalize_board_input(board):
    """
    Normalize and validate board input from client.
    
    Args:
        board: Raw board data from request.
    
    Returns:
        Tuple of (normalized_board, error_message).
        If successful, error_message is None.
    
    Raises:
        ValueError: If board format or values are invalid.
    """
    if not isinstance(board, list) or len(board) != GRID_SIZE:
        raise ValueError("Invalid board format.")
    
    if any(not isinstance(row, list) or len(row) != GRID_SIZE for row in board):
        raise ValueError("Invalid board format.")
    
    normalized = []
    for row_idx in range(GRID_SIZE):
        normalized_row = []
        for col_idx in range(GRID_SIZE):
            cell_value = board[row_idx][col_idx]
            
            # Convert empty cells to 0
            if cell_value in EMPTY_CELL_VALUES:
                normalized_row.append(0)
            else:
                try:
                    int_value = int(cell_value)
                    if int_value < MIN_CELL_VALUE or int_value > MAX_CELL_VALUE:
                        raise ValueError("Board values must be 0..9.")
                    normalized_row.append(int_value)
                except (ValueError, TypeError) as e:
                    raise ValueError("Board contains non-numeric values.") from e
        
        normalized.append(normalized_row)
    
    return normalized


def _check_givens_integrity(board, solution, givens):
    """
    Verify that given cells have not been modified.
    
    Args:
        board: Current board state.
        solution: Solution grid.
        givens: Mask of given cells.
    
    Returns:
        Tuple of (is_valid, error_cell).
        If valid, error_cell is None.
    """
    for row_idx in range(GRID_SIZE):
        for col_idx in range(GRID_SIZE):
            if givens[row_idx][col_idx] == 1 and board[row_idx][col_idx] != solution[row_idx][col_idx]:
                return False, {"row": row_idx, "col": col_idx}
    
    return True, None


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
    for row_idx in range(GRID_SIZE):
        for col_idx in range(GRID_SIZE):
            if board[row_idx][col_idx] != 0 and board[row_idx][col_idx] != solution[row_idx][col_idx]:
                incorrect.append({"row": row_idx, "col": col_idx})
    
    return incorrect


def _is_board_complete(board):
    """
    Check if the board has no empty cells.
    
    Args:
        board: Current board state.
    
    Returns:
        True if board is complete, False otherwise.
    """
    return all(board[row_idx][col_idx] != 0 
               for row_idx in range(GRID_SIZE) 
               for col_idx in range(GRID_SIZE))


def _generate_verification_message(is_complete, is_solved):
    """
    Generate appropriate message based on puzzle state.
    
    Args:
        is_complete: Whether board is completely filled.
        is_solved: Whether board matches solution exactly.
    
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
    Render the Sudoku game page with current puzzle.
    
    Returns:
        Rendered HTML template with puzzle and givens.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving index page")
    return render_template("index.html", puzzle=puzzle, givens=givens)


@app.route("/api/puzzle", methods=["POST"])
def api_puzzle():
    """
    Return the current puzzle and givens in JSON format.
    
    Returns:
        JSON response with puzzle and givens arrays.
    """
    puzzle, _, givens = _ensure_puzzle_in_session()
    logger.info("Serving current puzzle via API")
    return jsonify({"puzzle": puzzle, "givens": givens})


@app.route("/api/new", methods=["POST"])
def api_new():
    """
    Generate a new puzzle with optional difficulty level.
    
    Request JSON:
        {
            "difficulty": str (optional, default: "medium")
        }
    
    Returns:
        JSON response with new puzzle, givens, and difficulty.
    """
    request_data = request.get_json(silent=True) or {}
    difficulty = request_data.get("difficulty", DEFAULT_DIFFICULTY)
    
    puzzle, _, givens = _generate_and_store_puzzle(difficulty)
    
    return jsonify({
        "puzzle": puzzle,
        "givens": givens,
        "difficulty": difficulty
    })


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """
    Verify the submitted board against the solution.
    
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
        JSON response with verification results or error message.
    """
    if "solution" not in session or "givens" not in session:
        logger.warning("Verify request with no active puzzle")
        return jsonify({"error": "No active puzzle found."}), 400

    request_data = request.get_json(silent=True) or {}
    board = request_data.get("board")

    # Normalize and validate board input
    try:
        board = _normalize_board_input(board)
    except ValueError as e:
        logger.warning(f"Invalid board submission: {str(e)}")
        return jsonify({"error": str(e)}), 400

    solution = session["solution"]
    givens = session["givens"]

    # Check that given cells haven't been modified
    givens_valid, error_cell = _check_givens_integrity(board, solution, givens)
    if not givens_valid:
        logger.info(f"Given cell modified at {error_cell}")
        return jsonify({
            "complete": False,
            "solved": False,
            "incorrect_cells": [error_cell],
            "message": "You modified a given cell, which is not allowed."
        }), 200

    # Analyze board state
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
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)