from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CATEGORY = "General"
INCOME_TYPE = "Income"
EXPENSE_TYPE = "Expense"
DATE_FORMAT = "%Y-%m-%d"
INITIAL_ID = 1
MIN_SAVINGS_GOAL = 0.0
ALL_CATEGORIES_FILTER = "All"


@dataclass
class Transaction:
    """Represents a single financial transaction.
    
    Attributes:
        id: Unique identifier for the transaction
        date: Date when the transaction occurred
        ttype: Transaction type - either "Income" or "Expense"
        category: Category classification for the transaction
        description: Human-readable description of the transaction
        amount: Transaction amount (always positive; sign inferred from ttype)
    """
    id: int
    date: date
    ttype: str
    category: str
    description: str
    amount: float

    def to_row(self) -> Tuple[int, date, str, str, str, float]:
        """Convert transaction to a row tuple for storage.
        
        Returns:
            Tuple containing all transaction fields in order
        """
        return (self.id, self.date, self.ttype, self.category, self.description, float(self.amount))

    @staticmethod
    def _parse_date(date_value) -> date:
        """Parse date from various input formats.
        
        Args:
            date_value: Date value in datetime, string, or date format
            
        Returns:
            Parsed date object, or today's date if parsing fails
        """
        if isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, DATE_FORMAT).date()
            except ValueError:
                logger.warning(f"Failed to parse date string: {date_value}, using today's date")
                return date.today()
        elif isinstance(date_value, date):
            return date_value
        else:
            logger.warning(f"Unexpected date type: {type(date_value)}, using today's date")
            return date.today()

    @staticmethod
    def _normalize_string(value: str, default: str = "") -> str:
        """Normalize string input with default fallback.
        
        Args:
            value: String value to normalize
            default: Default value if input is None or empty
            
        Returns:
            Normalized string or default value
        """
        return str(value).strip() if value is not None else default

    @staticmethod
    def from_row(row: Iterable) -> Transaction:
        """Create a Transaction from a row of data.
        
        Args:
            row: Iterable containing (ID, Date, Type, Category, Description, Amount)
            
        Returns:
            Transaction object constructed from row data
        """
        row_list = list(row)
        transaction_id = int(row_list[0])
        parsed_date = Transaction._parse_date(row_list[1])
        transaction_type = Transaction._normalize_string(row_list[2])
        category = Transaction._normalize_string(row_list[3], DEFAULT_CATEGORY)
        description = Transaction._normalize_string(row_list[4])
        amount = abs(float(row_list[5])) if row_list[5] is not None else 0.0

        return Transaction(
            id=transaction_id,
            date=parsed_date,
            ttype=transaction_type,
            category=category,
            description=description,
            amount=amount,
        )


