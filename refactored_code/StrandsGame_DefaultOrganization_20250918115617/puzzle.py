from __future__ import annotations

import difflib
import logging
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Constants
MIN_SEGMENT_LENGTH = 2
MAX_SEGMENT_LENGTH = 4
MIN_SIMILARITY_THRESHOLD = 0.5
MIN_STRING_LENGTH_FOR_SPLIT = 4
SINGLE_SEGMENT_LENGTH = 3
DOUBLE_SEGMENT_LENGTH = 4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize(text: str) -> str:
    """
    Normalize a phrase for matching: lowercase, remove spaces and punctuation.
    
    Args:
        text: The input string to normalize.
        
    Returns:
        Normalized string containing only alphanumeric characters in lowercase.
    """
    return re.sub(r"[^a-z0-9]", "", text.lower())


@dataclass
class Segment:
    """
    Represents a single strand segment in a puzzle.
    
    Attributes:
        id: Unique identifier for the segment.
        text: The text content of the segment.
        phrase_index: Index of the phrase this segment belongs to.
        seg_index: Index of this segment within its phrase.
    """
    id: str
    text: str
    phrase_index: int
    seg_index: int

    def to_dict(self) -> Dict:
        """
        Convert segment to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the segment.
        """
        return {
            "id": self.id,
            "text": self.text,
            "phrase_index": self.phrase_index,
            "seg_index": self.seg_index,
        }


