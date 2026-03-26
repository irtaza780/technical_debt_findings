from dataclasses import dataclass
from typing import Any, List, Optional, Union, Iterable, Set
import re
import logging

logger = logging.getLogger(__name__)

# Constants
QUESTION_TYPE_MCQ = "mcq"
QUESTION_TYPE_SHORT = "short"
VALID_QUESTION_TYPES = {QUESTION_TYPE_MCQ, QUESTION_TYPE_SHORT}
ANSWER_NOT_AVAILABLE = "N/A"
INVALID_INDEX = -1


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
    # Collapse multiple whitespace characters into single space
    text = re.sub(r"\s+", " ", text)
    return text


def _convert_to_int(value: Any) -> Optional[int]:
    """
    Safely convert a value to an integer.
    
    Args:
        value: The value to convert.
        
    Returns:
        Integer value if conversion succeeds, None otherwise.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _find_option_index_by_text(options: List[str], text: str) -> int:
    """
    Find the index of an option by matching normalized text.
    
    Args:
        options: List of option strings.
        text: The text to match.
        
    Returns:
        Index of matching option, or INVALID_INDEX if not found.
    """
    text_normalized = normalize_text(text)
    for index, option in enumerate(options):
        if normalize_text(option) == text_normalized:
            return index
    return INVALID_INDEX


def _extract_answer_indices(answer: Any, options: List[str]) -> Set[int]:
    """
    Extract valid option indices from an answer value.
    
    Handles answer as int, str (option text), or list of ints/strings.
    
    Args:
        answer: The answer value (int, str, or list).
        options: List of available options for validation.
        
    Returns:
        Set of valid option indices.
    """
    indices: Set[int] = set()
    
    if isinstance(answer, list):
        for item in answer:
            if isinstance(item, int):
                if 0 <= item < len(options):
                    indices.add(item)
            elif isinstance(item, str):
                index = _find_option_index_by_text(options, item)
                if index >= 0:
                    indices.add(index)
    elif isinstance(answer, int):
        if 0 <= answer < len(options):
            indices.add(answer)
    elif isinstance(answer, str):
        index = _find_option_index_by_text(options, answer)
        if index >= 0:
            indices.add(index)
    
    return indices


@dataclass
class Question:
    """
    Represents a quiz question with support for multiple-choice and short-answer formats.
    
    Attributes:
        qtype: Question type - "mcq" for multiple-choice or "short" for short-answer.
        prompt: The question text.
        options: For MCQ, list of option strings. None for short-answer.
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
        Check if the user's answer is correct.
        
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
        Check if a multiple-choice answer is correct.
        
        Args:
            user_answer: The user's selected option(s).
            
        Returns:
            True if the answer matches the correct option(s).
        """
        correct_indices = self._mcq_correct_indices()
        if not correct_indices:
            return False
        
        # Handle multiple selections
        if isinstance(user_answer, (list, tuple, set)):
            selected_indices = self._extract_user_indices(user_answer)
            return selected_indices == correct_indices
        
        # Handle single selection
        user_index = _convert_to_int(user_answer)
        if user_index is None:
            return False
        
        # Single selection only matches if exactly one correct answer exists
        return len(correct_indices) == 1 and user_index in correct_indices

    def _extract_user_indices(self, user_selections: Iterable[Any]) -> Set[int]:
        """
        Extract valid indices from user's multiple selections.
        
        Args:
            user_selections: Iterable of user-selected indices.
            
        Returns:
            Set of valid indices.
        """
        selected_indices: Set[int] = set()
        for item in user_selections:
            index = _convert_to_int(item)
            if index is not None:
                selected_indices.add(index)
        return selected_indices

    def _is_short_answer_correct(self, user_answer: Any) -> bool:
        """
        Check if a short-answer is correct.
        
        Args:
            user_answer: The user's text answer.
            
        Returns:
            True if the answer matches an acceptable answer.
        """
        if user_answer is None:
            return False
        
        user_answer_normalized = normalize_text(str(user_answer))
        acceptable_answers = self._short_acceptable_answers()
        return user_answer_normalized in acceptable_answers

    def get_correct_answer_text(self) -> str:
        """
        Get a human-readable string of the correct answer(s).
        
        Returns:
            Formatted string of correct answer(s).
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_mcq_correct_answer_text()
        else:
            return self._get_short_answer_text()

    def _get_mcq_correct_answer_text(self) -> str:
        """
        Get formatted text of correct MCQ option(s).
        
        Returns:
            Comma-separated option texts or ANSWER_NOT_AVAILABLE.
        """
        indices = sorted(self._mcq_correct_indices())
        if not self.options or not indices:
            return ANSWER_NOT_AVAILABLE
        
        texts = [self.options[i] for i in indices if 0 <= i < len(self.options)]
        return ", ".join(texts) if texts else ANSWER_NOT_AVAILABLE

    def _get_short_answer_text(self) -> str:
        """
        Get formatted text of acceptable short answers.
        
        Returns:
            Comma-separated acceptable answers or ANSWER_NOT_AVAILABLE.
        """
        acceptable = self._short_acceptable_answers(raw=True)
        return ", ".join(acceptable) if acceptable else ANSWER_NOT_AVAILABLE

    def get_user_answer_text(self, user_answer: Any) -> str:
        """
        Get a human-readable string of the user's answer.
        
        Args:
            user_answer: The user's submitted answer.
            
        Returns:
            Formatted string representation of the answer.
        """
        if self.qtype == QUESTION_TYPE_MCQ:
            return self._get_mcq_user_answer_text(user_answer)
        else:
            return str(user_answer) if user_answer is not None else ANSWER_NOT_AVAILABLE

    def _get_mcq_user_answer_text(self, user_answer: Any) -> str:
        """
        Get formatted text of user's MCQ selection(s).
        
        Args:
            user_answer: The user's selected option(s).
            
        Returns:
            Formatted option text(s) or ANSWER_NOT_AVAILABLE.
        """
        if isinstance(user_answer, (list, tuple, set)):
            return self._indices_to_option_texts(user_answer)
        
        user_index = _convert_to_int(user_answer)
        if user_index is None:
            return ANSWER_NOT_AVAILABLE
        
        if self.options and 0 <= user_index < len(self.options):
            return self.options[user_index]
        
        return f"Option #{user_index + 1}"

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
        Extract correct option indices for MCQ questions.
        
        Handles answer as int, str (option text), or list of ints/strings.
        
        Returns:
            Set of correct option indices.
        """
        if self.options is None or self.answer is None:
            return set()
        
        return _extract_answer_indices(self.answer, self.options)

    def _short_acceptable_answers(self, raw: bool = False) -> List[str]:
        """
        Get list of acceptable answers for short-answer questions.
        
        Args:
            raw: If True, return un-normalized strings for display.
                 If False, return normalized strings for comparison.
        
        Returns:
            List of acceptable answer strings.
        """
        if self.answer is None:
            return []
        
        answers = self._extract_answer_strings()
        
        if raw:
            return answers
        
        return [normalize_text(answer) for answer in answers]

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
        Convert indices to comma-separated option text.
        
        Args:
            indices: Collection of option indices.
            
        Returns:
            Formatted option texts or ANSWER_NOT_AVAILABLE.
        """
        if not self.options:
            return ANSWER_NOT_AVAILABLE
        
        # Preserve order for list/tuple; sort for set for determinism
        ordered_indices = list(indices) if not isinstance(indices, set) else sorted(indices)
        texts: List[str] = []
        
        for item in ordered_indices:
            index = _convert_to_int(item)
            if index is None:
                continue
            
            if 0 <= index < len(self.options):
                texts.append(self.options[index])
            else:
                texts.append(f"Option #{index + 1}")
        
        return ", ".join(texts) if texts else ANSWER_NOT_AVAILABLE


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
        return Question(
            qtype=QUESTION_TYPE_MCQ,
            prompt=prompt,
            options=options,
            answer=answer,
            explanation=explanation
        )
    else:
        _validate_answer_exists(answer, "Short-answer question")
        return Question(
            qtype=QUESTION_TYPE_SHORT,
            prompt=prompt,
            options=None,
            answer=answer,
            explanation=explanation
        )


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
    if not isinstance(options, list) or not options:
        raise ValueError("MCQ requires a non-empty 'options' list")
    
    if not all(isinstance(option, str) for option in options):
        raise ValueError("MCQ 'options' must all be strings")


def _validate_answer_exists(answer: Any, question_type: str) -> None:
    """
    Validate that an answer is provided.
    
    Args:
        answer: The answer to validate.
        question_type: Description of question type for error message.
        
    Raises:
        ValueError: If answer is None.
    """
    if answer is None:
        raise ValueError(f"{question_type} requires an 'answer'")