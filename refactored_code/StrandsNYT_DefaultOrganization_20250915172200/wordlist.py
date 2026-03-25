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
        logger.warning("Expected list of words, got %s", type(words).__name__)
        return {}
    
    validation_results = {}
    for word in words:
        try:
            validation_results[word] = is_valid_word(word)
        except (TypeError, AttributeError) as error:
            logger.error("Error validating word '%s': %s", word, error)
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
    if not isinstance(words, list):
        logger.warning("Expected list of words, got %s", type(words).__name__)
        return []
    
    valid_words_list = []
    for word in words:
        try:
            if is_valid_word(word):
                valid_words_list.append(word.lower().strip())
        except (TypeError, AttributeError) as error:
            logger.error("Error processing word '%s': %s", word, error)
    
    return valid_words_list


def add_custom_words(custom_words: Set[str]) -> None:
    """
    Add custom words to the valid words set.
    
    Args:
        custom_words: A set of words to add to the valid words collection.
        
    Raises:
        TypeError: If custom_words is not a set.
    """
    if not isinstance(custom_words, set):
        raise TypeError("custom_words must be a set")
    
    # Normalize and filter words by minimum length
    normalized_words = {
        word.lower().strip() 
        for word in custom_words 
        if len(word.strip()) >= MIN_WORD_LENGTH
    }
    
    VALID_WORDS.update(normalized_words)
    logger.info("Added %d custom words to valid words set", len(normalized_words))


def get_word_count() -> int:
    """
    Get the total count of valid words in the set.
    
    Returns:
        The number of words in the valid words set.
    """
    return len(VALID_WORDS)