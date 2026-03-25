import logging
from dataclasses import dataclass
from typing import List, Iterator, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MIN_LENGTH = 3
SENTENCE_TERMINATORS = ".!?"
SENTENCE_TRAILING_CHARS = ')"\']'


@dataclass
class DetectionOptions:
    """Options for controlling what to detect and how to normalize."""
    check_words: bool = True
    check_sentences: bool = True
    check_lines: bool = True
    min_length: int = DEFAULT_MIN_LENGTH
    ignore_case: bool = True
    ignore_non_alnum: bool = True


@dataclass
class PalindromeMatch:
    """
    A single palindrome detection result.
    
    Attributes:
        category: Type of palindrome ('word', 'sentence', or 'line')
        text: Original substring as it appears in the file
        normalized: Normalized text used for palindrome check
        length: Length of normalized text
        line_no: 1-based line number (Tk Text indexing)
        start_pos: 0-based column start in the line
        end_pos: 0-based column end (exclusive) in the line
    """
    category: str
    text: str
    normalized: str
    length: int
    line_no: int
    start_pos: int
    end_pos: int


def _normalize(s: str, ignore_case: bool, ignore_non_alnum: bool) -> str:
    """
    Normalize text according to options.
    
    Args:
        s: String to normalize
        ignore_case: If True, convert to lowercase
        ignore_non_alnum: If True, remove non-alphanumeric characters
        
    Returns:
        Normalized string
    """
    if ignore_non_alnum:
        s = "".join(ch for ch in s if ch.isalnum())
    if ignore_case:
        s = s.casefold()
    return s


def _is_palindrome(s: str) -> bool:
    """
    Check if string is a non-empty palindrome.
    
    Args:
        s: String to check
        
    Returns:
        True if s is a palindrome, False otherwise
    """
    return len(s) > 0 and s == s[::-1]


def _iter_words(line: str) -> Iterator[Tuple[int, int]]:
    """
    Yield (start, end) spans for words within a line.
    
    Words are contiguous alphanumeric sequences (Unicode-aware).
    
    Args:
        line: Line of text to process
        
    Yields:
        Tuples of (start_index, end_index) for each word
    """
    n = len(line)
    i = 0
    while i < n:
        # Skip non-alphanumeric characters
        while i < n and not line[i].isalnum():
            i += 1
        if i >= n:
            break
        start = i
        # Consume contiguous alphanumeric characters
        while i < n and line[i].isalnum():
            i += 1
        yield start, i


def _iter_sentences(line: str) -> Iterator[Tuple[int, int]]:
    """
    Yield (start, end) spans of sentence-like segments within a line.
    
    Sentences end at '.', '!' or '?' with optional trailing quotes/brackets.
    The final fragment without terminal punctuation is also yielded.
    
    Args:
        line: Line of text to process
        
    Yields:
        Tuples of (start_index, end_index) for each sentence
    """
    n = len(line)
    start = 0
    i = 0
    while i < n:
        if line[i] in SENTENCE_TERMINATORS:
            end = i + 1
            # Include typical trailing quotes/brackets adjacent to sentence end
            while end < n and line[end] in SENTENCE_TRAILING_CHARS:
                end += 1
            yield start, end
            # Skip whitespace before next sentence
            j = end
            while j < n and line[j].isspace():
                j += 1
            start = j
            i = j
        else:
            i += 1
    if start < n:
        yield start, n


def _check_and_add_match(
    results: List[PalindromeMatch],
    category: str,
    segment: str,
    line_no: int,
    start_pos: int,
    end_pos: int,
    options: DetectionOptions,
) -> None:
    """
    Check if segment is a palindrome and add to results if it meets criteria.
    
    Args:
        results: List to append match to
        category: Type of palindrome ('word', 'sentence', or 'line')
        segment: Text segment to check
        line_no: 1-based line number
        start_pos: 0-based column start
        end_pos: 0-based column end
        options: Detection options with normalization settings
    """
    normalized = _normalize(segment, options.ignore_case, options.ignore_non_alnum)
    if len(normalized) >= options.min_length and _is_palindrome(normalized):
        match = PalindromeMatch(
            category=category,
            text=segment,
            normalized=normalized,
            length=len(normalized),
            line_no=line_no,
            start_pos=start_pos,
            end_pos=end_pos,
        )
        results.append(match)
        logger.debug(f"Found {category} palindrome: {segment!r} at line {line_no}")


def _detect_line_palindromes(
    line: str,
    line_no: int,
    options: DetectionOptions,
    results: List[PalindromeMatch],
) -> None:
    """
    Detect palindromic lines.
    
    Args:
        line: Line of text to check
        line_no: 1-based line number
        options: Detection options
        results: List to append matches to
    """
    _check_and_add_match(
        results,
        category="line",
        segment=line,
        line_no=line_no,
        start_pos=0,
        end_pos=len(line),
        options=options,
    )


def _detect_word_palindromes(
    line: str,
    line_no: int,
    options: DetectionOptions,
    results: List[PalindromeMatch],
) -> None:
    """
    Detect palindromic words within a line.
    
    Args:
        line: Line of text to check
        line_no: 1-based line number
        options: Detection options
        results: List to append matches to
    """
    for start, end in _iter_words(line):
        segment = line[start:end]
        _check_and_add_match(
            results,
            category="word",
            segment=segment,
            line_no=line_no,
            start_pos=start,
            end_pos=end,
            options=options,
        )


def _detect_sentence_palindromes(
    line: str,
    line_no: int,
    options: DetectionOptions,
    results: List[PalindromeMatch],
) -> None:
    """
    Detect palindromic sentences within a line.
    
    Args:
        line: Line of text to check
        line_no: 1-based line number
        options: Detection options
        results: List to append matches to
    """
    for start, end in _iter_sentences(line):
        segment = line[start:end]
        if not segment.strip():
            continue
        _check_and_add_match(
            results,
            category="sentence",
            segment=segment,
            line_no=line_no,
            start_pos=start,
            end_pos=end,
            options=options,
        )


def detect_palindromes(text: str, options: DetectionOptions) -> List[PalindromeMatch]:
    """
    Detect palindromic words, sentences, and lines within the provided text.
    
    Processing is done per line so results can be highlighted within a single line.
    Line numbers are 1-based for compatibility with Tk Text indexing.
    
    Args:
        text: Text to analyze
        options: Detection configuration
        
    Returns:
        List of PalindromeMatch objects for all detected palindromes
    """
    results: List[PalindromeMatch] = []
    lines = text.splitlines()

    for line_no, line in enumerate(lines, start=1):
        if options.check_lines:
            _detect_line_palindromes(line, line_no, options, results)

        if options.check_words:
            _detect_word_palindromes(line, line_no, options, results)

        if options.check_sentences:
            _detect_sentence_palindromes(line, line_no, options, results)

    logger.info(f"Detected {len(results)} palindromes in text")
    return results