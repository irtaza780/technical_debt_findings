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
logger = logging.getLogger(__name__)


def normalize(s: str) -> str:
    """
    Normalizes a phrase for matching: lowercase, remove spaces and punctuation.
    Keeps alphanumeric characters only.
    
    Args:
        s: The string to normalize.
        
    Returns:
        Normalized string with only lowercase alphanumeric characters.
    """
    return re.sub(r"[^a-z0-9]", "", s.lower())


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
        Returns a dict suitable for JSON serialization to the client.
        
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
    A Strands puzzle: theme, set of target phrases/words, and generated segments.
    
    Segments are created by splitting each phrase (letters only) into 2-4 character chunks,
    and then shuffling across all phrases.
    
    Attributes:
        id: Unique puzzle identifier.
        theme: The theme of the puzzle.
        phrases: List of target phrases to find.
        segments: Generated segments from phrases.
        phrase_segments_map: Maps phrase index to its segment IDs.
    """
    id: str
    theme: str
    phrases: List[str]
    segments: List[Segment] = field(default_factory=list)
    phrase_segments_map: Dict[int, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        """
        Build segments deterministically based on puzzle ID.
        """
        self.build_segments()

    def build_segments(self) -> None:
        """
        Generate segments for each phrase and shuffle across the puzzle.
        
        Uses a deterministic random seed from the puzzle id for reproducibility.
        """
        rng = random.Random(self.id)
        all_segments: List[Segment] = []
        phrase_segments_map: Dict[int, List[str]] = {}

        for p_idx, phrase in enumerate(self.phrases):
            letters = normalize(phrase)
            parts = self._split_into_segments(letters, rng)
            seg_ids_for_phrase = self._create_segment_objects(
                p_idx, parts, all_segments
            )
            phrase_segments_map[p_idx] = seg_ids_for_phrase

        rng.shuffle(all_segments)
        self.segments = all_segments
        self.phrase_segments_map = phrase_segments_map

    def _create_segment_objects(
        self, phrase_idx: int, parts: List[str], all_segments: List[Segment]
    ) -> List[str]:
        """
        Create Segment objects for each part and add to all_segments list.
        
        Args:
            phrase_idx: Index of the phrase.
            parts: List of text parts to create segments from.
            all_segments: List to append created segments to.
            
        Returns:
            List of segment IDs for this phrase.
        """
        seg_ids_for_phrase = []
        for s_idx, part in enumerate(parts):
            seg_id = f"{self.id}-{phrase_idx}-{s_idx}"
            seg_ids_for_phrase.append(seg_id)
            all_segments.append(
                Segment(
                    id=seg_id,
                    text=part,
                    phrase_index=phrase_idx,
                    seg_index=s_idx,
                )
            )
        return seg_ids_for_phrase

    @staticmethod
    def _split_into_segments(s: str, rng: random.Random) -> List[str]:
        """
        Splits a string into 2-4 length segments with no leftover of length 1.
        
        Ensures at least two segments for strings of length >= 4.
        
        Args:
            s: String to split.
            rng: Random number generator for deterministic splitting.
            
        Returns:
            List of string segments.
        """
        n = len(s)
        
        # Handle short strings
        if n <= SINGLE_SEGMENT_LENGTH:
            return [s]
        
        if n == DOUBLE_SEGMENT_LENGTH:
            return [s[:2], s[2:]]

        parts: List[str] = []
        i = 0
        
        while i < n:
            remaining = n - i
            length = StrandPuzzle._calculate_segment_length(
                remaining, rng
            )
            parts.append(s[i : i + length])
            i += length

        # Ensure at least two parts if possible
        if len(parts) == 1 and n >= MIN_STRING_LENGTH_FOR_SPLIT:
            return [s[: n // 2], s[n // 2 :]]
        
        return parts

    @staticmethod
    def _calculate_segment_length(remaining: int, rng: random.Random) -> int:
        """
        Calculate the length of the next segment to avoid remainder of 1.
        
        Args:
            remaining: Number of characters remaining to segment.
            rng: Random number generator.
            
        Returns:
            Length of the next segment.
        """
        if remaining <= MAX_SEGMENT_LENGTH:
            return remaining

        length = rng.randint(MIN_SEGMENT_LENGTH, MAX_SEGMENT_LENGTH)
        
        # Avoid leaving a remainder of 1
        if remaining - length == 1:
            if length < MAX_SEGMENT_LENGTH:
                length += 1
            else:
                length -= 1
        
        # If we accidentally made last chunk too small, adjust
        if (remaining - length) != 0 and (remaining - length) < MIN_SEGMENT_LENGTH:
            length = remaining - MIN_SEGMENT_LENGTH
        
        return length

    def to_dict(self) -> Dict:
        """
        Returns a dictionary representation of the puzzle suitable for JSON.
        
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
    Holds multiple pre-defined puzzles and provides access by id or random choice.
    """

    def __init__(self):
        """Initialize the puzzle bank and load puzzles."""
        self._puzzles: Dict[str, StrandPuzzle] = {}
        self._load()

    def _load(self) -> None:
        """
        Defines a set of themed puzzles.
        
        In a production system, these could come from a database or file.
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
                phrases=[
                    "espresso",
                    "cappuccino",
                    "latte",
                    "americano",
                    "macchiato",
                    "mocha",
                ],
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
        self._puzzles = {p.id: p for p in puzzles_seed}

    def all_ids(self) -> List[str]:
        """
        Returns all available puzzle IDs.
        
        Returns:
            List of puzzle IDs.
        """
        return list(self._puzzles.keys())

    def get_by_id(self, puzzle_id: str) -> Optional[StrandPuzzle]:
        """
        Returns a puzzle by id, or None if not found.
        
        Args:
            puzzle_id: The ID of the puzzle to retrieve.
            
        Returns:
            The puzzle if found, None otherwise.
        """
        return self._puzzles.get(puzzle_id)

    def random_puzzle(self) -> StrandPuzzle:
        """
        Returns a random puzzle.
        
        Returns:
            A randomly selected puzzle.
        """
        return random.choice(list(self._puzzles.values()))


