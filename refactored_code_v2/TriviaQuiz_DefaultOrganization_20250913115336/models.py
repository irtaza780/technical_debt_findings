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
MIN_VALID_INDEX = 0
NA_TEXT = "N/A"


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


def _match_text_to_option_index(text: str, options: List[str]) -> int:
    """
    Find the index of an option by matching normalized text.
    
    Args:
        text: The text to match.
        options: List of option strings to search.
        
    Returns:
        The index of the matching option, or INVALID_INDEX if not found.
    """
    text_normalized = normalize_text(text)
    for index, option in enumerate(options):
        if normalize_text(option) == text_normalized:
            return index
    return INVALID_INDEX


def _convert_to_int(value: Any) -> Optional[int]:
    """
    Safely convert a value to an integer.
    
    Args:
        value: The value to convert.
        
    Returns:
        The integer value, or None if conversion fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _is_valid_option_index(index: int, options_count: int) -> bool:
    """
    Check if an index is valid for the given options list.
    
    Args:
        index: The index to validate.
        options_count: The number of available options.
        
    Returns:
        True if the index is valid, False otherwise.
    """
    return MIN_VALID_INDEX <= index < options_count


@dataclass
class Question:
    """
    Represents a quiz question with support for multiple-choice and short-answer types.
    
    Attributes:
        qtype: Question type - "mcq" for multiple-choice or "short" for short-answer.
        prompt: The question text.
        options: List of option strings for MCQ questions. None for short-answer.
        answer: Correct answer(s). For MCQ: index (int), option text (str), or list of indices/texts.
                For short-answer: string or list of acceptable strings.
        explanation: Optional explanation text.
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
            user_answer: The user's provided answer.
            
        Returns:
            True if the answer is correct, False otherwise.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._is_correct_mcq(user_answer)
        else:
            return self._is_correct_short_answer(user_answer)

    def _is_correct_mcq(self, user_answer: Any) -> bool:
        """
        Check if a multiple-choice answer is correct.
        
        Args:
            user_answer: The user's answer (index, indices, or collection).
            
        Returns:
            True if the answer matches the correct answer(s).
        """
        correct_indices = self._mcq_correct_indices()
        if not correct_indices:
            return False

        # Handle multiple selections
        if isinstance(user_answer, (list, tuple, set)):
            selected_indices = self._extract_indices_from_collection(user_answer)
            return selected_indices == correct_indices

        # Handle single selection
        selected_index = _convert_to_int(user_answer)
        if selected_index is None:
            return False

        # Single selection only matches if exactly one correct answer exists
        return len(correct_indices) == 1 and selected_index in correct_indices

    def _is_correct_short_answer(self, user_answer: Any) -> bool:
        """
        Check if a short-answer is correct.
        
        Args:
            user_answer: The user's answer string.
            
        Returns:
            True if the answer matches an acceptable answer.
        """
        if user_answer is None:
            return False
        user_answer_normalized = normalize_text(str(user_answer))
        acceptable_answers = self._short_acceptable_answers()
        return user_answer_normalized in acceptable_answers

    def _extract_indices_from_collection(self, items: Iterable[Any]) -> Set[int]:
        """
        Extract valid option indices from a collection of mixed types.
        
        Args:
            items: Collection of items to convert to indices.
            
        Returns:
            Set of valid indices.
        """
        indices: Set[int] = set()
        for item in items:
            index = _convert_to_int(item)
            if index is not None and self.options and _is_valid_option_index(index, len(self.options)):
                indices.add(index)
        return indices

    def get_correct_answer_text(self) -> str:
        """
        Get a human-readable string of the correct answer(s).
        
        Returns:
            Formatted string of correct answer(s), or NA_TEXT if unavailable.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_correct_answer_text_mcq()
        else:
            return self._get_correct_answer_text_short()

    def _get_correct_answer_text_mcq(self) -> str:
        """
        Get correct answer text for MCQ questions.
        
        Returns:
            Comma-separated list of correct option texts.
        """
        indices = sorted(self._mcq_correct_indices())
        if not self.options or not indices:
            return NA_TEXT
        texts = [self.options[i] for i in indices if _is_valid_option_index(i, len(self.options))]
        return ", ".join(texts) if texts else NA_TEXT

    def _get_correct_answer_text_short(self) -> str:
        """
        Get correct answer text for short-answer questions.
        
        Returns:
            Comma-separated list of acceptable answers.
        """
        acceptable = self._short_acceptable_answers(raw=True)
        return ", ".join(acceptable) if acceptable else NA_TEXT

    def get_user_answer_text(self, user_answer: Any) -> str:
        """
        Convert a user's answer to human-readable text.
        
        Args:
            user_answer: The user's provided answer.
            
        Returns:
            Formatted string representation of the answer.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_user_answer_text_mcq(user_answer)
        else:
            return self._get_user_answer_text_short(user_answer)

    def _get_user_answer_text_mcq(self, user_answer: Any) -> str:
        """
        Convert MCQ user answer to text.
        
        Args:
            user_answer: The user's answer (index or indices).
            
        Returns:
            Formatted option text(s).
        """
        if isinstance(user_answer, (list, tuple, set)):
            return self._indices_to_option_texts(user_answer)

        index = _convert_to_int(user_answer)
        if index is None:
            return NA_TEXT

        if self.options and _is_valid_option_index(index, len(self.options)):
            return self.options[index]
        return f"Option #{index + 1}"

    def _get_user_answer_text_short(self, user_answer: Any) -> str:
        """
        Convert short-answer user answer to text.
        
        Args:
            user_answer: The user's answer string.
            
        Returns:
            String representation of the answer.
        """
        return str(user_answer) if user_answer is not None else NA_TEXT

    def mcq_correct_indices(self) -> Set[int]:
        """
        Get the set of correct option indices for MCQ questions.
        
        Returns:
            Set of correct indices, or empty set for non-MCQ or unconfigured questions.
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
        Extract correct option indices from the answer field.
        
        Supports answer as int, str (option text), or list of ints/strings.
        
        Returns:
            Set of valid option indices.
        """
        indices: Set[int] = set()
        if self.options is None or self.answer is None:
            return indices

        if isinstance(self.answer, list):
            indices.update(self._extract_indices_from_answer_list(self.answer))
        elif isinstance(self.answer, int):
            if _is_valid_option_index(self.answer, len(self.options)):
                indices.add(self.answer)
        elif isinstance(self.answer, str):
            index = _match_text_to_option_index(self.answer, self.options)
            if index != INVALID_INDEX:
                indices.add(index)

        return indices

    def _extract_indices_from_answer_list(self, answer_list: List[Any]) -> Set[int]:
        """
        Extract indices from a list of mixed answer types.
        
        Args:
            answer_list: List containing ints or strings.
            
        Returns:
            Set of valid indices.
        """
        indices: Set[int] = set()
        for item in answer_list:
            if isinstance(item, int):
                if _is_valid_option_index(item, len(self.options)):
                    indices.add(item)
            elif isinstance(item, str):
                index = _match_text_to_option_index(item, self.options)
                if index != INVALID_INDEX:
                    indices.add(index)
        return indices

    def _short_acceptable_answers(self, raw: bool = False) -> List[str]:
        """
        Get acceptable answers for short-answer questions.
        
        Args:
            raw: If True, return un-normalized strings. If False, return normalized.
            
        Returns:
            List of acceptable answer strings.
        """
        if self.answer is None:
            return []

        answers = self._extract_answer_strings()
        return answers if raw else [normalize_text(a) for a in answers]

    def _extract_answer_strings(self) -> List[str]:
        """
        Extract answer strings from the answer field.
        
        Returns:
            List of answer strings.
        """
        answers: List[str] = []
        if isinstance(self.answer, list):
            for item in self.answer:
                answers.append(str(item))
        else:
            answers.append(str(self.answer))
        return answers

    def _indices_to_option_texts(self, indices: Iterable[Any]) -> str:
        """
        Convert option indices to their text representations.
        
        Args:
            indices: Collection of indices to convert.
            
        Returns:
            Comma-separated list of option texts, or NA_TEXT if none valid.
        """
        if not self.options:
            return NA_TEXT

        texts: List[str] = []
        # Preserve order for list/tuple; sort for set for determinism
        sorted_indices = list(indices) if not isinstance(indices, set) else sorted(indices)

        for item in sorted_indices:
            index = _convert_to_int(item)
            if index is None:
                continue
            if _is_valid_option_index(index, len(self.options)):
                texts.append(self.options[index])
            else:
                texts.append(f"Option #{index + 1}")

        return ", ".join(texts) if texts else NA_TEXT


