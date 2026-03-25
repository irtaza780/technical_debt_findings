import logging
from typing import Any, List, Dict, Tuple, Optional
from models import Question

# Configuration constants
MIN_VALID_INDEX = 0
SCORE_INCREMENT = 1

# Configure logging
logger = logging.getLogger(__name__)


class QuizSession:
    """
    Manages a quiz session including question tracking, answer submission, and scoring.
    
    Attributes:
        questions: List of Question objects to be presented in the quiz.
        show_answers: Flag to control whether answers are shown to the user.
        current_index: Index of the current question being answered.
        score: Number of correctly answered questions.
        records: List of answer records containing question, user answer, and correctness.
    """

    def __init__(self, questions: List[Question], show_answers: bool = False) -> None:
        """
        Initialize a quiz session with a list of questions.
        
        Args:
            questions: List of Question objects for the quiz.
            show_answers: Whether to display correct answers (default: False).
            
        Raises:
            ValueError: If questions is not a list of Question objects.
        """
        self._validate_questions(questions)
        self.questions: List[Question] = questions
        self.show_answers: bool = show_answers
        self.current_index: int = MIN_VALID_INDEX
        self.score: int = MIN_VALID_INDEX
        self.records: List[Dict[str, Any]] = []

    @staticmethod
    def _validate_questions(questions: Any) -> None:
        """
        Validate that questions parameter is a list of Question objects.
        
        Args:
            questions: The questions to validate.
            
        Raises:
            ValueError: If questions is not a list or contains non-Question objects.
        """
        if not isinstance(questions, list):
            raise ValueError("questions must be a list of Question objects")
        if not all(isinstance(q, Question) for q in questions):
            raise ValueError("questions must be a list of Question objects")

    def current_question(self) -> Optional[Question]:
        """
        Retrieve the current question being answered.
        
        Returns:
            The current Question object, or None if no valid question exists.
        """
        if self._is_valid_index(self.current_index):
            return self.questions[self.current_index]
        return None

    def _is_valid_index(self, index: int) -> bool:
        """
        Check if an index is within valid bounds of the questions list.
        
        Args:
            index: The index to validate.
            
        Returns:
            True if index is valid, False otherwise.
        """
        return MIN_VALID_INDEX <= index < len(self.questions)

    def submit_answer(self, user_answer: Any) -> None:
        """
        Submit an answer for the current question and advance to the next.
        
        Args:
            user_answer: The user's answer to the current question.
            
        Logs:
            Warning if no current question exists.
        """
        current_q = self.current_question()
        if current_q is None:
            logger.warning("Attempted to submit answer with no current question")
            return

        # Evaluate answer correctness
        is_answer_correct = current_q.is_correct(user_answer)
        
        # Update score if answer is correct
        if is_answer_correct:
            self.score += SCORE_INCREMENT

        # Record the answer attempt
        self._record_answer(current_q, user_answer, is_answer_correct)
        
        # Advance to next question
        self.current_index += 1

    def _record_answer(self, question: Question, user_answer: Any, is_correct: bool) -> None:
        """
        Record an answer attempt in the session history.
        
        Args:
            question: The Question object that was answered.
            user_answer: The user's submitted answer.
            is_correct: Whether the answer was correct.
        """
        answer_record = {
            "question": question,
            "user_answer": user_answer,
            "correct": is_correct
        }
        self.records.append(answer_record)

    def has_next(self) -> bool:
        """
        Check if there are more questions remaining in the quiz.
        
        Returns:
            True if there are unanswered questions, False otherwise.
        """
        return self._is_valid_index(self.current_index)

    def results(self) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Retrieve the final quiz results.
        
        Returns:
            Tuple containing:
                - score: Number of correctly answered questions.
                - total: Total number of questions in the quiz.
                - records: List of all answer records.
        """
        total_questions = len(self.questions)
        return self.score, total_questions, self.records