@dataclass
class StrandPuzzle:
    """
    A Strands puzzle containing a theme, target phrases, and generated segments.
    
    Segments are created by splitting each phrase (letters only) into 2-4 character chunks,
    then shuffled across all phrases. Segment generation is deterministic based on puzzle ID.
    
    Attributes:
        id: Unique puzzle identifier.
        theme: Theme description for the puzzle.
        phrases: List of target phrases/words to find.
        segments: Generated segments from phrases.
        phrase_segments_map: Maps phrase index to its segment IDs.
    """
    id: str
    theme: str
    phrases: List[str]
    segments: List[Segment] = field(default_factory=list)
    phrase_segments_map: Dict[int, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize puzzle by building segments."""
        self.build_segments()

    def build_segments(self) -> None:
        """
        Generate segments for each phrase and shuffle across the puzzle.
        
        Uses a deterministic random seed from the puzzle ID for reproducibility.
        """
        rng = random.Random(self.id)
        all_segments: List[Segment] = []
        phrase_segments_map: Dict[int, List[str]] = {}

        for phrase_idx, phrase in enumerate(self.phrases):
            letters = normalize(phrase)
            parts = self._split_into_segments(letters, rng)
            segment_ids_for_phrase = self._create_segments_for_phrase(
                phrase_idx, parts, all_segments
            )
            phrase_segments_map[phrase_idx] = segment_ids_for_phrase

        rng.shuffle(all_segments)
        self.segments = all_segments
        self.phrase_segments_map = phrase_segments_map

    def _create_segments_for_phrase(
        self, phrase_idx: int, parts: List[str], all_segments: List[Segment]
    ) -> List[str]:
        """
        Create segment objects for a phrase and add to all_segments list.
        
        Args:
            phrase_idx: Index of the phrase.
            parts: List of text parts for the phrase.
            all_segments: List to append created segments to.
            
        Returns:
            List of segment IDs created for this phrase.
        """
        segment_ids = []
        for seg_idx, part in enumerate(parts):
            seg_id = f"{self.id}-{phrase_idx}-{seg_idx}"
            segment_ids.append(seg_id)
            all_segments.append(
                Segment(id=seg_id, text=part, phrase_index=phrase_idx, seg_index=seg_idx)
            )
        return segment_ids

    @staticmethod
    def _split_into_segments(text: str, rng: random.Random) -> List[str]:
        """
        Split a string into 2-4 length segments with no leftover of length 1.
        
        Ensures at least two segments for strings of length >= 4.
        
        Args:
            text: The string to split.
            rng: Random number generator for deterministic splitting.
            
        Returns:
            List of text segments.
        """
        text_length = len(text)
        
        # Handle very short strings
        if text_length <= SINGLE_SEGMENT_LENGTH:
            return [text]
        
        # Handle exactly 4 characters
        if text_length == DOUBLE_SEGMENT_LENGTH:
            return [text[:2], text[2:]]

        parts = StrandPuzzle._split_long_string(text, text_length, rng)
        
        # Ensure at least two parts if possible
        if len(parts) == 1 and text_length >= MIN_STRING_LENGTH_FOR_SPLIT:
            return [text[: text_length // 2], text[text_length // 2 :]]
        
        return parts

    @staticmethod
    def _split_long_string(text: str, text_length: int, rng: random.Random) -> List[str]:
        """
        Split a long string (>4 chars) into segments avoiding remainder of 1.
        
        Args:
            text: The string to split.
            text_length: Length of the string.
            rng: Random number generator.
            
        Returns:
            List of text segments.
        """
        parts: List[str] = []
        position = 0
        
        while position < text_length:
            remaining = text_length - position
            segment_length = StrandPuzzle._calculate_segment_length(
                remaining, position, text_length
            )
            
            # Adjust to avoid leaving remainder of 1
            if remaining - segment_length == 1:
                segment_length = StrandPuzzle._adjust_for_remainder(
                    segment_length, remaining
                )
            
            # Ensure last chunk is not too small
            if remaining - segment_length != 0 and remaining - segment_length < MIN_SEGMENT_LENGTH:
                segment_length = remaining - MIN_SEGMENT_LENGTH
            
            parts.append(text[position : position + segment_length])
            position += segment_length
        
        return parts

    @staticmethod
    def _calculate_segment_length(remaining: int, position: int, text_length: int) -> int:
        """
        Calculate appropriate segment length based on remaining characters.
        
        Args:
            remaining: Number of remaining characters.
            position: Current position in string.
            text_length: Total length of string.
            
        Returns:
            Calculated segment length.
        """
        if remaining <= MAX_SEGMENT_LENGTH:
            return remaining
        
        rng = random.Random()
        return rng.randint(MIN_SEGMENT_LENGTH, MAX_SEGMENT_LENGTH)

    @staticmethod
    def _adjust_for_remainder(segment_length: int, remaining: int) -> int:
        """
        Adjust segment length to avoid leaving a remainder of 1.
        
        Args:
            segment_length: Current segment length.
            remaining: Remaining characters.
            
        Returns:
            Adjusted segment length.
        """
        if segment_length < MAX_SEGMENT_LENGTH:
            return segment_length + 1
        return segment_length - 1

    def to_dict(self) -> Dict:
        """
        Convert puzzle to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the puzzle.
        """
        return {
            "id": self.id,
            "theme": self.theme,
            "phrases": self.phrases,
            "segments": [seg.to_dict() for seg in self.segments],
            "phrase_segments_map": self.phrase_segments_map,
        }


class PuzzleBank:
    """
    Manages a collection of pre-defined puzzles.
    
    Provides access to puzzles by ID or random selection.
    """
    
    def __init__(self):
        """Initialize the puzzle bank and load puzzles."""
        self._puzzles: Dict[str, StrandPuzzle] = {}
        self._load()

    def _load(self) -> None:
        """
        Load pre-defined puzzles into the bank.
        
        In production, these could come from a database or file.
        """
        puzzles_seed = [
            StrandPuzzle(
                id="fruits1",
                theme="Fruits",
                phrases=["apple", "banana", "cherry", "grape", "orange", "pear"],
            ),
            StrandPuzzle(
                id="cafe1",
                theme="Cafe Menu",
                phrases=["espresso", "cappuccino", "latte", "americano", "macchiato", "mocha"],
            ),
            StrandPuzzle(
                id="tech1",
                theme="Tech Buzzwords",
                phrases=[
                    "machine learning",
                    "artificial intelligence",
                    "data science",
                    "neural network",
                    "big data",
                    "deep learning",
                ],
            ),
        ]
        self._puzzles = {puzzle.id: puzzle for puzzle in puzzles_seed}

    def all_ids(self) -> List[str]:
        """
        Get all available puzzle IDs.
        
        Returns:
            List of puzzle IDs.
        """
        return list(self._puzzles.keys())

    def get_by_id(self, puzzle_id: str) -> Optional[StrandPuzzle]:
        """
        Retrieve a puzzle by its ID.
        
        Args:
            puzzle_id: The ID of the puzzle to retrieve.
            
        Returns:
            The puzzle if found, None otherwise.
        """
        return self._puzzles.get(puzzle_id)

    def random_puzzle(self) -> StrandPuzzle:
        """
        Get a random puzzle from the bank.
        
        Returns:
            A randomly selected puzzle.
        """
        return random.choice(list(self._puzzles.values()))


def verify_merge(puzzle: StrandPuzzle, selected_ids: List[str]) -> Dict:
    """
    Verify whether selected segments form a valid phrase or partial path.
    
    Rules:
    - All segments must belong to the same phrase and be in correct order.
    - A full valid solution must exactly match the complete phrase segments.
    
    Args:
        puzzle: The puzzle being solved.
        selected_ids: List of selected segment IDs.
        
    Returns:
        Dictionary with status ("ok", "partial", or "invalid"), message, and optional details.
    """
    if not selected_ids:
        return {"status": "invalid", "message": "No strands selected."}

    segments = _get_segments_from_ids(puzzle, selected_ids)
    if segments is None:
        return {"status": "invalid", "message": "Unknown strand selected."}

    # Check if all segments belong to same phrase
    phrase_indices = {seg.phrase_index for seg in segments}
    if len(phrase_indices) != 1:
        return _handle_mixed_phrases(puzzle, segments)

    phrase_index = segments[0].phrase_index
    return _verify_phrase_segments(puzzle, segments, phrase_index)


def _get_segments_from_ids(
    puzzle: StrandPuzzle, selected_ids: List[str]
) -> Optional[List[Segment]]:
    """
    Retrieve segment objects from their IDs.
    
    Args:
        puzzle: The puzzle containing segments.
        selected_ids: List of segment IDs to retrieve.
        
    Returns:
        List of segments if all found, None if any segment not found.
    """
    seg_by_id = {seg.id: seg for seg in puzzle.segments}
    segments: List[Segment] = []
    
    for segment_id in selected_ids:
        if segment_id in seg_by_id:
            segments.append(seg_by_id[segment_id])
        else:
            # Try to reconstruct from phrase map
            reconstructed = _segment_from_any(puzzle, segment_id)
            if not reconstructed:
                return None
            segments.append(reconstructed)
    
    return segments


def _handle_mixed_phrases(puzzle: StrandPuzzle, segments: List[Segment]) -> Dict:
    """
    Handle case where selected segments come from different phrases.
    
    Args:
        puzzle: The puzzle being solved.
        segments: The selected segments.
        
    Returns:
        Dictionary with invalid status and helpful message.
    """
    message = "Those strands come from different words/phrases. Try sticking to one at a time."
    
    # Suggest nearest phrase by similarity
    concatenated = "".join(seg.text for seg in segments)
    nearest_phrase, similarity_ratio = _nearest_phrase(puzzle, concatenated)
    
    if nearest_phrase and similarity_ratio >= MIN_SIMILARITY_THRESHOLD:
        message += f' Your merge looks close to: "{nearest_phrase}".'
    
    return {"status": "invalid", "message": message}


def _verify_phrase_segments(
    puzzle: StrandPuzzle, segments: List[Segment], phrase_index: int
) -> Dict:
    """
    Verify segments for a single phrase.
    
    Args:
        puzzle: The puzzle being solved.
        segments: Segments from the same phrase.
        phrase_index: Index of the phrase.
        
    Returns:
        Dictionary with verification result.
    """
    target_segment_ids = puzzle.phrase_segments_map[phrase_index]
    selected_segment_indices = [seg.seg_index for seg in segments]

    # Check if segments are in strictly increasing and contiguous order
    is_increasing_order = all(
        selected_segment_indices[i] + 1 == selected_segment_indices[i + 1]
        for i in range(len(selected_segment_indices) - 1)
    )

    if is_increasing_order:
        return _handle_ordered_segments(
            puzzle, segments, phrase_index, target_segment_ids, selected_segment_indices
        )

    # Segments from same phrase but out of order
    if len(set(selected_segment_indices)) == len(selected_segment_indices):
        return {
            "status": "invalid",
            "message": "These strands belong to the same word/phrase, but the order seems off.",
        }

    # General invalid with suggestion
    concatenated = "".join(seg.text for seg in segments)
    nearest_phrase, similarity_ratio = _nearest_phrase(puzzle, concatenated)
    hint = ""
    if nearest_phrase and similarity_ratio >= MIN_SIMILARITY_THRESHOLD:
        hint = f' It resembles: "{nearest_phrase}".'
    
    return {"status": "invalid", "message": f"That merge doesn't form a target.{hint}"}


def _handle_ordered_segments(
    puzzle: StrandPuzzle,
    segments: List[Segment],
    phrase_index: int,
    target_segment_ids: List[str],
    selected_segment_indices: List[int],
) -> Dict:
    """
    Handle segments that are in correct order.
    
    Args:
        puzzle: The puzzle being solved.
        segments: The selected segments.
        phrase_index: Index of the phrase.
        target_segment_ids: All segment IDs for the phrase.
        selected_segment_indices: Indices of selected segments.
        
    Returns:
        Dictionary with verification result.
    """
    start_idx = selected_segment_indices[0]
    end_idx = selected_segment_indices[-1]
    selected_ids_ordered = [seg.id for seg in segments]

    # Check for complete phrase match
    if (start_idx == 0 and end_idx == len(target_segment_ids) - 1 and
            selected_ids_