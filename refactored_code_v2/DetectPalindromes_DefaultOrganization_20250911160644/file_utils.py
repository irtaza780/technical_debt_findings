import logging
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants for encoding detection
ENCODINGS_TEXT_MODE: List[str] = [
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "utf-32",
    "utf-32-le",
    "utf-32-be",
    "cp1252",
    "latin-1",
]

# BOM signatures for binary detection
BOM_UTF32_BE = b"\x00\x00\xfe\xff"
BOM_UTF32_LE = b"\xff\xfe\x00\x00"
BOM_UTF16_BE = b"\xfe\xff"
BOM_UTF16_LE = b"\xff\xfe"
BOM_UTF8 = b"\xef\xbb\xbf"

# Thresholds for heuristic detection
MAX_NULL_RATIO = 0.2
FALLBACK_ENCODING = "utf-8"
FALLBACK_ERRORS = "replace"


def _try_text_mode_decoding(path: str, encodings: List[str]) -> tuple[Optional[str], Optional[Exception]]:
    """
    Attempt to read file in text mode using a list of encodings.

    Args:
        path: File path to read.
        encodings: List of encoding names to try in order.

    Returns:
        Tuple of (decoded_string, last_exception). If successful, exception is None.
    """
    last_exception: Optional[Exception] = None

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as file:
                content = file.read()
                logger.debug(f"Successfully decoded {path} with {encoding}")
                return content, None
        except (UnicodeDecodeError, LookupError) as e:
            last_exception = e
            logger.debug(f"Failed to decode {path} with {encoding}: {e}")
            continue

    return None, last_exception


def _read_binary_file(path: str) -> bytes:
    """
    Read file in binary mode.

    Args:
        path: File path to read.

    Returns:
        Raw binary data.

    Raises:
        OSError: If file cannot be read.
    """
    with open(path, "rb") as file:
        return file.read()


def _detect_bom_encoding(data: bytes) -> Optional[str]:
    """
    Detect encoding from BOM (Byte Order Mark) signature.

    Args:
        data: Raw binary data.

    Returns:
        Encoding name if BOM detected, None otherwise.
    """
    bom_signatures = [
        (BOM_UTF32_BE, "utf-32-be"),
        (BOM_UTF32_LE, "utf-32-le"),
        (BOM_UTF16_BE, "utf-16-be"),
        (BOM_UTF16_LE, "utf-16-le"),
        (BOM_UTF8, "utf-8-sig"),
    ]

    for bom_bytes, encoding in bom_signatures:
        if data.startswith(bom_bytes):
            logger.debug(f"Detected BOM for {encoding}")
            return encoding

    return None


def _try_bom_decoding(data: bytes) -> Optional[str]:
    """
    Attempt to decode binary data using detected BOM.

    Args:
        data: Raw binary data.

    Returns:
        Decoded string if successful, None otherwise.
    """
    detected_encoding = _detect_bom_encoding(data)

    if detected_encoding is None:
        return None

    try:
        decoded = data.decode(detected_encoding)
        logger.debug(f"Successfully decoded using BOM-detected {detected_encoding}")
        return decoded
    except (UnicodeDecodeError, LookupError) as e:
        logger.debug(f"BOM-detected encoding {detected_encoding} failed: {e}")
        return None


def _try_utf16_with_heuristic(data: bytes) -> Optional[str]:
    """
    Attempt UTF-16 decoding with heuristic to detect mis-decoding.

    Uses null character ratio to determine if UTF-16 decoding is plausible.
    High null ratio suggests mis-decoding and fallback to UTF-8 is preferred.

    Args:
        data: Raw binary data.

    Returns:
        Decoded string if heuristic passes, None otherwise.
    """
    try:
        decoded = data.decode("utf-16", errors=FALLBACK_ERRORS)

        if not decoded:
            return None

        # Calculate ratio of null characters as indicator of mis-decoding
        null_count = decoded.count("\x00")
        null_ratio = null_count / len(decoded)

        if null_ratio <= MAX_NULL_RATIO:
            logger.debug(f"UTF-16 decoding accepted (null ratio: {null_ratio:.2%})")
            return decoded

        logger.debug(f"UTF-16 decoding rejected (null ratio: {null_ratio:.2%} exceeds {MAX_NULL_RATIO:.2%})")
        return None

    except (UnicodeDecodeError, LookupError) as e:
        logger.debug(f"UTF-16 decoding failed: {e}")
        return None


def _fallback_decode(data: bytes) -> str:
    """
    Final fallback decoding using UTF-8 with error replacement.

    This method never raises and preserves text structure by replacing
    invalid sequences with replacement character.

    Args:
        data: Raw binary data.

    Returns:
        Decoded string with invalid sequences replaced.
    """
    decoded = data.decode(FALLBACK_ENCODING, errors=FALLBACK_ERRORS)
    logger.debug(f"Using fallback {FALLBACK_ENCODING} with {FALLBACK_ERRORS} error handling")
    return decoded


def read_text_file(path: str) -> str:
    """
    Read text file with robust encoding detection and fallback strategies.

    Attempts multiple strategies in order:
    1. Text mode with common encodings (UTF-8, UTF-16, UTF-32, Windows, Latin-1)
    2. Binary read with BOM detection
    3. UTF-16 with null-character heuristic
    4. UTF-8 with error replacement (never fails)

    Args:
        path: Path to text file.

    Returns:
        Decoded file content as string.

    Raises:
        OSError: If file cannot be read in binary mode.
        UnicodeDecodeError: Only if all strategies fail (rare).
    """
    # Strategy 1: Try text mode with explicit encodings
    decoded_content, last_text_exception = _try_text_mode_decoding(path, ENCODINGS_TEXT_MODE)
    if decoded_content is not None:
        return decoded_content

    # Strategy 2: Read binary and attempt BOM detection
    try:
        binary_data = _read_binary_file(path)
    except OSError as e:
        logger.error(f"Failed to read {path} in binary mode: {e}")
        if last_text_exception:
            raise last_text_exception
        raise

    # Strategy 3: Try BOM-based decoding
    bom_decoded = _try_bom_decoding(binary_data)
    if bom_decoded is not None:
        return bom_decoded

    # Strategy 4: Try UTF-16 with heuristic
    utf16_decoded = _try_utf16_with_heuristic(binary_data)
    if utf16_decoded is not None:
        return utf16_decoded

    # Strategy 5: Final fallback to UTF-8 with replacement
    return _fallback_decode(binary_data)