class BudgetModel:
    """Model for managing budget transactions and categories.
    
    Manages a collection of transactions, categories, and savings goals.
    Provides methods for CRUD operations and financial analysis.
    """

    def __init__(self):
        """Initialize an empty budget model."""
        self.transactions: List[Transaction] = []
        self.categories: List[str] = [DEFAULT_CATEGORY]
        self.savings_goal: float = MIN_SAVINGS_GOAL
        self._next_id: int = INITIAL_ID

    def load(
        self,
        transactions: List[Transaction],
        categories: Iterable[str],
        savings_goal: float = MIN_SAVINGS_GOAL,
    ) -> None:
        """Load transactions, categories, and savings goal into the model.
        
        Args:
            transactions: List of Transaction objects to load
            categories: Iterable of category names to load
            savings_goal: Target savings goal amount
        """
        self.transactions = list(transactions)
        self.categories = self._deduplicate_categories(categories)
        self.savings_goal = float(savings_goal) if savings_goal is not None else MIN_SAVINGS_GOAL
        self._next_id = self._calculate_next_id()

    @staticmethod
    def _deduplicate_categories(categories: Iterable[str]) -> List[str]:
        """Remove duplicate categories while preserving order.
        
        Args:
            categories: Iterable of category names
            
        Returns:
            List of unique categories with DEFAULT_CATEGORY first
        """
        seen = set()
        unique_categories = []

        for category in categories:
            normalized = str(category).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_categories.append(normalized)

        # Ensure DEFAULT_CATEGORY is first
        if DEFAULT_CATEGORY not in seen:
            unique_categories.insert(0, DEFAULT_CATEGORY)
        elif unique_categories[0] != DEFAULT_CATEGORY:
            unique_categories.remove(DEFAULT_CATEGORY)
            unique_categories.insert(0, DEFAULT_CATEGORY)

        return unique_categories

    def _calculate_next_id(self) -> int:
        """Calculate the next available transaction ID.
        
        Returns:
            Next ID value based on maximum existing transaction ID
        """
        max_id = max((t.id for t in self.transactions), default=0)
        return max_id + 1

    def ensure_category(self, name: str) -> None:
        """Add a category if it doesn't already exist.
        
        Args:
            name: Category name to ensure exists
        """
        normalized_name = name.strip()
        if normalized_name and normalized_name not in self.categories:
            self.categories.append(normalized_name)

    def generate_next_id(self) -> int:
        """Generate and return the next transaction ID.
        
        Returns:
            Next available transaction ID
        """
        current_id = self._next_id
        self._next_id += 1
        return current_id

    @staticmethod
    def _normalize_transaction_type(ttype: str) -> str:
        """Normalize transaction type to standard format.
        
        Args:
            ttype: Transaction type string
            
        Returns:
            Normalized type: either "Income" or "Expense"
        """
        return INCOME_TYPE if ttype.lower().startswith("inc") else EXPENSE_TYPE

    def _sort_transactions(self) -> None:
        """Sort transactions by date then ID for consistent ordering."""
        self.transactions.sort(key=lambda x: (x.date, x.id))

    def add_transaction(
        self,
        tdate: date,
        ttype: str,
        category: str,
        description: str,
        amount: float,
    ) -> Transaction:
        """Add a new transaction to the model.
        
        Args:
            tdate: Transaction date
            ttype: Transaction type (Income or Expense)
            category: Transaction category
            description: Transaction description
            amount: Transaction amount
            
        Returns:
            Created Transaction object
        """
        normalized_type = self._normalize_transaction_type(ttype)
        normalized_amount = abs(float(amount))
        normalized_category = category.strip() or DEFAULT_CATEGORY

        self.ensure_category(normalized_category)

        transaction = Transaction(
            id=self.generate_next_id(),
            date=tdate,
            ttype=normalized_type,
            category=normalized_category,
            description=description.strip(),
            amount=normalized_amount,
        )
        self.transactions.append(transaction)
        self._sort_transactions()
        return transaction

    def edit_transaction(
        self,
        tx_id: int,
        tdate: date,
        ttype: str,
        category: str,
        description: str,
        amount: float,
    ) -> bool:
        """Edit an existing transaction.
        
        Args:
            tx_id: ID of transaction to edit
            tdate: New transaction date
            ttype: New transaction type
            category: New transaction category
            description: New transaction description
            amount: New transaction amount
            
        Returns:
            True if transaction was found and edited, False otherwise
        """
        transaction = self.get_transaction(tx_id)
        if not transaction:
            return False

        transaction.date = tdate
        transaction.ttype = self._normalize_transaction_type(ttype)
        transaction.category = category.strip() or DEFAULT_CATEGORY
        transaction.description = description.strip()
        transaction.amount = abs(float(amount))

        self.ensure_category(transaction.category)
        self._sort_transactions()
        return True

    def delete_transaction(self, tx_id: int) -> bool:
        """Delete a transaction by ID.
        
        Args:
            tx_id: ID of transaction to delete
            
        Returns:
            True if transaction was found and deleted, False otherwise
        """
        initial_count = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != tx_id]
        return len(self.transactions) < initial_count

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        """Retrieve a transaction by ID.
        
        Args:
            tx_id: ID of transaction to retrieve
            
        Returns:
            Transaction object if found, None otherwise
        """
        for transaction in self.transactions:
            if transaction.id == tx_id:
                return transaction
        return None

    def set_savings_goal(self, goal: float) -> None:
        """Set the savings goal amount.
        
        Args:
            goal: Target savings goal (negative values converted to 0)
        """
        self.savings_goal = max(MIN_SAVINGS_GOAL, float(goal))

    def totals(self) -> Dict[str, float]:
        """Calculate total income, expenses, and net amount.
        
        Returns:
            Dictionary with keys: income, expenses, net
        """
        income = sum(t.amount for t in self.transactions if t.ttype == INCOME_TYPE)
        expenses = sum(t.amount for t in self.transactions if t.ttype == EXPENSE_TYPE)
        net = income - expenses

        return {"income": income, "expenses": expenses, "net": net}

    def category_totals(self) -> Dict[str, float]:
        """Calculate total amount per category (signed by transaction type).
        
        Returns:
            Dictionary mapping category names to their net totals
        """
        category_amounts: Dict[str, float] = {}

        for transaction in self.transactions:
            # Income is positive, expenses are negative
            sign = 1 if transaction.ttype == INCOME_TYPE else -1
            current_total = category_amounts.get(transaction.category, 0.0)
            category_amounts[transaction.category] = current_total + (sign * transaction.amount)

        return category_amounts

    def filtered_transactions(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        ttype: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Transaction]:
        """Filter transactions by various criteria.
        
        Args:
            year: Filter by year (optional)
            month: Filter by month (optional)
            ttype: Filter by transaction type (optional)
            category: Filter by category (optional)
            search: Filter by description search term (optional)
            
        Returns:
            List of transactions matching all specified filters
        """
        normalized_type = self._normalize_filter_type(ttype)
        normalized_category = category.strip() if category else None
        normalized_search = search.strip().lower() if search else None

        filtered = []
        for transaction in self.transactions:
            if not self._matches_filters(
                transaction,
                year,
                month,
                normalized_type,
                normalized_category,
                normalized_search,
            ):
                continue
            filtered.append(transaction)

        return filtered

    @staticmethod
    def _normalize_filter_type(ttype: Optional[str]) -> Optional[str]:
        """Normalize transaction type filter value.
        
        Args:
            ttype: Transaction type filter string
            
        Returns:
            Normalized type or None if not a valid type
        """
        if not ttype:
            return None
        normalized = ttype.strip().lower()
        if normalized == "income":
            return INCOME_TYPE
        elif normalized == "expense":
            return EXPENSE_TYPE
        return None

    @staticmethod
    def _matches_filters(
        transaction: Transaction,
        year: Optional[int],
        month: Optional[int],
        ttype: Optional[str],
        category: Optional[str],
        search: Optional[str],
    ) -> bool:
        """Check if a transaction matches all specified filters.
        
        Args:
            transaction: Transaction to check
            year: Year filter
            month: Month filter
            ttype: Transaction type filter
            category: Category filter
            search: Search term filter
            
        Returns:
            True if transaction matches all filters, False otherwise
        """
        if year and transaction.date.year != year:
            return False
        if month and transaction.date.month != month:
            return False
        if ttype and transaction.ttype != ttype:
            return False
        if category and category != ALL_CATEGORIES_FILTER and transaction.category != category:
            return False
        if search and search not in (transaction.description or "").lower():
            return False
        return True