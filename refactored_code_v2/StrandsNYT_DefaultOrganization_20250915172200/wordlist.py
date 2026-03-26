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


def validate_words(words: list[str]) -> tuple[list[str], list[str]]:
    """
    Validate a list of words and separate them into valid and invalid groups.
    
    Args:
        words: A list of words to validate.
        
    Returns:
        A tuple containing (valid_words, invalid_words).
    """
    valid_words = []
    invalid_words = []
    
    for word in words:
        try:
            if is_valid_word(word):
                valid_words.append(word.lower().strip())
            else:
                invalid_words.append(word.lower().strip())
        except (TypeError, AttributeError) as error:
            logger.warning(f"Error validating word '{word}': {error}")
            invalid_words.append(word)
    
    return valid_words, invalid_words


def add_words(new_words: Set[str]) -> None:
    """
    Add new words to the valid words set.
    
    Args:
        new_words: A set of words to add to the valid word list.
    """
    if not isinstance(new_words, set):
        logger.warning("new_words should be a set; converting...")
        new_words = set(new_words)
    
    # Filter words that meet minimum length requirement
    filtered_words = {word.lower() for word in new_words if len(word) >= MIN_WORD_LENGTH}
    
    added_count = len(filtered_words - VALID_WORDS)
    VALID_WORDS.update(filtered_words)
    
    logger.info(f"Added {added_count} new valid words")


def remove_words(words_to_remove: Set[str]) -> None:
    """
    Remove words from the valid words set.
    
    Args:
        words_to_remove: A set of words to remove from the valid word list.
    """
    if not isinstance(words_to_remove, set):
        logger.warning("words_to_remove should be a set; converting...")
        words_to_remove = set(words_to_remove)
    
    normalized_words = {word.lower() for word in words_to_remove}
    removed_count = len(normalized_words & VALID_WORDS)
    VALID_WORDS.difference_update(normalized_words)
    
    logger.info(f"Removed {removed_count} words")


def get_word_count() -> int:
    """
    Get the total count of valid words in the word list.
    
    Returns:
        The number of valid words.
    """
    return len(VALID_WORDS)


def get_words_by_length(target_length: int) -> Set[str]:
    """
    Retrieve all valid words of a specific length.
    
    Args:
        target_length: The desired word length.
        
    Returns:
        A set of words matching the target length.
    """
    return {word for word in VALID_WORDS if len(word) == target_length}