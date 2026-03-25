from dataclasses import dataclass
from typing import Any, List, Optional, Union, Iterable, Set
import re
import logging

logger = logging.getLogger(__name__)

# Constants
QUESTION_TYPE_MCQ = "mcq"
QUESTION_TYPE_SHORT = "short"
VALID_QUESTION_TYPES = {QUESTION_TYPE_MCQ, QUESTION_TYPE_SHORT}
INVALID_INDEX = -1
NA_TEXT = "N/A"
OPTION_PREFIX = "Option #"


def normalize_text(text: str) -> str:
    """
    Normalize free text for comparison: trim, lowercase, collapse spaces.
    
    Args:
        text: The text to normalize.
        
    Returns:
        Normalized text string, or empty string if input is None.
    """
    if text is None:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


@dataclass
class Question:
    """
    Represents a quiz question with support for multiple-choice and short-answer formats.
    
    Attributes:
        qtype: Question type - "mcq" for multiple-choice or "short" for short-answer.
        prompt: The question text.
        options: List of option strings for MCQ questions; None for short-answer.
        answer: For MCQ: index (int), option text (str), or list of indices/texts.
                For short-answer: correct answer string or list of acceptable strings.
        explanation: Optional explanation string.
    """
    qtype: str
    prompt: str
    options: Optional[List[str]] = None
    answer: Union[str, int, List[Union[str, int]], None] = None
    explanation: Optional[str] = None

    def is_correct(self, user_answer: Any) -> bool:
        """
        Determine if the user's answer is correct.
        
        Args:
            user_answer: The user's submitted answer.
            
        Returns:
            True if the answer is correct, False otherwise.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._is_mcq_correct(user_answer)
        else:
            return self._is_short_answer_correct(user_answer)

    def _is_mcq_correct(self, user_answer: Any) -> bool:
        """
        Check if MCQ user answer matches correct indices.
        
        Args:
            user_answer: User's answer (int, list, tuple, or set).
            
        Returns:
            True if answer matches correct indices, False otherwise.
        """
        correct_indices = self._mcq_correct_indices()
        if not correct_indices:
            return False

        # Handle multiple selections
        if isinstance(user_answer, (list, tuple, set)):
            selected = self._convert_to_indices(user_answer)
            return selected == correct_indices

        # Handle single selection
        try:
            idx = int(user_answer)
        except (ValueError, TypeError):
            return False

        # Only correct if exactly one correct answer and it matches
        return len(correct_indices) == 1 and idx in correct_indices

    def _is_short_answer_correct(self, user_answer: Any) -> bool:
        """
        Check if short-answer user answer matches acceptable answers.
        
        Args:
            user_answer: User's answer string.
            
        Returns:
            True if answer matches an acceptable answer, False otherwise.
        """
        if user_answer is None:
            return False
        user_answer_normalized = normalize_text(str(user_answer))
        acceptable = self._short_acceptable_answers()
        return user_answer_normalized in acceptable

    def _convert_to_indices(self, items: Iterable[Any]) -> Set[int]:
        """
        Convert a collection of items to a set of valid indices.
        
        Args:
            items: Collection of items to convert.
            
        Returns:
            Set of valid indices.
        """
        selected: Set[int] = set()
        for item in items:
            try:
                idx = int(item)
                selected.add(idx)
            except (ValueError, TypeError):
                # Skip non-convertible entries
                continue
        return selected

    def get_correct_answer_text(self) -> str:
        """
        Get human-readable text of the correct answer(s).
        
        Returns:
            Comma-separated string of correct answer(s), or "N/A" if unavailable.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_mcq_correct_answer_text()
        else:
            return self._get_short_answer_text()

    def _get_mcq_correct_answer_text(self) -> str:
        """
        Get correct answer text for MCQ question.
        
        Returns:
            Comma-separated option texts or "N/A".
        """
        indices = sorted(self._mcq_correct_indices())
        if not self.options:
            return NA_TEXT
        texts = [self.options[i] for i in indices if 0 <= i < len(self.options)]
        return ", ".join(texts) if texts else NA_TEXT

    def _get_short_answer_text(self) -> str:
        """
        Get acceptable answer text for short-answer question.
        
        Returns:
            Comma-separated acceptable answers or "N/A".
        """
        acceptable = self._short_acceptable_answers(raw=True)
        return ", ".join(acceptable) if acceptable else NA_TEXT

    def get_user_answer_text(self, user_answer: Any) -> str:
        """
        Get human-readable text of the user's answer.
        
        Args:
            user_answer: The user's submitted answer.
            
        Returns:
            Human-readable answer text or "N/A".
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_mcq_user_answer_text(user_answer)
        else:
            return str(user_answer) if user_answer is not None else NA_TEXT

    def _get_mcq_user_answer_text(self, user_answer: Any) -> str:
        """
        Get user answer text for MCQ question.
        
        Args:
            user_answer: The user's answer.
            
        Returns:
            Human-readable option text(s) or "N/A".
        """
        # Handle multi-selection
        if isinstance(user_answer, (list, tuple, set)):
            return self._indices_to_option_texts(user_answer)

        # Handle single index
        try:
            idx = int(user_answer)
        except (ValueError, TypeError):
            return NA_TEXT

        if self.options and 0 <= idx < len(self.options):
            return self.options[idx]
        return f"{OPTION_PREFIX}{idx + 1}"

    def mcq_correct_indices(self) -> Set[int]:
        """
        Get the set of correct option indices for MCQ questions.
        
        Returns:
            Set of correct indices, or empty set for non-MCQ or invalid questions.
        """
        return set(self._mcq_correct_indices())

    def is_multi_answer(self) -> bool:
        """
        Check if this MCQ has multiple correct answers.
        
        Returns:
            True if MCQ with multiple correct answers, False otherwise.
        """
        return self.qtype == QUESTION_TYPE_MCQ and len(self._mcq_correct_indices()) > 1

    def _mcq_correct_indices(self) -> Set[int]:
        """
        Extract correct option indices from answer field for MCQ questions.
        
        Supports answer as int, str (option text), or list of ints/strings.
        
        Returns:
            Set of valid correct indices.
        """
        indices: Set[int] = set()
        if self.options is None or self.answer is None:
            return indices

        if isinstance(self.answer, list):
            indices.update(self._process_answer_list(self.answer))
        elif isinstance(self.answer, int):
            if 0 <= self.answer < len(self.options):
                indices.add(self.answer)
        elif isinstance(self.answer, str):
            idx = self._match_text_to_index(self.answer)
            if idx >= 0:
                indices.add(idx)

        return indices

    def _process_answer_list(self, answer_list: List[Any]) -> Set[int]:
        """
        Process a list of answer items and convert to indices.
        
        Args:
            answer_list: List of answer items (ints or strings).
            
        Returns:
            Set of valid indices.
        """
        indices: Set[int] = set()
        for item in answer_list:
            if isinstance(item, int):
                if 0 <= item < len(self.options):
                    indices.add(item)
            elif isinstance(item, str):
                idx = self._match_text_to_index(item)
                if idx >= 0:
                    indices.add(idx)
        return indices

    def _match_text_to_index(self, text: str) -> int:
        """
        Find the index of an option by matching normalized text.
        
        Args:
            text: The option text to match.
            
        Returns:
            Index of matching option, or -1 if not found.
        """
        text_normalized = normalize_text(text)
        for i, option in enumerate(self.options):
            if normalize_text(option) == text_normalized:
                return i
        return INVALID_INDEX

    def _short_acceptable_answers(self, raw: bool = False) -> List[str]:
        """
        Get list of acceptable answers for short-answer questions.
        
        Args:
            raw: If True, return un-normalized strings; if False, return normalized.
            
        Returns:
            List of acceptable answer strings.
        """
        if self.answer is None:
            return []

        answers = self._extract_answer_strings()
        return answers if raw else [normalize_text(a) for a in answers]

    def _extract_answer_strings(self) -> List[str]:
        """
        Extract answer strings from answer field.
        
        Returns:
            List of answer strings.
        """
        answers: List[str] = []
        if isinstance(self.answer, list):
            answers = [str(a) if not isinstance(a, str) else a for a in self.answer]
        else:
            answers = [str(self.answer) if not isinstance(self.answer, str) else self.answer]
        return answers

    def _indices_to_option_texts(self, indices: Iterable[Any]) -> str:
        """
        Convert indices to comma-separated option text.
        
        Args:
            indices: Collection of indices.
            
        Returns:
            Comma-separated option texts or "N/A".
        """
        if not self.options:
            return NA_TEXT

        texts: List[str] = []
        # Preserve order for list/tuple; sort for set for determinism
        ordered_indices = list(indices) if not isinstance(indices, set) else sorted(indices)

        for item in ordered_indices:
            try:
                idx = int(item)
            except (ValueError, TypeError):
                continue

            if 0 <= idx < len(self.options):
                texts.append(self.options[idx])
            else:
                texts.append(f"{OPTION_PREFIX}{idx + 1}")

        return ", ".join(texts) if texts else NA_TEXT


def question_from_dict(data: dict) -> Question:
    """
    Create a Question instance from a dictionary.
    
    Expected schema:
    {
      "type": "mcq" | "short",
      "prompt": "question text",
      "options": ["A", "B", "C"],           # required for mcq
      "answer": 1 | "B" | [1,2] | ["B"],   # required
      "explanation": "optional text"
    }
    
    Args:
        data: Dictionary containing question data.
        
    Returns:
        Question instance.
        
    Raises:
        ValueError: If data is invalid or missing required fields.
    """
    if not isinstance(data, dict):
        raise ValueError("Question must be an object")

    qtype = _extract_question_type(data)
    prompt = _extract_prompt(data)

    if qtype == QUESTION_TYPE_MCQ:
        return _create_mcq_question(data, prompt)
    else:
        return _create_short_answer_question(data, prompt)


def _extract_question_type(data: dict) -> str:
    """
    Extract and validate question type from data.
    
    Args:
        data: Question data dictionary.
        
    Returns:
        Validated question type.
        
    Raises:
        ValueError: If type is missing or invalid.
    """
    qtype = data.get("type") or data.get("qtype")
    if not qtype or qtype not in VALID_QUESTION_TYPES:
        raise ValueError(f"Question 'type' must be one of {VALID_QUESTION_TYPES}")
    return qtype


def _extract_prompt(data: dict) -> str:
    """
    Extract and validate prompt from data.
    
    Args:
        data: Question data dictionary.
        
    Returns:
        Validated prompt string.
        
    Raises:
        ValueError: If prompt is missing or invalid.
    """
    prompt = data.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Question 'prompt' must be a non-empty string")
    return prompt


def _create_mcq_question(data: dict, prompt: str) -> Question:
    """
    Create an MCQ Question from validated data.
    
    Args:
        data: Question data dictionary.
        prompt: Validated prompt string.
        
    Returns:
        MCQ Question instance.
        
    Raises:
        ValueError: If MCQ-specific fields are invalid.
    """
    options = data.get("options")
    answer = data.get("answer")
    explanation = data.get("explanation")

    if not isinstance(options, list) or not options or not all(isinstance(o, str) for o in options):
        raise ValueError("MCQ requires a non-empty 'options' list of strings")
    if answer is None:
        raise ValueError("MCQ requires an 'answer'")

    return Question(
        qtype=QUESTION_TYPE_MCQ,
        prompt=prompt,
        options=options,
        answer=answer,
        explanation=explanation
    )


def _create_short_answer_question(data: dict, prompt: str) -> Question:
    """
    Create a short-answer Question from validated data.
    
    Args:
        data: Question data dictionary.
        prompt: Validated prompt string.
        
    Returns:
        Short-answer Question instance.
        
    Raises:
        ValueError: If answer is missing.
    """
    answer = data.get("answer")
    explanation = data.get("explanation")

    if answer is None:
        raise ValueError("Short-answer question requires an 'answer'")

    return Question(
        qtype=QUESTION_TYPE_SHORT,
        prompt=prompt,
        options=None,
        answer=answer,
        explanation=explanation
    )