def verify_merge(puzzle: StrandPuzzle, selected_ids: List[str]) -> Dict:
    """
    Verifies whether the selected segments form a valid phrase or partial path.
    
    Rules:
    - To be valid, all segments must belong to the same phrase and be in correct order.
    - A full valid solution must exactly match the full set of segments for that phrase.
    
    Args:
        puzzle: The puzzle being solved.
        selected_ids: List of selected segment IDs.
        
    Returns:
        Dictionary with status ("ok", "partial", or "invalid") and message.
    """
    if not selected_ids:
        return {"status": "invalid", "message": "No strands selected."}

    segments = _get_segments_from_ids(puzzle, selected_ids)
    if segments is None:
        return {"status": "invalid", "message": "Unknown strand selected."}

    # Check single phrase constraint
    phrase_indices = {seg.phrase_index for seg in segments}
    if len(phrase_indices) != 1:
        return _handle_multiple_phrases(puzzle, segments)

    phrase_index = segments[0].phrase_index
    return _verify_phrase_segments(puzzle, segments, phrase_index)


def _get_segments_from_ids(
    puzzle: StrandPuzzle, selected_ids: List[str]
) -> Optional[List[Segment]]:
    """
    Retrieves Segment objects from their IDs.
    
    Args:
        puzzle: The puzzle containing segments.
        selected_ids: List of segment IDs to retrieve.
        
    Returns:
        List of Segment objects, or None if any ID is invalid.
    """
    seg_by_id = {seg.id: seg for seg in puzzle.segments}
    segments: List[Segment] = []
    
    for sid in selected_ids:
        if sid in seg_by_id:
            segments.append(seg_by_id[sid])
        else:
            # Try to reconstruct from phrase map
            found = _segment_from_any(puzzle, sid)
            if not found:
                return None
            segments.append(found)
    
    return segments


