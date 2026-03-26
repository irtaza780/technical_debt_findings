import logging
from typing import Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MIN_WORD_LENGTH = 4
VALID_WORDS: Set[str] = {
    # Common short words (4-7 letters)
    "soft", "ware", "wars", "sore", "rose", "rows", "soar", "toes", "tore", "tone",
    "twin", "twine", "tire", "wore", "wont", "went", "west", "wise", "wine",
    "ring", "wing", "wins", "wets", "swan", "sift", "swift", "snow", "sofa",
    "star", "start", "stare", "stew", "stow", "straw", "straws", "strawed",
    "stone", "store", "storm", "stomp", "snore", "snort",
    "snarl", "snows", "snout", "swing", "swore", "sworn",
    "python", "rust", "ruby", "kotlin", "scala", "julia", "goat",
    "coal", "cola", "goal", "goals", "golf", "gore", "gone",
    "tango", "tangoes", "tangoed", "tang", "tangy", "tilt", "tilts", "tins",
    "into", "oint", "oints", "pith", "thin", "thing", "things", "thaw", "thaws",
    "thinly", "thorn", "thorns",
    "sort", "sorts", "salt", "sail", "sails", "salsa", "silo", "silos", "siloed",
    "alto", "altar", "alter", "alert", "alerts", "alerted",
    "iron", "irons", "irony", "ions", "loin", "loins", "loan", "loans", "luna",
    "lunar", "lure", "lures", "lured", "lute", "lutes",
    "java", "perl", "lisp", "pascal",
    "tones", "tunes", "tune", "tuned", "tuner", "tug", "tugs",
    "tang", "tangs", "torn", "tore",
    "ore", "ores", "earn", "earns", "earned", "earl", "earls",
    "farm", "farms", "farmer", "farmers", "frame", "frames", "framed",
    "form", "forms", "formed", "former", "forage", "forages", "forge", "forged",
    "range", "ranges", "rang", "rangy", "rangier", "anger", "angers", "angry",
    "lion", "lions", "lioness", "loaner", "loaners", "solar",
    "soars", "soared", "softer", "soften", "softened", "softener",
    "wear", "wears", "wean", "weans", "weaned", "warn", "warns", "warned",
    "earnest", "near", "nears", "nearer", "nearest", "ear", "ears",
    "software", "warfare", "angle", "angles", "angler", "anglers",
    "orange", "oranges", "strange", "stranger", "strangers",
    "frost", "frosts", "frosted", "stones", "stoneware",
    "snare", "snares", "snared", "sinew", "sinews", "waste", "waster", "wasted",
    "wastes",
}


def is_valid_word(word: str) -> bool:
    """
    Check if a word is valid for Strands puzzle hints.
    
    A word is valid if it meets the minimum length requirement and exists
    in the valid words set.
    
    Args:
        word: The word to validate (will be converted to lowercase).
        
    Returns:
        True if the word is valid, False otherwise.
    """
    normalized_word = word.lower().strip()
    
    # Check minimum length requirement
    if len(normalized_word) < MIN_WORD_LENGTH:
        return False
    
    return normalized_word in VALID_WORDS


def validate_words(words: list[str]) -> dict[str, bool]:
    """
    Validate a list of words against the valid words set.
    
    Args:
        words: A list of words to validate.
        
    Returns:
        A dictionary mapping each word to its validation result.
    """
    if not isinstance(words, list):
        logger.warning("Input is not a list, attempting to convert")
        try:
            words = list(words)
        except TypeError as e:
            logger.error(f"Cannot convert input to list: {e}")
            return {}
    
    validation_results = {}
    for word in words:
        try:
            validation_results[word] = is_valid_word(word)
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error validating word '{word}': {e}")
            validation_results[word] = False
    
    return validation_results


def get_valid_words_from_list(words: list[str]) -> list[str]:
    """
    Filter a list of words to return only valid ones.
    
    Args:
        words: A list of words to filter.
        
    Returns:
        A list containing only the valid words.
    """
    validation_results = validate_words(words)
    return [word for word, is_valid in validation_results.items() if is_valid]


def add_word_to_dictionary(word: str) -> bool:
    """
    Add a new word to the valid words dictionary.
    
    Args:
        word: The word to add (will be converted to lowercase).
        
    Returns:
        True if the word was added, False if it already existed.
    """
    normalized_word = word.lower().strip()
    
    if len(normalized_word) < MIN_WORD_LENGTH:
        logger.warning(f"Word '{word}' is too short (minimum {MIN_WORD_LENGTH} characters)")
        return False
    
    if normalized_word in VALID_WORDS:
        logger.info(f"Word '{normalized_word}' already exists in dictionary")
        return False
    
    VALID_WORDS.add(normalized_word)
    logger.info(f"Added word '{normalized_word}' to dictionary")
    return True


def get_dictionary_stats() -> dict[str, int]:
    """
    Get statistics about the valid words dictionary.
    
    Returns:
        A dictionary containing word count and minimum word length.
    """
    return {
        "total_words": len(VALID_WORDS),
        "min_word_length": MIN_WORD_LENGTH,
    }