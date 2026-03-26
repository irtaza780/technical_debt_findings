import json
import logging
from typing import Dict, List

from models import Question, question_from_dict

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_QUESTIONS_FOR_VALID_BANK = 1
JSON_ENCODING = "utf-8"
GENERAL_KNOWLEDGE_BANK = "General Knowledge"
SCIENCE_TECH_BANK = "Science & Tech"


def _create_general_knowledge_questions() -> List[Question]:
    """
    Create the General Knowledge question bank.
    
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


def _create_science_tech_questions() -> List[Question]:
    """
    Create the Science & Technology question bank.
    
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
    Retrieve all built-in question banks.
    
    Returns:
        Dict[str, List[Question]]: A dictionary mapping bank names to their questions.
    """
    banks: Dict[str, List[Question]] = {
        GENERAL_KNOWLEDGE_BANK: _create_general_knowledge_questions(),
        SCIENCE_TECH_BANK: _create_science_tech_questions(),
    }
    return banks


def _parse_question_from_json_item(item: dict, item_index: int) -> tuple[Question | None, str | None]:
    """
    Attempt to parse a single question from a JSON item.
    
    Args:
        item: A dictionary representing a question.
        item_index: The 1-based index of the item in the JSON list.
    
    Returns:
        tuple[Question | None, str | None]: A tuple of (Question, None) on success,
            or (None, error_message) on failure.
    """
    try:
        question = question_from_dict(item)
        return question, None
    except ValueError as e:
        error_message = f"Q{item_index}: {e}"
        logger.warning(error_message)
        return None, error_message
    except KeyError as e:
        error_message = f"Q{item_index}: Missing required field {e}"
        logger.warning(error_message)
        return None, error_message
    except TypeError as e:
        error_message = f"Q{item_index}: Invalid data type {e}"
        logger.warning(error_message)
        return None, error_message


def load_bank_from_json(path: str) -> List[Question]:
    """
    Load a question bank from a JSON file.
    
    The JSON file should contain a list of question objects with the following structure:
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
        path: The file path to the JSON question bank.
    
    Returns:
        List[Question]: A list of successfully parsed questions.
    
    Raises:
        ValueError: If the JSON root is not a list or if no valid questions are parsed.
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
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

    # Validate that the root element is a list
    if not isinstance(data, list):
        error_msg = "Root of JSON must be a list of questions"
        logger.error(error_msg)
        raise ValueError(error_msg)

    questions: List[Question] = []
    errors: List[str] = []

    # Parse each question item
    for idx, item in enumerate(data, start=1):
        question, error = _parse_question_from_json_item(item, idx)
        if question is not None:
            questions.append(question)
        else:
            errors.append(error)

    # If no questions were successfully parsed, raise an error
    if len(questions) < MIN_QUESTIONS_FOR_VALID_BANK:
        error_summary = "; ".join(errors)
        error_msg = f"No valid questions parsed. Errors: {error_summary}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Successfully loaded {len(questions)} questions from {path}")
    return questions