def _handle_multiple_phrases(puzzle: StrandPuzzle, segments: List[Segment]) -> Dict:
    """
    Handles the case where selected segments come from different phrases.
    
    Args:
        puzzle: The puzzle being solved.
        segments: List of segments from different phrases.
        
    Returns:
        Dictionary with invalid status and helpful message.
    """
    msg = "Those strands come from different words/phrases. Try sticking to one at a time."
    concat = "".join(seg.text for seg in segments)
    nearest, ratio = _nearest_phrase(puzzle, concat)
    
    if nearest and ratio >= MIN_SIMILARITY_THRESHOLD:
        msg += f' Your merge looks close to: "{nearest}".'
    
    return {"status": "invalid", "message": msg}


def _verify_phrase_segments(
    puzzle: StrandPuzzle, segments: List[Segment], phrase_index: int
) -> Dict:
    """
    Verifies segments for a single phrase.
    
    Args:
        puzzle: The puzzle being solved.
        segments: List of segments from the same phrase.
        phrase_index: Index of the phrase.
        
    Returns:
        Dictionary with verification result.
    """
    target_seg_ids = puzzle.phrase_segments_map[phrase_index]
    selected_seg_indices = [seg.seg_index for seg in segments]

    # Check if selected are in strictly increasing order and contiguous
    is_increasing_order = all(
        selected_seg_indices[i] + 1 == selected_seg_indices[i + 1]
        for i in range(len(selected_seg_indices) - 1)
    )

    if is_increasing_order:
        return _handle_ordered_segments(
            puzzle, segments, phrase_index, target_seg_ids, selected_seg_indices
        )

    # Check if reordering might help
    if len(set(selected_seg_indices)) == len(selected_seg_indices):
        return {
            "status": "invalid",
            "message": "These strands belong to the same word/phrase, but the order seems off.",
        }

    # General invalid feedback
    return _handle_invalid_merge(puzzle, segments)


def _handle_ordered_segments(
    puzzle: StrandPuzzle,
    segments: List[Segment],
    phrase_index: int,
    target_seg_ids: List[str],
    selected_seg_indices: List[int],
) -> Dict:
    """
    Handles verification of segments that are in correct order.
    
    Args:
        puzzle: The puzzle being solved.
        segments: List of ordered segments.
        phrase_index: Index of the phrase.
        target_seg_ids: Expected segment IDs for the phrase.
        selected_seg_indices: Indices of selected segments.
        
    Returns:
        Dictionary with verification result.
    """
    start_idx = selected_seg_indices[0]
    end_idx = selected_seg_indices[-1]
    selected_ids_ordered = [seg.id for seg in segments]

    # Full match must start at 0 and end at last
    if (
        start_idx == 0
        and end_idx == len(target_seg_ids) - 1
        and selected_ids_ordered == target_seg_ids
    ):
        solved_phrase = puzzle.phrases[phrase_index]
        return {
            "status": "ok",
            "message": f'Great! You found: "{solved_phrase}".',
            "phrase_index": phrase_index,
            "solved_phrase": solved_phrase,
        }

    # Partial prefix
    if start_idx == 0:
        assembled = "".join(seg.text for seg in segments)
        return {
            "status": "partial",
            "message": f'Good path! You have a valid beginning of "{puzzle.phrases[phrase_index]}". Keep going.',
            "assembled": assembled,
            "phrase_index": phrase_index,
        }

    # Valid contiguous middle/end, but not starting from first piece
    return {
        "status": "partial",
        "message": "Nice connection! These pieces fit together within a word/phrase. Try adding the missing beginning.",
        "phrase_index": phrase_index,
    }


def _handle_invalid_merge(puzzle: StrandPuzzle, segments: List[Segment]) -> Dict:
    """
    Handles invalid merge with helpful feedback.
    
    Args:
        puzzle: The puzzle being solved.
        segments: List of segments that don't form a valid merge.
        
    Returns:
        Dictionary with invalid status and message.
    """
    concat = "".join(seg.text for seg in segments)
    nearest, ratio = _nearest_phrase(puzzle, concat)
    hint = ""
    
    if nearest and ratio >= MIN_SIMILARITY_