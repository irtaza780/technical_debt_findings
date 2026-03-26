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


def _create_yellow_categories() -> List[CategoryDefinition]:
    """Create all yellow (easiest) difficulty categories."""
    return [
        CategoryDefinition("Fruit", ["apple", "banana", "orange", "grape"], "yellow"),
        CategoryDefinition("Cardinal Numbers (1–4)", ["one", "two", "three", "four"], "yellow"),
        CategoryDefinition("Basic Units of Time", ["second", "minute", "hour", "day"], "yellow"),
        CategoryDefinition("Winter Clothing", ["coat", "scarf", "gloves", "boots"], "yellow"),
        CategoryDefinition("Sports Equipment", ["ball", "bat", "racket", "helmet"], "yellow"),
        CategoryDefinition("3D Shapes", ["cube", "sphere", "cone", "cylinder"], "yellow"),
        CategoryDefinition("Baked Goods", ["bread", "muffin", "bagel", "donut"], "yellow"),
        CategoryDefinition("Tools", ["hammer", "wrench", "pliers", "screwdriver"], "yellow"),
        CategoryDefinition("Kitchen Appliances", ["toaster", "blender", "microwave", "oven"], "yellow"),
        CategoryDefinition("Vehicles", ["car", "truck", "bicycle", "motorcycle"], "yellow"),
        CategoryDefinition("Computer Parts", ["keyboard", "mouse", "monitor", "cpu"], "yellow"),
        CategoryDefinition("Movie Genres", ["comedy", "drama", "horror", "thriller"], "yellow"),
        CategoryDefinition("Weather Events", ["rain", "snow", "thunder", "hail"], "yellow"),
    ]


def _create_green_categories() -> List[CategoryDefinition]:
    """Create all green (medium) difficulty categories."""
    return [
        CategoryDefinition("Planets", ["mercury", "venus", "earth", "mars"], "green"),
        CategoryDefinition("Quadrilaterals", ["square", "rectangle", "rhombus", "trapezoid"], "green"),
        CategoryDefinition("Programming Languages", ["python", "java", "swift", "rust"], "green"),
        CategoryDefinition("Web Protocols", ["http", "https", "ftp", "smtp"], "green"),
        CategoryDefinition("Dog Breeds", ["beagle", "poodle", "bulldog", "labrador"], "green"),
        CategoryDefinition("Musical Instruments", ["violin", "piano", "trumpet", "flute"], "green"),
        CategoryDefinition("Trees", ["oak", "pine", "maple", "birch"], "green"),
        CategoryDefinition("Birds", ["eagle", "sparrow", "robin", "pigeon"], "green"),
        CategoryDefinition("Sea Creatures", ["shark", "dolphin", "octopus", "squid"], "green"),
        CategoryDefinition("Board Games", ["chess", "checkers", "monopoly", "scrabble"], "green"),
        CategoryDefinition("Card Games", ["poker", "bridge", "hearts", "spades"], "green"),
        CategoryDefinition("File Image Extensions", ["jpg", "png", "gif", "bmp"], "green"),
        CategoryDefinition("Countries", ["china", "india", "brazil", "canada"], "green"),
        CategoryDefinition("U.S. States", ["texas", "florida", "ohio", "alaska"], "green"),
        CategoryDefinition("Tea Types", ["black", "green", "oolong", "white"], "green"),
        CategoryDefinition("Currency Units", ["dollar", "euro", "yen", "pound"], "green"),
        CategoryDefinition("Occupations", ["doctor", "teacher", "lawyer", "engineer"], "green"),
        CategoryDefinition("Zodiac Signs (set 1)", ["aries", "cancer", "libra", "virgo"], "green"),
        CategoryDefinition("Human Languages", ["english", "spanish", "french", "german"], "green"),
        CategoryDefinition("Root Vegetables", ["carrot", "beet", "radish", "turnip"], "green"),
    ]


