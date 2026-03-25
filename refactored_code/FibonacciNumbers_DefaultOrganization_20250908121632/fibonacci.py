import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
MIN_VALID_LIMIT = 0
DEFAULT_SEPARATOR = ", "
EMPTY_SEQUENCE_STATS = {"count": 0, "max": 0, "sum": 0}


def parse_limit(text: str) -> int:
    """
    Parse and validate the limit input as a non-negative integer.

    Args:
        text: Input string from the user.

    Returns:
        A non-negative integer representing the upper bound (inclusive).

    Raises:
        ValueError: If the input is empty, not an integer, or negative.
    """
    trimmed_input = (text or "").strip()
    
    if not trimmed_input:
        raise ValueError("Please enter a non-negative integer.")
    
    try:
        parsed_value = int(trimmed_input, 10)
    except (TypeError, ValueError) as e:
        raise ValueError("Invalid number. Enter a whole number like 0, 10, 12345.") from e
    
    if parsed_value < MIN_VALID_LIMIT:
        raise ValueError("The number must be non-negative (>= 0).")
    
    return parsed_value


def generate_fibonacci_up_to(limit: int) -> List[int]:
    """
    Generate Fibonacci numbers up to and including the given limit.

    The sequence starts with 0 and 1: 0, 1, 1, 2, 3, 5, ...

    Args:
        limit: Non-negative integer specifying the inclusive upper bound.

    Returns:
        A list of Fibonacci numbers n where n <= limit.

    Raises:
        ValueError: If limit is negative.
    """
    if limit < MIN_VALID_LIMIT:
        raise ValueError("Limit must be non-negative.")
    
    fibonacci_sequence: List[int] = []
    current, next_value = 0, 1
    
    # Generate Fibonacci numbers iteratively until exceeding limit
    while current <= limit:
        fibonacci_sequence.append(current)
        current, next_value = next_value, current + next_value
    
    return fibonacci_sequence


def format_sequence(seq: List[int], separator: str = DEFAULT_SEPARATOR) -> str:
    """
    Format a sequence of integers into a string.

    Args:
        seq: List of integers.
        separator: String used to separate numbers. Defaults to ", ".

    Returns:
        A single string with numbers joined by the separator.
    """
    return separator.join(str(number) for number in seq)


def sequence_stats(seq: List[int]) -> Dict[str, int]:
    """
    Compute basic statistics for a sequence of integers.

    Args:
        seq: List of integers.

    Returns:
        A dict with keys: 'count', 'max', 'sum'.
        For an empty list, count is 0, max is 0, sum is 0.
    """
    if not seq:
        return EMPTY_SEQUENCE_STATS.copy()
    
    return {
        "count": len(seq),
        "max": max(seq),
        "sum": sum(seq)
    }