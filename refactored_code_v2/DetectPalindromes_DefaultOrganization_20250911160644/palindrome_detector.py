import logging
from dataclasses import dataclass
from typing import List, Iterator, Tuple

logger = logging.getLogger(__name__)

MIN_PALINDROME_LENGTH = 3
SENTENCE_TERMINATORS = ".!?"
SENTENCE_TRAILING_CHARS = ')"\']'


@dataclass
class DetectionOptions:
    """Options for controlling what to detect and how to normalize."""
    check_words: bool = True
    check_sentences: bool = True
    check_lines: bool = True
    min_length: int = MIN_PALINDROME_LENGTH
    ignore_case: bool = True
    ignore_non_alnum: bool = True


@dataclass
class PalindromeMatch:
    """
    A single palindrome detection result.
    
    Attributes:
        category: Type of match ('word', 'sentence', or 'line')
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


def _normalize(text: str, ignore_case: bool, ignore_non_alnum: bool) -> str:
    """
    Normalize text according to specified options.
    
    Args:
        text: The text to normalize
        ignore_case: If True, convert to lowercase
        ignore_non_alnum: If True, remove non-alphanumeric characters
        
    Returns:
        Normalized text string
    """
    if ignore_non_alnum:
        text = "".join(char for char in text if char.isalnum())
    if ignore_case:
        text = text.casefold()
    return text


def _is_palindrome(text: str) -> bool:
    """
    Check if text is a non-empty palindrome.
    
    Args:
        text: The text to check
        
    Returns:
        True if text reads the same forwards and backwards, False otherwise
    """
    return len(text) > 0 and text == text[::-1]


def _iter_words(line: str) -> Iterator[Tuple[int, int]]:
    """
    Yield (start, end) spans for words within a line.
    
    Words are contiguous alphanumeric sequences (Unicode-aware).
    
    Args:
        line: The line to scan for words
        
    Yields:
        Tuples of (start_position, end_position) for each word
    """
    line_length = len(line)
    current_pos = 0
    
    while current_pos < line_length:
        # Skip non-alphanumeric characters
        while current_pos < line_length and not line[current_pos].isalnum():
            current_pos += 1
        
        if current_pos >= line_length:
            break
        
        word_start = current_pos
        
        # Consume contiguous alphanumeric characters
        while current_pos < line_length and line[current_pos].isalnum():
            current_pos += 1
        
        yield word_start, current_pos


def _iter_sentences(line: str) -> Iterator[Tuple[int, int]]:
    """
    Yield (start, end) spans of sentence-like segments within a line.
    
    Sentences end at '.', '!' or '?' with optional trailing quotes/brackets.
    The final fragment without terminal punctuation is also yielded.
    
    Args:
        line: The line to scan for sentences
        
    Yields:
        Tuples of (start_position, end_position) for each sentence
    """
    line_length = len(line)
    sentence_start = 0
    current_pos = 0
    
    while current_pos < line_length:
        if line[current_pos] in SENTENCE_TERMINATORS:
            sentence_end = current_pos + 1
            
            # Include typical trailing quotes/brackets adjacent to sentence end
            while sentence_end < line_length and line[sentence_end] in SENTENCE_TRAILING_CHARS:
                sentence_end += 1
            
            yield sentence_start, sentence_end
            
            # Skip whitespace before next sentence
            next_start = sentence_end
            while next_start < line_length and line[next_start].isspace():
                next_start += 1
            
            sentence_start = next_start
            current_pos = next_start
        else:
            current_pos += 1
    
    if sentence_start < line_length:
        yield sentence_start, line_length


def _check_and_record_palindrome(
    segment: str,
    category: str,
    line_no: int,
    start_pos: int,
    end_pos: int,
    options: DetectionOptions,
    results: List[PalindromeMatch]
) -> None:
    """
    Check if a segment is a palindrome and record it if conditions are met.
    
    Args:
        segment: The text segment to check
        category: Type of match ('word', 'sentence', or 'line')
        line_no: 1-based line number
        start_pos: 0-based column start position
        end_pos: 0-based column end position
        options: Detection options with normalization settings
        results: List to append matching palindromes to
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


def detect_palindromes(text: str, options: DetectionOptions) -> List[PalindromeMatch]:
    """
    Detect palindromic words, sentences, and lines within the provided text.
    
    Processing is done per line so results can be highlighted within a single line.
    Line numbers are 1-based to match Tk Text widget indexing.
    
    Args:
        text: The text to analyze
        options: Detection configuration options
        
    Returns:
        List of PalindromeMatch objects for all detected palindromes
    """
    results: List[PalindromeMatch] = []
    lines = text.splitlines()

    for line_no, line in enumerate(lines, start=1):
        # Check entire line as palindrome
        if options.check_lines:
            _check_and_record_palindrome(
                segment=line,
                category="line",
                line_no=line_no,
                start_pos=0,
                end_pos=len(line),
                options=options,
                results=results,
            )

        # Check words in line
        if options.check_words:
            for word_start, word_end in _iter_words(line):
                word_segment = line[word_start:word_end]
                _check_and_record_palindrome(
                    segment=word_segment,
                    category="word",
                    line_no=line_no,
                    start_pos=word_start,
                    end_pos=word_end,
                    options=options,
                    results=results,
                )

        # Check sentences in line
        if options.check_sentences:
            for sentence_start, sentence_end in _iter_sentences(line):
                sentence_segment = line[sentence_start:sentence_end]
                
                # Skip empty or whitespace-only segments
                if not sentence_segment.strip():
                    continue
                
                _check_and_record_palindrome(
                    segment=sentence_segment,
                    category="sentence",
                    line_no=line_no,
                    start_pos=sentence_start,
                    end_pos=sentence_end,
                    options=options,
                    results=results,
                )

    return results