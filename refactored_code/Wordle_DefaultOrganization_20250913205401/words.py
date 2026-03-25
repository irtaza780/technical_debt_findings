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
    Check if a word meets the format requirements for Wordle.
    
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
        error_message = (
            f"Word lists must contain only {WORD_LENGTH}-letter alphabetic words. "
            f"Invalid entries: {', '.join(map(str, invalid_words))}"
        )
        logger.error(error_message)
        raise ValueError(error_message)
    
    return [w.lower() for w in word_list]


# Validate and initialize answer list
VALID_ANSWERS: List[str] = _validate_word_list(ANSWER_LIST)
assert len(VALID_ANSWERS) >= MIN_ANSWER_LIST_SIZE, "VALID_ANSWERS must not be empty."

# Initialize guesses list by combining answers and common guesses, removing duplicates
GUESSES_LIST = list(set(ANSWER_LIST + COMMON_GUESSES))
VALID_GUESSES: Set[str] = set(_validate_word_list(GUESSES_LIST))


def is_valid_guess(word: str) -> bool:
    """
    Check if a word is a valid guess in the game.
    
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


def _calculate_word_index(target_date: Date, answers: List[str]) -> int:
    """
    Calculate the index into the answers list for a given date.
    
    Uses a deterministic algorithm based on days offset from BASE_DATE to ensure
    the same date always returns the same word.
    
    Args:
        target_date: The date to calculate the index for.
        answers: The list of possible answer words.
        
    Returns:
        An index into the answers list.
    """
    # Handle dates before base date by wrapping forward
    if target_date < BASE_DATE:
        day_difference = abs((BASE_DATE - target_date).days)
        return day_difference % len(answers)
    
    # For dates on or after base date, calculate offset
    day_offset = (target_date - BASE_DATE).days
    return day_offset % len(answers)


def get_daily_word(target_date: Date = None) -> str:
    """
    Get the daily word for a specific date using deterministic selection.
    
    Returns the same word for the same date every time. If no date is provided,
    uses today's UTC date. The word is selected from VALID_ANSWERS using a
    deterministic algorithm based on the date offset from BASE_DATE.
    
    Args:
        target_date: The date to get the word for. If None, uses today's UTC date.
        
    Returns:
        A 5-letter word from VALID_ANSWERS.
    """
    if target_date is None:
        target_date = _get_utc_today()
    
    word_index = _calculate_word_index(target_date, VALID_ANSWERS)
    return VALID_ANSWERS[word_index]


def get_random_word() -> str:
    """
    Get a random word from the validated answer list.
    
    Returns:
        A randomly selected 5-letter word from VALID_ANSWERS.
    """
    return random.choice(VALID_ANSWERS)