import csv
import logging
from typing import Iterable

from palindrome_detector import PalindromeMatch

# CSV export configuration
CSV_ENCODING = "utf-8"
CSV_NEWLINE = ""
CSV_HEADERS = ["Category", "Content", "Normalized", "Length", "Line", "StartCol", "EndCol"]

logger = logging.getLogger(__name__)


def _extract_match_row(match: PalindromeMatch) -> list:
    """
    Extract match data into a list for CSV row writing.
    
    Args:
        match: A PalindromeMatch object containing palindrome detection results.
        
    Returns:
        A list containing match attributes in the order of CSV_HEADERS.
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
    Write palindrome detection results to a CSV file.
    
    Args:
        path: File path where CSV will be written.
        results: Iterable of PalindromeMatch objects to export.
        
    Raises:
        IOError: If the file cannot be written.
        ValueError: If results contain invalid data.
    """
    try:
        _write_csv_file(path, results)
        logger.info(f"Successfully exported results to {path}")
    except IOError as e:
        logger.error(f"Failed to write CSV file at {path}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data in results: {e}")
        raise


def _write_csv_file(path: str, results: Iterable[PalindromeMatch]) -> None:
    """
    Write CSV file with headers and match data rows.
    
    Args:
        path: File path where CSV will be written.
        results: Iterable of PalindromeMatch objects to export.
        
    Raises:
        IOError: If file operations fail.
    """
    with open(path, "w", newline=CSV_NEWLINE, encoding=CSV_ENCODING) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADERS)
        _write_match_rows(writer, results)


def _write_match_rows(writer: csv.writer, results: Iterable[PalindromeMatch]) -> None:
    """
    Write all match rows to CSV writer.
    
    Args:
        writer: CSV writer instance.
        results: Iterable of PalindromeMatch objects to write.
    """
    for match in results:
        row = _extract_match_row(match)
        writer.writerow(row)