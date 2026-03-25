import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY_SYMBOL = "$"
DEFAULT_FLOAT_VALUE = 0.0
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")
CURRENCY_FORMATTING_CHARS = (",", "$")


def format_currency(value: float, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> str:
    """
    Format a numeric value as a currency string.
    
    Args:
        value: The numeric value to format.
        symbol: The currency symbol to prepend (default: "$").
    
    Returns:
        A formatted currency string with the symbol, sign, and two decimal places.
        Returns "$0.00" if the value cannot be converted to float.
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert '{value}' to float, using default 0.0")
        numeric_value = DEFAULT_FLOAT_VALUE
    
    # Determine sign separately to handle negative values correctly
    sign = "-" if numeric_value < 0 else ""
    return f"{sign}{symbol}{abs(numeric_value):,.2f}"


def parse_float(text: str, default: float = DEFAULT_FLOAT_VALUE) -> float:
    """
    Parse a string value into a float, handling common currency formatting.
    
    Args:
        text: The string to parse.
        default: The default value to return if parsing fails (default: 0.0).
    
    Returns:
        The parsed float value, or the default if parsing fails or input is None/empty.
    """
    if text is None:
        return default
    
    try:
        # Remove common currency formatting characters
        cleaned_text = _remove_formatting_chars(str(text))
        
        if not cleaned_text:
            return default
        
        return float(cleaned_text)
    except ValueError:
        logger.warning(f"Could not parse '{text}' as float, using default {default}")
        return default


def _remove_formatting_chars(text: str) -> str:
    """
    Remove common currency formatting characters from a string.
    
    Args:
        text: The string to clean.
    
    Returns:
        The cleaned string with formatting characters removed and whitespace stripped.
    """
    cleaned = text.strip()
    for char in CURRENCY_FORMATTING_CHARS:
        cleaned = cleaned.replace(char, "")
    return cleaned


def parse_date(text: str, default: Optional[date] = None) -> date:
    """
    Parse a date from various string formats or date objects.
    
    Args:
        text: The date string or date object to parse.
        default: The default date to return if parsing fails (default: today's date).
    
    Returns:
        A date object parsed from the input, or the default if parsing fails.
    """
    # Handle date objects directly
    if isinstance(text, date):
        return text
    
    # Convert datetime to date
    if isinstance(text, datetime):
        return text.date()
    
    # Try parsing string formats
    if text:
        return _parse_date_string(str(text).strip(), default)
    
    return default or date.today()


def _parse_date_string(text: str, default: Optional[date] = None) -> date:
    """
    Attempt to parse a date string using supported formats.
    
    Args:
        text: The date string to parse.
        default: The default date to return if all formats fail (default: today's date).
    
    Returns:
        A date object if parsing succeeds, otherwise the default date.
    """
    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            # Try next format
            continue
    
    logger.warning(f"Could not parse date '{text}' with any supported format, using default")
    return default or date.today()


def date_to_str(date_obj: date) -> str:
    """
    Convert a date object to a formatted string.
    
    Args:
        date_obj: The date object to convert.
    
    Returns:
        A string representation of the date in YYYY-MM-DD format.
    """
    return date_obj.strftime(DEFAULT_DATE_FORMAT)