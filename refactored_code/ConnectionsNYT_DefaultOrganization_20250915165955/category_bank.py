import logging
from dataclasses import dataclass
from typing import List, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WORDS_PER_CATEGORY = 4
VALID_DIFFICULTIES = {"yellow", "green", "blue", "purple"}
MIN_DIFFICULTY_CATEGORIES = 13


@dataclass(frozen=True)
class CategoryDefinition:
    """
    Represents a single category for puzzle generation.
    
    Attributes:
        name: The category name
        words: Exactly four unique words belonging to this category
        difficulty: One of: yellow, green, blue, purple
    """
    name: str
    words: List[str]
    difficulty: str

    def __post_init__(self) -> None:
        """Validate category definition on instantiation."""
        if len(self.words) != WORDS_PER_CATEGORY:
            raise ValueError(
                f"Category '{self.name}' must have exactly {WORDS_PER_CATEGORY} words, "
                f"got {len(self.words)}"
            )
        if self.difficulty not in VALID_DIFFICULTIES:
            raise ValueError(
                f"Category '{self.name}' has invalid difficulty '{self.difficulty}'. "
                f"Must be one of: {', '.join(VALID_DIFFICULTIES)}"
            )


def _create_category(name: str, words: List[str], difficulty: str) -> CategoryDefinition:
    """
    Factory function to create a CategoryDefinition with validation.
    
    Args:
        name: The category name
        words: List of exactly four words
        difficulty: One of the valid difficulty levels
        
    Returns:
        A validated CategoryDefinition instance
        
    Raises:
        ValueError: If validation fails
    """
    return CategoryDefinition(name=name, words=words, difficulty=difficulty)


def _validate_word_uniqueness(categories: List[CategoryDefinition]) -> None:
    """
    Ensure all words are unique across the entire category bank.
    
    Args:
        categories: List of CategoryDefinition objects to validate
        
    Raises:
        ValueError: If any word appears in multiple categories
    """
    seen_words: Set[str] = set()
    
    for category in categories:
        for word in category.words:
            normalized_word = word.strip().lower()
            
            if normalized_word in seen_words:
                raise ValueError(
                    f"Duplicate word across category bank: '{normalized_word}'"
                )
            seen_words.add(normalized_word)
    
    logger.info(f"Validated {len(seen_words)} unique words across {len(categories)} categories")


def _validate_difficulty_distribution(categories: List[CategoryDefinition]) -> None:
    """
    Log the distribution of categories by difficulty level.
    
    Args:
        categories: List of CategoryDefinition objects
    """
    difficulty_counts = {difficulty: 0 for difficulty in VALID_DIFFICULTIES}
    
    for category in categories:
        difficulty_counts[category.difficulty] += 1
    
    for difficulty, count in sorted(difficulty_counts.items()):
        logger.info(f"Difficulty '{difficulty}': {count} categories")


