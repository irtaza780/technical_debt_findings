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
        text: The string to parse (may contain commas, currency symbols, etc.).
        default: The default value to return if parsing fails.
    
    Returns:
        The parsed float value, or the default if parsing fails.
    """
    if text is None:
        return default
    
    try:
        # Remove common currency formatting characters
        cleaned_text = str(text).strip()
        for char in CURRENCY_FORMATTING_CHARS:
            cleaned_text = cleaned_text.replace(char, "")
        
        if not cleaned_text:
            return default
        
        return float(cleaned_text)
    except ValueError:
        logger.warning(f"Failed to parse '{text}' as float, using default {default}")
        return default


def parse_date(text: str, default: Optional[date] = None) -> date:
    """
    Parse a string or date-like object into a date object.
    
    Supports multiple date formats and handles datetime objects.
    If parsing fails, returns the provided default or today's date.
    
    Args:
        text: The string or date-like object to parse.
        default: The default date to return if parsing fails (default: today).
    
    Returns:
        A date object parsed from the input or the default date.
    """
    # Handle date and datetime objects directly
    if isinstance(text, date):
        return text
    
    if isinstance(text, datetime):
        return text.date()
    
    # Attempt to parse string in supported formats
    if text:
        text_str = str(text).strip()
        for date_format in SUPPORTED_DATE_FORMATS:
            try:
                return datetime.strptime(text_str, date_format).date()
            except ValueError:
                # Try next format
                continue
        
        logger.warning(f"Could not parse date '{text}' in any supported format")
    
    return default or date.today()


def date_to_str(date_obj: date) -> str:
    """
    Convert a date object to a formatted string.
    
    Args:
        date_obj: The date object to format.
    
    Returns:
        A date string in ISO format (YYYY-MM-DD).
    """
    return date_obj.strftime(DEFAULT_DATE_FORMAT)