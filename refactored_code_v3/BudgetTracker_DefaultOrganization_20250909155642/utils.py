import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY_SYMBOL = "$"
DEFAULT_FLOAT_VALUE = 0.0
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")
CURRENCY_FORMATTING_CHARS = {",", "$"}


def format_currency(value: float, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> str:
    """
    Format a numeric value as a currency string with symbol and thousands separator.
    
    Args:
        value: The numeric value to format.
        symbol: The currency symbol to prepend (default: "$").
    
    Returns:
        A formatted currency string (e.g., "-$1,234.56").
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to float, using default 0.0")
        numeric_value = DEFAULT_FLOAT_VALUE
    
    # Determine sign and work with absolute value for formatting
    sign = "-" if numeric_value < 0 else ""
    return f"{sign}{symbol}{abs(numeric_value):,.2f}"


def parse_float(text: str, default: float = DEFAULT_FLOAT_VALUE) -> float:
    """
    Parse a string value into a float, handling common currency formatting.
    
    Args:
        text: The string to parse (may contain commas, dollar signs, etc.).
        default: The value to return if parsing fails (default: 0.0).
    
    Returns:
        The parsed float value, or the default if parsing fails.
    """
    if text is None:
        return default
    
    try:
        # Remove common currency formatting characters
        cleaned_text = str(text).replace(",", "").replace("$", "").strip()
        
        if not cleaned_text:
            return default
        
        return float(cleaned_text)
    except ValueError:
        logger.warning(f"Failed to parse '{text}' as float, using default {default}")
        return default


def _try_parse_date_with_format(text: str, date_format: str) -> Optional[date]:
    """
    Attempt to parse a date string using a specific format.
    
    Args:
        text: The date string to parse.
        date_format: The strftime format string to use.
    
    Returns:
        A date object if parsing succeeds, None otherwise.
    """
    try:
        return datetime.strptime(text, date_format).date()
    except ValueError:
        return None


def parse_date(text: str, default: Optional[date] = None) -> date:
    """
    Parse a date from various input formats and types.
    
    Supports:
    - date objects (returned as-is)
    - datetime objects (converted to date)
    - strings in formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
    
    Args:
        text: The date value to parse (string, date, or datetime).
        default: The value to return if parsing fails (default: today's date).
    
    Returns:
        A date object.
    """
    # Handle date and datetime objects directly
    if isinstance(text, date) and not isinstance(text, datetime):
        return text
    
    if isinstance(text, datetime):
        return text.date()
    
    # Try parsing string representations
    if text:
        cleaned_text = str(text).strip()
        
        for date_format in SUPPORTED_DATE_FORMATS:
            parsed_date = _try_parse_date_with_format(cleaned_text, date_format)
            if parsed_date is not None:
                return parsed_date
        
        logger.warning(f"Could not parse date '{text}' with any supported format")
    
    return default or date.today()


def date_to_str(date_obj: date) -> str:
    """
    Convert a date object to an ISO 8601 formatted string.
    
    Args:
        date_obj: The date to convert.
    
    Returns:
        A string in YYYY-MM-DD format.
    """
    return date_obj.strftime(DEFAULT_DATE_FORMAT)