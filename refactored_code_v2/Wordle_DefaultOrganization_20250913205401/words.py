import logging
import random
from datetime import date as Date, datetime, timezone
from typing import List, Set

# Configure logging
logger = logging.getLogger(__name__)

# Constants
WORD_LENGTH = 5
BASE_DATE = Date(2021, 6, 19)
MIN_ANSWER_LIST_SIZE = 1

# A modest curated list of 5-letter English words for daily answers.
ANSWER_LIST = [
    "apple", "brave", "crane", "delta", "eagle", "flame", "grape", "honey", "ivory", "joker",
    "kneel", "lemon", "mango", "noble", "ocean", "piano", "queen", "roast", "sunny", "tiger",
    "ultra", "vigor", "whale", "xenon", "yacht", "zesty", "adore", "bloom", "cider", "dolly",
    "ember", "fancy", "glove", "hazel", "irony", "jelly", "kitty", "lunar", "mirth", "nylon",
    "optic", "pride", "quilt", "rally", "salsa", "tease", "unite", "vivid", "waltz", "xylem",
    "yodel", "zebra", "angel", "bison", "chess", "dwell", "elite", "forgo", "gamma", "hippo",
    "inert", "jaunt", "karma", "linen", "metal", "nicer", "omega", "parer", "quake", "riper",
    "solar", "table", "unfed", "voter", "woven", "xerox", "yearn", "zonal", "aloft", "blaze",
    "canny", "drape", "expel", "femur", "gaily", "hoist", "ingot", "jolly", "knack", "lodge",
    "moult", "naiad", "ounce", "pleat", "radii", "sleet", "theta", "udder", "vaunt", "worry",
    "wreak", "wrung", "yeast", "zippy"
]

# Common 5-letter English words allowed as guesses
COMMON_GUESSES = [
    "about", "other", "which", "their", "there", "would", "could", "these", "those", "where",
    "after", "again", "below", "every", "first", "great", "house", "large", "never", "place",
    "small", "sound", "still", "thing", "think", "three", "world", "young", "right", "light",
    "point", "water", "story", "money", "heart", "music", "human", "laugh", "rough", "tough",
    "sugar", "spice", "sweet", "salty", "bread", "cheer", "grill", "grind", "spoon", "knife",
    "spike", "pride", "glory", "sleet", "storm", "cloud", "winds", "sunny", "rainy", "snowy",
    "zesty", "amber", "beach", "cabin", "drift", "flint", "gleam", "hover", "ivies", "jokes",
    "knees", "leapt", "mirth", "novel", "oasis", "punch", "quart", "rhyme", "sugar", "tulip",
    "udder", "vocal", "whirl", "xenon", "youth", "zebra"
]


def _is_valid_word_format(word: str) -> bool:
    """
    Check if a word meets the format requirements for Wordle words.
    
    Args:
        word: The word to validate.
        
    Returns:
        True if the word is a string, has exactly WORD_LENGTH characters, and contains only letters.
    """
    return isinstance(word, str) and len(word) == WORD_LENGTH and word.isalpha()


def _validate_word_list(word_list: List[str]) -> List[str]:
    """
    Validate and normalize a word list.
    
    Ensures all words meet format requirements and converts them to lowercase.
    Raises ValueError if any invalid entries are found.
    
    Args:
        word_list: List of words to validate.
        
    Returns:
        List of validated, lowercase words.
        
    Raises:
        ValueError: If any words do not meet format requirements.
    """
    invalid_words = [word for word in word_list if not _is_valid_word_format(word)]
    
    if invalid_words:
        error_message = (
            f"Word lists must contain only {WORD_LENGTH}-letter alphabetic words. "
            f"Invalid entries: {', '.join(map(str, invalid_words))}"
        )
        logger.error(error_message)
        raise ValueError(error_message)
    
    return [word.lower() for word in word_list]


# Initialize and validate word lists
VALID_ANSWERS: List[str] = _validate_word_list(ANSWER_LIST)
assert len(VALID_ANSWERS) >= MIN_ANSWER_LIST_SIZE, "VALID_ANSWERS must not be empty."

# Combine answers with common guesses, removing duplicates
GUESSES_LIST = list(set(ANSWER_LIST + COMMON_GUESSES))
VALID_GUESSES: Set[str] = set(_validate_word_list(GUESSES_LIST))

logger.info(f"Loaded {len(VALID_ANSWERS)} valid answers and {len(VALID_GUESSES)} valid guesses.")


def is_valid_guess(word: str) -> bool:
    """
    Check if a word is a valid guess.
    
    Performs a fast O(1) dictionary membership check against the allowed guesses set.
    
    Args:
        word: The word to validate.
        
    Returns:
        True if the word is in the valid guesses set, False otherwise.
    """
    if not isinstance(word, str):
        return False
    return word.lower() in VALID_GUESSES


def _get_utc_today() -> Date:
    """
    Get today's date in UTC timezone.
    
    Returns:
        Today's date as a Date object in UTC.
    """
    return datetime.now(timezone.utc).date()


def _calculate_word_index(target_date: Date, answer_list: List[str]) -> int:
    """
    Calculate the index into the answer list for a given date.
    
    Uses a deterministic algorithm based on the difference between the target date
    and the base date to ensure the same date always returns the same word.
    
    Args:
        target_date: The date to calculate the index for.
        answer_list: The list of answers to index into.
        
    Returns:
        An index within the valid range of the answer list.
    """
    # Calculate days difference from base date
    if target_date < BASE_DATE:
        # If before base, use absolute difference and wrap
        day_offset = abs((BASE_DATE - target_date).days)
    else:
        # If on or after base, use positive difference
        day_offset = (target_date - BASE_DATE).days
    
    # Use modulo to wrap around the answer list
    return day_offset % len(answer_list)


def get_daily_word(target_date: Date = None) -> str:
    """
    Get the daily word for a given UTC date.
    
    Returns a deterministic word based on the date, ensuring the same date
    always returns the same word. If no date is provided, uses today's UTC date.
    
    Args:
        target_date: The date to get the word for. Defaults to today's UTC date.
        
    Returns:
        A 5-letter word from the validated answer list.
    """
    if target_date is None:
        target_date = _get_utc_today()
    
    index = _calculate_word_index(target_date, VALID_ANSWERS)
    return VALID_ANSWERS[index]


def get_random_word() -> str:
    """
    Get a random word from the validated answer list.
    
    Returns:
        A randomly selected 5-letter word from the answer list.
    """
    return random.choice(VALID_ANSWERS)