def _create_blue_categories() -> List[CategoryDefinition]:
    """Create all blue (harder) difficulty categories."""
    return [
        CategoryDefinition("Noble Gases", ["helium", "neon", "argon", "krypton"], "blue"),
        CategoryDefinition("Metric Prefixes (small)", ["milli", "micro", "nano", "pico"], "blue"),
        CategoryDefinition("Body Organs", ["heart", "liver", "kidney", "lungs"], "blue"),
        CategoryDefinition("Bones", ["femur", "tibia", "ulna", "radius"], "blue"),
        CategoryDefinition("Math Terms", ["integral", "vector", "matrix", "scalar"], "blue"),
        CategoryDefinition("Cloud Types", ["cirrus", "cumulus", "stratus", "nimbus"], "blue"),
        CategoryDefinition("Constellations", ["orion", "leo", "taurus", "gemini"], "blue"),
        CategoryDefinition("Capital Cities", ["paris", "tokyo", "london", "cairo"], "blue"),
        CategoryDefinition("Rivers", ["nile", "amazon", "danube", "thames"], "blue"),
        CategoryDefinition("Awards (Entertainment)", ["oscar", "emmy", "tony", "grammy"], "blue"),
        CategoryDefinition("Programming Paradigms", ["object", "functional", "procedural", "declarative"], "blue"),
        CategoryDefinition("Spacecraft / Missions", ["apollo", "voyager", "soyuz", "hubble"], "blue"),
        CategoryDefinition("Precious Stones", ["diamond", "emerald", "sapphire", "topaz"], "blue"),
    ]


def _create_purple_categories() -> List[CategoryDefinition]:
    """Create all purple (trickiest) difficulty categories."""
    return [
        CategoryDefinition("Chess Pieces", ["king", "queen", "rook", "bishop"], "purple"),
        CategoryDefinition("Directions", ["north", "south", "east", "west"], "purple"),
        CategoryDefinition("Seasons", ["spring", "summer", "autumn", "winter"], "purple"),
        CategoryDefinition("Fast Synonyms", ["rapid", "quick", "brisk", "speedy"], "purple"),
        CategoryDefinition("Operating Systems", ["windows", "linux", "android", "ios"], "purple"),
        CategoryDefinition("Coffee Drinks", ["espresso", "latte", "cappuccino", "mocha"], "purple"),
        CategoryDefinition("Greek Letters", ["alpha", "beta", "gamma", "delta"], "purple"),
    ]


def _validate_word_uniqueness(categories: List[CategoryDefinition]) -> None:
    """
    Validate that all words are unique across the entire category bank.
    
    Args:
        categories: List of category definitions to validate
        
    Raises:
        ValueError: If any word appears in multiple categories
    """
    seen_words: Set[str] = set()
    
    for category in categories:
        for word in category.words:
            normalized_word = word.strip().lower()
            
            # Check for duplicate words across categories
            if normalized_word in seen_words:
                raise ValueError(
                    f"Duplicate word across category bank: '{normalized_word}' "
                    f"(found in category '{category.name}')"
                )
            seen_words.add(normalized_word)
    
    logger.info(f"Word uniqueness validation passed. Total unique words: {len(seen_words)}")


def get_category_bank() -> List[CategoryDefinition]:
    """
    Retrieve the complete curated category bank for puzzle generation.
    
    All words are lowercase, single-token where possible, and unique across 
    all categories to ensure a unique solution when mixing categories.
    
    Returns:
        List of CategoryDefinition objects organized by difficulty level
        
    Raises:
        ValueError: If word uniqueness validation fails
    """
    # Aggregate all categories by difficulty level
    all_categories = (
        _create_yellow_categories() +
        _create_green_categories() +
        _create_blue_categories() +
        _create_purple_categories()
    )
    
    # Validate word uniqueness across entire bank
    _validate_word_uniqueness(all_categories)
    
    logger.info(f"Category bank loaded with {len(all_categories)} categories")
    return all_categories