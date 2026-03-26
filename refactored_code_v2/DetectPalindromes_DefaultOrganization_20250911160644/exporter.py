import csv
import logging
from typing import Iterable

from palindrome_detector import PalindromeMatch

# CSV export configuration
CSV_ENCODING = "utf-8"
CSV_HEADERS = ["Category", "Content", "Normalized", "Length", "Line", "StartCol", "EndCol"]

logger = logging.getLogger(__name__)


def _extract_match_row(match: PalindromeMatch) -> list:
    """
    Extract match data into a list for CSV row writing.
    
    Args:
        match: A PalindromeMatch object containing palindrome detection results.
        
    Returns:
        A list containing match attributes in the order matching CSV_HEADERS.
    """
    return [
        match.category,
        match.text,
        match.normalized,
        match.length,
        match.line_no,
        match.start_pos,
        match.end_pos,
    ]


def export_results_to_csv(path: str, results: Iterable[PalindromeMatch]) -> None:
    """
    Write palindrome detection results to a CSV file with headers.
    
    Args:
        path: File path where CSV will be written.
        results: Iterable of PalindromeMatch objects to export.
        
    Raises:
        IOError: If the file cannot be written.
        ValueError: If results contain invalid data.
    """
    try:
        with open(path, "w", newline="", encoding=CSV_ENCODING) as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADERS)
            
            # Write each match as a row, extracting data in consistent order
            for match in results:
                row = _extract_match_row(match)
                writer.writerow(row)
        
        logger.info(f"Successfully exported results to {path}")
        
    except IOError as io_error:
        logger.error(f"Failed to write CSV file at {path}: {io_error}")
        raise
    except ValueError as value_error:
        logger.error(f"Invalid data encountered during CSV export: {value_error}")
        raise