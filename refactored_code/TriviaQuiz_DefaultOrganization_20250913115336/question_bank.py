import json
import logging
from typing import Dict, List

from models import Question, question_from_dict

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_QUESTIONS_FOR_VALID_BANK = 1
JSON_ENCODING = "utf-8"
QUESTION_INDEX_START = 1


def _create_general_knowledge_bank() -> List[Question]:
    """
    Create and return the General Knowledge question bank.
    
    Returns:
        List[Question]: A list of general knowledge questions.
    """
    return [
        Question(
            qtype="mcq",
            prompt="Which planet is known as the Red Planet?",
            options=["Earth", "Mars", "Jupiter", "Venus"],
            answer=1
        ),
        Question(
            qtype="mcq",
            prompt="What is the capital city of France?",
            options=["Berlin", "Madrid", "Paris", "Rome"],
            answer="Paris"
        ),
        Question(
            qtype="short",
            prompt="In which continent is the Sahara Desert located?",
            answer=["africa", "the african continent"]
        ),
        Question(
            qtype="mcq",
            prompt="Which language is primarily spoken in Brazil?",
            options=["Spanish", "Portuguese", "French", "English"],
            answer="Portuguese"
        ),
        Question(
            qtype="short",
            prompt="What is the largest mammal on Earth?",
            answer=["blue whale", "the blue whale"]
        ),
        Question(
            qtype="mcq",
            prompt="Which of the following are prime numbers? (Select all that apply)",
            options=["2", "4", "9", "11"],
            answer=[0, 3],
            explanation="2 and 11 are prime; 4 and 9 are composite."
        ),
        Question(
            qtype="short",
            prompt="Who wrote the play 'Romeo and Juliet'?",
            answer=["William Shakespeare", "Shakespeare"]
        ),
        Question(
            qtype="mcq",
            prompt="Which ocean lies on the east coast of the United States?",
            options=["Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "Arctic Ocean"],
            answer=0
        ),
    ]


def _create_science_tech_bank() -> List[Question]:
    """
    Create and return the Science & Technology question bank.
    
    Returns:
        List[Question]: A list of science and technology questions.
    """
    return [
        Question(
            qtype="mcq",
            prompt="What does CPU stand for?",
            options=["Central Processing Unit", "Computer Personal Unit", "Central Print Unit", "Core Processing Utility"],
            answer="Central Processing Unit"
        ),
        Question(
            qtype="short",
            prompt="What is the chemical symbol for water?",
            answer=["H2O", "H₂O"]
        ),
        Question(
            qtype="mcq",
            prompt="Which company created the programming language Python?",
            options=["Google", "Microsoft", "Python Software Foundation", "It's open-source; originated by Guido van Rossum"],
            answer=3,
            explanation="Python was created by Guido van Rossum and is maintained by the community/PSF."
        ),
        Question(
            qtype="short",
            prompt="What particle has a negative electric charge?",
            answer=["electron"]
        ),
        Question(
            qtype="mcq",
            prompt="Which data structure uses FIFO (First In, First Out)?",
            options=["Stack", "Queue", "Tree", "Graph"],
            answer="Queue"
        ),
        Question(
            qtype="short",
            prompt="Name one programming paradigm that Python supports.",
            answer=["object-oriented", "functional", "procedural"]
        ),
    ]


def get_builtin_banks() -> Dict[str, List[Question]]:
    """
    Return a dictionary of built-in question banks.
    
    Returns:
        Dict[str, List[Question]]: A mapping of bank names to their question lists.
    """
    banks: Dict[str, List[Question]] = {
        "General Knowledge": _create_general_knowledge_bank(),
        "Science & Tech": _create_science_tech_bank(),
    }
    return banks


def _parse_question_from_dict(item: dict, question_index: int) -> tuple[Question | None, str | None]:
    """
    Attempt to parse a single question from a dictionary.
    
    Args:
        item: Dictionary representation of a question.
        question_index: The index of the question in the source list (1-based).
    
    Returns:
        tuple[Question | None, str | None]: A tuple of (Question object or None, error message or None).
            If parsing succeeds, returns (Question, None).
            If parsing fails, returns (None, error_message).
    """
    try:
        question = question_from_dict(item)
        return question, None
    except ValueError as e:
        error_message = f"Q{question_index}: {e}"
        return None, error_message
    except KeyError as e:
        error_message = f"Q{question_index}: Missing required field {e}"
        return None, error_message
    except TypeError as e:
        error_message = f"Q{question_index}: Invalid data type {e}"
        return None, error_message


def load_bank_from_json(path: str) -> List[Question]:
    """
    Load a question bank from a JSON file.
    
    The JSON file should contain a list of question objects. Example:
    [
      {
        "type": "mcq",
        "prompt": "What is 2+2?",
        "options": ["3","4","5","22"],
        "answer": 1
      },
      {
        "type": "short",
        "prompt": "Name a primary color",
        "answer": ["red","blue","yellow"]
      }
    ]
    
    Args:
        path: File path to the JSON question bank file.
    
    Returns:
        List[Question]: A list of successfully parsed Question objects.
    
    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON root is not a list or no valid questions could be parsed.
    """
    try:
        with open(path, "r", encoding=JSON_ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError as e:
        logger.error(f"Question bank file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {path}: {e}")
        raise

    # Validate that root element is a list
    if not isinstance(data, list):
        error_message = "Root of JSON must be a list of questions"
        logger.error(error_message)
        raise ValueError(error_message)

    questions: List[Question] = []
    errors: List[str] = []

    # Parse each question and collect errors
    for question_index, item in enumerate(data, start=QUESTION_INDEX_START):
        parsed_question, error_message = _parse_question_from_dict(item, question_index)
        
        if parsed_question is not None:
            questions.append(parsed_question)
        else:
            errors.append(error_message)
            logger.warning(error_message)

    # Raise error if no questions were successfully parsed
    if not questions:
        combined_errors = "; ".join(errors)
        error_message = f"No valid questions parsed. Errors: {combined_errors}"
        logger.error(error_message)
        raise ValueError(error_message)

    # Log summary of parsing results
    if errors:
        logger.info(f"Loaded {len(questions)} questions with {len(errors)} parsing errors")
    else:
        logger.info(f"Successfully loaded {len(questions)} questions")

    return questions