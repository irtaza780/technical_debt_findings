import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import random
from datetime import date as dt_date
from category_bank import get_category_bank, CategoryDefinition
from utils import days_since_epoch

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DIFFICULTY_COLORS = {
    "yellow": "#f7da21",
    "green": "#66bb6a",
    "blue": "#42a5f5",
    "purple": "#8e24aa",
}
DEFAULT_COLOR = "#cccccc"
DIFFICULTIES = ("yellow", "green", "blue", "purple")
MAX_GENERATION_ATTEMPTS = 1000
WORDS_PER_PUZZLE = 16


@dataclass
class Category:
    """Represents a category with words and difficulty level."""
    name: str
    words: List[str]
    difficulty: str
    color: str


@dataclass
class Puzzle:
    """Represents a complete puzzle with shuffled words and category mappings."""
    words: List[str]
    word_to_category: Dict[str, int]
    categories: List[Category]


def get_color_for_difficulty(difficulty: str) -> str:
    """
    Get the hex color code for a given difficulty level.
    
    Args:
        difficulty: The difficulty level (yellow, green, blue, purple).
        
    Returns:
        The hex color code as a string.
    """
    return DIFFICULTY_COLORS.get(difficulty.lower(), DEFAULT_COLOR)


def _group_categories_by_difficulty(
    bank: List[CategoryDefinition],
) -> Dict[str, List[CategoryDefinition]]:
    """
    Group categories from the bank by their difficulty level.
    
    Args:
        bank: List of category definitions from the category bank.
        
    Returns:
        Dictionary mapping difficulty levels to lists of categories.
        
    Raises:
        ValueError: If any required difficulty level has no categories.
    """
    diff_groups: Dict[str, List[CategoryDefinition]] = {
        difficulty: [] for difficulty in DIFFICULTIES
    }
    
    for category in bank:
        key = category.difficulty.lower()
        if key in diff_groups:
            diff_groups[key].append(category)
    
    # Validate that all difficulties have at least one category
    for difficulty in DIFFICULTIES:
        if not diff_groups[difficulty]:
            raise ValueError(f"No categories available for difficulty: {difficulty}")
    
    return diff_groups


def _select_one_category_per_difficulty(
    diff_groups: Dict[str, List[CategoryDefinition]],
    rng: random.Random,
) -> List[CategoryDefinition]:
    """
    Select exactly one category from each difficulty level.
    
    Args:
        diff_groups: Dictionary mapping difficulties to category lists.
        rng: Seeded random number generator for deterministic selection.
        
    Returns:
        List of four selected categories in order [yellow, green, blue, purple].
    """
    return [rng.choice(diff_groups[difficulty]) for difficulty in DIFFICULTIES]


def _validate_word_uniqueness(
    chosen_categories: List[CategoryDefinition],
) -> tuple[bool, List[str]]:
    """
    Validate that all words across chosen categories are unique.
    
    Args:
        chosen_categories: List of selected category definitions.
        
    Returns:
        Tuple of (is_valid, words_list). If valid, words_list contains all words.
        If invalid, words_list is empty.
    """
    words: List[str] = []
    seen: set = set()
    
    for category in chosen_categories:
        for word in category.words:
            if word in seen:
                return False, []
            seen.add(word)
            words.append(word)
    
    return True, words


def _build_categories_from_definitions(
    category_defs: List[CategoryDefinition],
) -> List[Category]:
    """
    Convert category definitions to Category objects with computed colors.
    
    Args:
        category_defs: List of category definitions from the bank.
        
    Returns:
        List of Category objects in the same order as input.
    """
    return [
        Category(
            name=cat_def.name,
            words=list(cat_def.words),
            difficulty=cat_def.difficulty,
            color=get_color_for_difficulty(cat_def.difficulty),
        )
        for cat_def in category_defs
    ]


def _build_word_to_category_map(categories: List[Category]) -> Dict[str, int]:
    """
    Build a mapping from each word to its category index.
    
    Args:
        categories: List of Category objects.
        
    Returns:
        Dictionary mapping word strings to category indices (0-3).
    """
    word_to_category: Dict[str, int] = {}
    for category_idx, category in enumerate(categories):
        for word in category.words:
            word_to_category[word] = category_idx
    return word_to_category


def generate_daily_puzzle(date: Optional[dt_date] = None) -> Puzzle:
    """
    Generate a daily puzzle deterministically based on the given date.
    
    Selects exactly one category from each difficulty level (yellow, green, blue,
    purple), ensures all 16 words are unique, and shuffles them using a seeded
    random number generator for consistent daily layouts.
    
    Args:
        date: The date for which to generate the puzzle. Defaults to today.
        
    Returns:
        A Puzzle object containing shuffled words and category mappings.
        
    Raises:
        ValueError: If any difficulty level has no available categories.
        RuntimeError: If a valid puzzle cannot be generated after max attempts.
    """
    if date is None:
        date = dt_date.today()
    
    seed = days_since_epoch(date)
    rng = random.Random(seed)
    bank = get_category_bank()
    
    # Group categories by difficulty and validate availability
    diff_groups = _group_categories_by_difficulty(bank)
    
    # Attempt to generate a valid puzzle with unique words
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        chosen_defs = _select_one_category_per_difficulty(diff_groups, rng)
        
        # Validate word uniqueness across selected categories
        is_valid, words = _validate_word_uniqueness(chosen_defs)
        if not is_valid:
            continue
        
        # Build category objects with colors
        categories = _build_categories_from_definitions(chosen_defs)
        
        # Shuffle words deterministically using seeded RNG
        rng.shuffle(words)
        
        # Build word-to-category mapping
        word_to_category = _build_word_to_category_map(categories)
        
        logger.debug(
            f"Generated daily puzzle for {date} on attempt {attempt + 1}"
        )
        return Puzzle(
            words=words,
            word_to_category=word_to_category,
            categories=categories,
        )
    
    logger.error(
        f"Failed to generate valid puzzle for {date} after "
        f"{MAX_GENERATION_ATTEMPTS} attempts"
    )
    raise RuntimeError(
        f"Failed to generate a valid daily puzzle after {MAX_GENERATION_ATTEMPTS} "
        "attempts."
    )