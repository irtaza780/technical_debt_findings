import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import random
from datetime import date as dt_date
from category_bank import get_category_bank, CategoryDefinition
from utils import days_since_epoch

# Constants
DIFFICULTY_COLORS = {
    "yellow": "#f7da21",
    "green": "#66bb6a",
    "blue": "#42a5f5",
    "purple": "#8e24aa",
}
DIFFICULTY_ORDER = ["yellow", "green", "blue", "purple"]
WORDS_PER_CATEGORY = 4
TOTAL_WORDS = 16
MAX_GENERATION_ATTEMPTS = 1000
DEFAULT_COLOR = "#cccccc"

logger = logging.getLogger(__name__)


@dataclass
class Category:
    """Represents a single category in the puzzle."""
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
    Organize categories from the bank by their difficulty level.
    
    Args:
        bank: List of category definitions from the category bank.
        
    Returns:
        Dictionary mapping difficulty levels to lists of categories.
        
    Raises:
        ValueError: If any required difficulty level has no categories.
    """
    diff_groups: Dict[str, List[CategoryDefinition]] = {
        difficulty: [] for difficulty in DIFFICULTY_ORDER
    }
    
    for category in bank:
        difficulty_key = category.difficulty.lower()
        if difficulty_key in diff_groups:
            diff_groups[difficulty_key].append(category)
    
    # Validate that all difficulties have at least one category
    for difficulty in DIFFICULTY_ORDER:
        if not diff_groups[difficulty]:
            raise ValueError(f"No categories available for difficulty: {difficulty}")
    
    return diff_groups


def _select_one_category_per_difficulty(
    rng: random.Random,
    diff_groups: Dict[str, List[CategoryDefinition]],
) -> List[CategoryDefinition]:
    """
    Select exactly one category from each difficulty level.
    
    Args:
        rng: Seeded random number generator for deterministic selection.
        diff_groups: Dictionary of categories grouped by difficulty.
        
    Returns:
        List of four selected category definitions in difficulty order.
    """
    return [rng.choice(diff_groups[difficulty]) for difficulty in DIFFICULTY_ORDER]


def _check_word_uniqueness(
    chosen_categories: List[CategoryDefinition],
) -> tuple[bool, List[str]]:
    """
    Verify that all words across chosen categories are unique.
    
    Args:
        chosen_categories: List of selected category definitions.
        
    Returns:
        Tuple of (is_valid, words_list). is_valid is True if all words are unique.
    """
    words: List[str] = []
    seen: set = set()
    
    for category_def in chosen_categories:
        for word in category_def.words:
            if word in seen:
                return False, []
            seen.add(word)
            words.append(word)
    
    return True, words


def _build_categories_from_definitions(
    category_defs: List[CategoryDefinition],
) -> List[Category]:
    """
    Convert category definitions into Category objects with computed colors.
    
    Args:
        category_defs: List of category definitions from the bank.
        
    Returns:
        List of Category objects with colors assigned.
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
    Create a mapping from each word to its category index.
    
    Args:
        categories: List of Category objects in display order.
        
    Returns:
        Dictionary mapping word strings to category indices (0-3).
    """
    word_to_category: Dict[str, int] = {}
    for category_index, category in enumerate(categories):
        for word in category.words:
            word_to_category[word] = category_index
    return word_to_category


def generate_daily_puzzle(date: Optional[dt_date] = None) -> Puzzle:
    """
    Generate a daily puzzle deterministically based on the given date.
    
    Selects exactly one category from each difficulty level (yellow, green, blue, purple),
    ensures all 16 words are unique, and shuffles them using a seeded RNG for
    consistent daily layouts.
    
    Args:
        date: The date for which to generate the puzzle. Defaults to today.
        
    Returns:
        A Puzzle object with shuffled words and category mappings.
        
    Raises:
        ValueError: If any difficulty level has no available categories.
        RuntimeError: If a valid puzzle cannot be generated after max attempts.
    """
    if date is None:
        date = dt_date.today()
    
    # Use date as seed for deterministic but varying daily puzzles
    seed = days_since_epoch(date)
    rng = random.Random(seed)
    bank = get_category_bank()
    
    # Organize categories by difficulty
    diff_groups = _group_categories_by_difficulty(bank)
    
    # Attempt to generate a valid puzzle with unique words
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        chosen_defs = _select_one_category_per_difficulty(rng, diff_groups)
        
        # Check if all words across categories are unique
        is_valid, words = _check_word_uniqueness(chosen_defs)
        if not is_valid:
            continue
        
        # Build category objects with colors
        categories = _build_categories_from_definitions(chosen_defs)
        
        # Shuffle words deterministically using seeded RNG
        rng.shuffle(words)
        
        # Create word-to-category mapping
        word_to_category = _build_word_to_category_map(categories)
        
        logger.debug(f"Generated daily puzzle for {date} on attempt {attempt + 1}")
        return Puzzle(
            words=words,
            word_to_category=word_to_category,
            categories=categories,
        )
    
    logger.error(f"Failed to generate valid puzzle for {date} after {MAX_GENERATION_ATTEMPTS} attempts")
    raise RuntimeError(
        f"Failed to generate a valid daily puzzle after {MAX_GENERATION_ATTEMPTS} attempts."
    )