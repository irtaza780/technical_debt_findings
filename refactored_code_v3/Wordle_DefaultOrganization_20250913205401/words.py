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
        True if word is a string, exactly WORD_LENGTH characters, and all alphabetic.
    """
    return isinstance(word, str) and len(word) == WORD_LENGTH and word.isalpha()


def _validate_word_list(word_list: List[str]) -> List[str]:
    """
    Validate and normalize a word list.
    
    Ensures all words are valid format (5-letter alphabetic strings) and converts
    them to lowercase. Raises ValueError if any invalid entries are found.
    
    Args:
        word_list: List of words to validate.
        
    Returns:
        List of validated, lowercased words.
        
    Raises:
        ValueError: If any words don't meet format requirements.
    """
    invalid_words = [w for w in word_list if not _is_valid_word_format(w)]
    
    if invalid_words:
        error_msg = (
            f"Word lists must contain only {WORD_LENGTH}-letter alphabetic words. "
            f"Invalid entries: {', '.join(map(str, invalid_words))}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return [w.lower() for w in word_list]


# Validate and initialize answer list
VALID_ANSWERS: List[str] = _validate_word_list(ANSWER_LIST)
assert len(VALID_ANSWERS) >= MIN_ANSWER_LIST_SIZE, "VALID_ANSWERS must not be empty."

# Initialize guesses list by combining answers with common guesses, removing duplicates
GUESSES_LIST = list(set(ANSWER_LIST + COMMON_GUESSES))
VALID_GUESSES: Set[str] = set(_validate_word_list(GUESSES_LIST))


def is_valid_guess(word: str) -> bool:
    """
    Check if a word is a valid guess in the allowed dictionary.
    
    Args:
        word: The word to validate.
        
    Returns:
        True if word is in the valid guesses set, False otherwise.
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


def _calculate_word_index(target_date: Date, base_date: Date, list_size: int) -> int:
    """
    Calculate the index into the word list for a given date.
    
    Uses modulo arithmetic to deterministically map dates to word list indices.
    Handles dates before the base date by using absolute difference.
    
    Args:
        target_date: The date to calculate the index for.
        base_date: The reference date for the calculation.
        list_size: The size of the word list to wrap around.
        
    Returns:
        An index in the range [0, list_size).
    """
    if target_date < base_date:
        # For dates before base, use absolute difference and wrap
        day_difference = abs((base_date - target_date).days)
    else:
        # For dates on or after base, use forward difference
        day_difference = (target_date - base_date).days
    
    return day_difference % list_size


def get_daily_word(target_date: Date = None) -> str:
    """
    Get the daily word for a given UTC date.
    
    Deterministically returns the same word for the same date using a fixed
    base date and modulo arithmetic. If no date is provided, uses today's UTC date.
    
    Args:
        target_date: The date to get the word for. If None, uses today's UTC date.
        
    Returns:
        A 5-letter word from the validated answer list.
    """
    if target_date is None:
        target_date = _get_utc_today()
    
    word_index = _calculate_word_index(target_date, BASE_DATE, len(VALID_ANSWERS))
    return VALID_ANSWERS[word_index]


def get_random_word() -> str:
    """
    Get a random word from the validated answer list.
    
    Returns:
        A randomly selected 5-letter word from the answer list.
    """
    return random.choice(VALID_ANSWERS)