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


def _try_text_mode_encodings(path: str, encodings: List[str]) -> tuple[Optional[str], Optional[Exception]]:
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
                logger.debug(f"Successfully read file with encoding: {encoding}")
                return content, None
        except (UnicodeDecodeError, LookupError) as e:
            last_exception = e
            logger.debug(f"Failed to read with encoding {encoding}: {e}")
            continue

    return None, last_exception


def _read_file_binary(path: str) -> Optional[bytes]:
    """
    Read file in binary mode.

    Args:
        path: File path to read.

    Returns:
        Binary file contents, or None if read fails.
    """
    try:
        with open(path, "rb") as file:
            return file.read()
    except OSError as e:
        logger.error(f"Failed to read file in binary mode: {e}")
        return None


def _detect_bom_encoding(data: bytes) -> Optional[str]:
    """
    Detect encoding from BOM (Byte Order Mark) signature.

    Args:
        data: Binary file contents.

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
            logger.debug(f"Detected BOM for encoding: {encoding}")
            return encoding

    return None


def _try_bom_decoding(data: bytes) -> Optional[str]:
    """
    Attempt to decode binary data using detected BOM encoding.

    Args:
        data: Binary file contents.

    Returns:
        Decoded string if successful, None otherwise.
    """
    detected_encoding = _detect_bom_encoding(data)

    if detected_encoding:
        try:
            decoded = data.decode(detected_encoding)
            logger.debug(f"Successfully decoded using BOM-detected encoding: {detected_encoding}")
            return decoded
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"BOM-detected encoding {detected_encoding} failed: {e}")

    return None


def _try_utf16_with_heuristic(data: bytes) -> Optional[str]:
    """
    Attempt UTF-16 decoding with heuristic to detect mis-decoding.

    Uses null character ratio to determine if UTF-16 decoding is plausible.
    If null ratio exceeds threshold, returns None to try other methods.

    Args:
        data: Binary file contents.

    Returns:
        Decoded string if UTF-16 appears valid, None otherwise.
    """
    try:
        decoded = data.decode("utf-16", errors=FALLBACK_ERRORS)

        if decoded:
            # Calculate ratio of null characters as indicator of mis-decoding
            null_count = decoded.count("\x00")
            null_ratio = null_count / len(decoded)

            if null_ratio <= MAX_NULL_RATIO:
                logger.debug(f"UTF-16 decoding accepted (null ratio: {null_ratio:.2%})")
                return decoded

            logger.debug(f"UTF-16 decoding rejected (null ratio: {null_ratio:.2%} exceeds threshold)")

    except (UnicodeDecodeError, LookupError) as e:
        logger.debug(f"UTF-16 decoding failed: {e}")

    return None


def _fallback_utf8_decode(data: bytes) -> str:
    """
    Decode binary data using UTF-8 with replacement error handling.

    This is the final fallback that never raises an exception.

    Args:
        data: Binary file contents.

    Returns:
        Decoded string with replacement characters for invalid sequences.
    """
    decoded = data.decode(FALLBACK_ENCODING, errors=FALLBACK_ERRORS)
    logger.debug("Using UTF-8 with replacement as final fallback")
    return decoded


def read_text_file(path: str) -> str:
    """
    Read text file with robust encoding detection and fallback strategies.

    Attempts multiple strategies in order:
    1. Text mode with common encodings (UTF-8, UTF-16, UTF-32, Windows, Latin-1)
    2. Binary mode with BOM detection
    3. UTF-16 with heuristic null-character validation
    4. UTF-8 with replacement characters (never fails)

    Args:
        path: Path to the text file to read.

    Returns:
        Decoded file contents as string.

    Raises:
        UnicodeDecodeError: If all decoding strategies fail (rare).
        OSError: If file cannot be opened.
    """
    # Strategy 1: Try text mode with explicit encodings
    content, last_text_exception = _try_text_mode_encodings(path, ENCODINGS_TEXT_MODE)
    if content is not None:
        return content

    # Strategy 2: Read binary and try BOM detection
    binary_data = _read_file_binary(path)
    if binary_data is None:
        if last_text_exception:
            raise last_text_exception
        raise OSError(f"Cannot read file: {path}")

    # Strategy 3: Try BOM-detected encoding
    bom_decoded = _try_bom_decoding(binary_data)
    if bom_decoded is not None:
        return bom_decoded

    # Strategy 4: Try UTF-16 with heuristic validation
    utf16_decoded = _try_utf16_with_heuristic(binary_data)
    if utf16_decoded is not None:
        return utf16_decoded

    # Strategy 5: Final fallback to UTF-8 with replacement
    return _fallback_utf8_decode(binary_data)