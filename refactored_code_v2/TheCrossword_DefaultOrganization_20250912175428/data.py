import logging

logger = logging.getLogger(__name__)

# Grid dimensions and puzzle metadata
GRID_SIZE = 5
PUZZLE_NAME = "Sator Square Mini (5x5)"

# Solution grid for the Sator Square puzzle
SOLUTION_ROWS = [
    "SATOR",
    "AREPO",
    "TENET",
    "OPERA",
    "ROTAS",
]

# Across clues indexed by clue number
ACROSS_CLUES_BY_NUMBER = {
    1: 'Latin "sower"; starts the famous square',
    6: "Mysterious name from the Sator square",
    7: "Belief or principle",
    8: "Stage works set to music",
    9: "Wheels, in Latin",
}

# Down clues indexed by clue number
DOWN_CLUES_BY_NUMBER = {
    1: "Starts the Latin word square",
    2: "Name found in the palindromic Latin square",
    3: "Doctrine",
    4: "Grand musical works",
    5: "Rotating things, in Latin",
}

# Legacy fallback: across clues indexed by answer text
ACROSS_CLUES_BY_ANSWER = {
    "SATOR": 'Latin "sower"; starts the famous square',
    "AREPO": "Mysterious name from the Sator square",
    "TENET": "Belief or principle",
    "OPERA": "Stage works set to music",
    "ROTAS": "Wheels, in Latin",
}

# Legacy fallback: down clues indexed by answer text
DOWN_CLUES_BY_ANSWER = {
    "SATOR": "Starts the Latin word square",
    "AREPO": "Name found in the palindromic Latin square",
    "TENET": "Doctrine",
    "OPERA": "Grand musical works",
    "ROTAS": "Rotating things, in Latin",
}


def get_puzzle():
    """
    Retrieve the Sator Square crossword puzzle dataset.

    Returns a dictionary containing the complete puzzle definition including
    the solution grid and clues indexed both by clue number (preferred) and
    by answer text (legacy fallback).

    The Sator Square is a famous 5x5 word square with perfect symmetry:
    each across word matches the corresponding down word, creating a
    palindromic structure.

    Returns:
        dict: A dictionary with the following keys:
            - name (str): The puzzle title
            - solution_rows (list): List of 5 strings representing each row
            - across_clues_by_number (dict): Across clues keyed by clue number
            - down_clues_by_number (dict): Down clues keyed by clue number
            - across_clues_by_answer (dict): Across clues keyed by answer text
            - down_clues_by_answer (dict): Down clues keyed by answer text
    """
    puzzle_data = {
        "name": PUZZLE_NAME,
        "solution_rows": SOLUTION_ROWS,
        "across_clues_by_number": ACROSS_CLUES_BY_NUMBER,
        "down_clues_by_number": DOWN_CLUES_BY_NUMBER,
        "across_clues_by_answer": ACROSS_CLUES_BY_ANSWER,
        "down_clues_by_answer": DOWN_CLUES_BY_ANSWER,
    }

    logger.debug("Loaded puzzle: %s", PUZZLE_NAME)
    return puzzle_data