def get_category_bank() -> List[CategoryDefinition]:
    """
    Retrieve the curated category bank for puzzle generation.
    
    All words are lowercase, single-token where possible, and unique across categories.
    Each category contains exactly four words and has a difficulty level.
    
    Returns:
        A list of validated CategoryDefinition objects
        
    Raises:
        ValueError: If validation fails (duplicate words or invalid definitions)
    """
    bank: List[CategoryDefinition] = [
        # Yellow (easiest)
        _create_category("Fruit", ["apple", "banana", "orange", "grape"], "yellow"),
        _create_category("Cardinal Numbers (1–4)", ["one", "two", "three", "four"], "yellow"),
        _create_category("Basic Units of Time", ["second", "minute", "hour", "day"], "yellow"),
        _create_category("Winter Clothing", ["coat", "scarf", "gloves", "boots"], "yellow"),
        _create_category("Sports Equipment", ["ball", "bat", "racket", "helmet"], "yellow"),
        _create_category("3D Shapes", ["cube", "sphere", "cone", "cylinder"], "yellow"),
        _create_category("Baked Goods", ["bread", "muffin", "bagel", "donut"], "yellow"),
        _create_category("Tools", ["hammer", "wrench", "pliers", "screwdriver"], "yellow"),
        _create_category("Kitchen Appliances", ["toaster", "blender", "microwave", "oven"], "yellow"),
        _create_category("Vehicles", ["car", "truck", "bicycle", "motorcycle"], "yellow"),
        _create_category("Computer Parts", ["keyboard", "mouse", "monitor", "cpu"], "yellow"),
        _create_category("Movie Genres", ["comedy", "drama", "horror", "thriller"], "yellow"),
        _create_category("Weather Events", ["rain", "snow", "thunder", "hail"], "yellow"),

        # Green (medium)
        _create_category("Planets", ["mercury", "venus", "earth", "mars"], "green"),
        _create_category("Quadrilaterals", ["square", "rectangle", "rhombus", "trapezoid"], "green"),
        _create_category("Programming Languages", ["python", "java", "swift", "rust"], "green"),
        _create_category("Web Protocols", ["http", "https", "ftp", "smtp"], "green"),
        _create_category("Dog Breeds", ["beagle", "poodle", "bulldog", "labrador"], "green"),
        _create_category("Musical Instruments", ["violin", "piano", "trumpet", "flute"], "green"),
        _create_category("Trees", ["oak", "pine", "maple", "birch"], "green"),
        _create_category("Birds", ["eagle", "sparrow", "robin", "pigeon"], "green"),
        _create_category("Sea Creatures", ["shark", "dolphin", "octopus", "squid"], "green"),
        _create_category("Board Games", ["chess", "checkers", "monopoly", "scrabble"], "green"),
        _create_category("Card Games", ["poker", "bridge", "hearts", "spades"], "green"),
        _create_category("File Image Extensions", ["jpg", "png", "gif", "bmp"], "green"),
        _create_category("Countries", ["china", "india", "brazil", "canada"], "green"),
        _create_category("U.S. States", ["texas", "florida", "ohio", "alaska"], "green"),
        _create_category("Tea Types", ["black", "green", "oolong", "white"], "green"),
        _create_category("Currency Units", ["dollar", "euro", "yen", "pound"], "green"),
        _create_category("Occupations", ["doctor", "teacher", "lawyer", "engineer"], "green"),
        _create_category("Zodiac Signs (set 1)", ["aries", "cancer", "libra", "virgo"], "green"),
        _create_category("Human Languages", ["english", "spanish", "french", "german"], "green"),
        _create_category("Root Vegetables", ["carrot", "beet", "radish", "turnip"], "green"),

        # Blue (harder)
        _create_category("Noble Gases", ["helium", "neon", "argon", "krypton"], "blue"),
        _create_category("Metric Prefixes (small)", ["milli", "micro", "nano", "pico"], "blue"),
        _create_category("Body Organs", ["heart", "liver", "kidney", "lungs"], "blue"),
        _create_category("Bones", ["femur", "tibia", "ulna", "radius"], "blue"),
        _create_category("Math Terms", ["integral", "vector", "matrix", "scalar"], "blue"),
        _create_category("Cloud Types", ["cirrus", "cumulus", "stratus", "nimbus"], "blue"),
        _create_category("Constellations", ["orion", "leo", "taurus", "gemini"], "blue"),
        _create_category("Capital Cities", ["paris", "tokyo", "london", "cairo"], "blue"),
        _create_category("Rivers", ["nile", "amazon", "danube", "thames"], "blue"),
        _create_category("Awards (Entertainment)", ["oscar", "emmy", "tony", "grammy"], "blue"),
        _create_category("Programming Paradigms", ["object", "functional", "procedural", "declarative"], "blue"),
        _create_category("Spacecraft / Missions", ["apollo", "voyager", "soyuz", "hubble"], "blue"),
        _create_category("Precious Stones", ["diamond", "emerald", "sapphire", "topaz"], "blue"),

        # Purple (trickiest)
        _create_category("Chess Pieces", ["king", "queen", "rook", "bishop"], "purple"),
        _create_category("Directions", ["north", "south", "east", "west"], "purple"),
        _create_category("Seasons", ["spring", "summer", "autumn", "winter"], "purple"),
        _create_category("Fast Synonyms", ["rapid", "quick", "brisk", "speedy"], "purple"),
        _create_category("Operating Systems", ["windows", "linux", "android", "ios"], "purple"),
        _create_category("Coffee Drinks", ["espresso", "latte", "cappuccino", "mocha"], "purple"),
        _create_category("Greek Letters", ["alpha", "beta", "gamma", "delta"], "purple"),
    ]

    # Validate the entire bank
    _validate_word_uniqueness(bank)
    _validate_difficulty_distribution(bank)
    
    return bank