def question_from_dict(data: dict) -> Question:
    """
    Create a Question instance from a dictionary.
    
    Expected schema for MCQ:
    {
      "type": "mcq",
      "prompt": "question text",
      "options": ["A", "B", "C", "D"],
      "answer": 1 | "B" | [1,2] | ["B","C"],
      "explanation": "optional text"
    }
    
    Expected schema for short-answer:
    {
      "type": "short",
      "prompt": "question text",
      "answer": "text" | ["text1", "text2"],
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

    qtype = data.get("type") or data.get("qtype")
    _validate_question_type(qtype)

    prompt = data.get("prompt")
    _validate_prompt(prompt)

    answer = data.get("answer")
    explanation = data.get("explanation")

    if qtype == QUESTION_TYPE_MCQ:
        options = data.get("options")
        _validate_mcq_options(options)
        _validate_answer_exists(answer, "MCQ")
        return Question(qtype=QUESTION_TYPE_MCQ, prompt=prompt, options=options, answer=answer, explanation=explanation)
    else:
        _validate_answer_exists(answer, "Short-answer question")
        return Question(qtype=QUESTION_TYPE_SHORT, prompt=prompt, options=None, answer=answer, explanation=explanation)


def _validate_question_type(qtype: Any) -> None:
    """
    Validate that question type is valid.
    
    Args:
        qtype: The question type to validate.
        
    Raises:
        ValueError: If type is invalid.
    """
    if not qtype or qtype not in VALID_QUESTION_TYPES:
        raise ValueError(f"Question 'type' must be one of {VALID_QUESTION_TYPES}")


def _validate_prompt(prompt: Any) -> None:
    """
    Validate that prompt is a non-empty string.
    
    Args:
        prompt: The prompt to validate.
        
    Raises:
        ValueError: If prompt is invalid.
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Question 'prompt' must be a non-empty string")


def _validate_mcq_options(options: Any) -> None:
    """
    Validate that MCQ options are a non-empty list of strings.
    
    Args:
        options: The options to validate.
        
    Raises:
        ValueError: If options are invalid.
    """
    if not isinstance(options, list) or not options or not all(isinstance(o, str) for o in options):
        raise ValueError("MCQ requires a non-empty 'options' list of strings")


def _validate_answer_exists(answer: Any, question_type: str) -> None:
    """
    Validate that an answer is provided.
    
    Args:
        answer: The answer to validate.
        question_type: The type of question (for error message).
        
    Raises:
        ValueError: If answer is missing.
    """
    if answer is None:
        raise ValueError(f"{question_type} requires an 'answer'")