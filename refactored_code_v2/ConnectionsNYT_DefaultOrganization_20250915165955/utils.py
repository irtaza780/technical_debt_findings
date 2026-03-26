import logging
from datetime import date
from typing import Optional

# Constants
EPOCH_DATE = date(1970, 1, 1)
ISO_DATE_FORMAT = "%Y-%m-%d"

# Configure logging
logger = logging.getLogger(__name__)


def today_date_str() -> str:
    """
    Return current local date as ISO 8601 formatted string.
    
    Returns:
        str: Current date in YYYY-MM-DD format.
    """
    return date.today().isoformat()


def days_since_epoch(target_date: date) -> int:
    """
    Calculate deterministic integer seed from a date.
    
    Computes the number of days between the given date and Unix epoch
    (January 1, 1970), providing a consistent seed value for RNG operations.
    
    Args:
        target_date: The date to calculate days from epoch for.
    
    Returns:
        int: Number of days since Unix epoch (1970-01-01).
    """
    # Calculate delta between target date and epoch for deterministic seeding
    delta = target_date - EPOCH_DATE
    return delta.days


def get_seeded_random(target_date: Optional[date] = None) -> random.Random:
    """
    Create a seeded Random instance for reproducible randomness.
    
    Generates a random.Random instance seeded by the provided date,
    enabling deterministic behavior for daily puzzles and similar
    date-dependent randomization.
    
    Args:
        target_date: Date to seed the RNG with. Defaults to today's date
                    if not provided.
    
    Returns:
        random.Random: A Random instance seeded with days since epoch.
    
    Raises:
        TypeError: If target_date is not a date instance or None.
    """
    if target_date is None:
        target_date = date.today()
    
    if not isinstance(target_date, date):
        logger.error(
            "Invalid date type provided: %s. Expected datetime.date instance.",
            type(target_date).__name__
        )
        raise TypeError(
            f"target_date must be a date instance, got {type(target_date).__name__}"
        )
    
    seed_value = days_since_epoch(target_date)
    logger.debug("Creating seeded Random instance with seed: %d", seed_value)
    return random.Random(seed_value)