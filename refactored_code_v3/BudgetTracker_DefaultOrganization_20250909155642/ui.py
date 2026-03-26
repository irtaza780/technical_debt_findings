import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from typing import Optional

from models import BudgetModel, Transaction
from utils import format_currency, parse_float, parse_date, date_to_str

# Configuration constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600
PADDING_STANDARD = 8
PADDING_SMALL = 4
PADDING_FORM = 6

COLOR_INCOME = "#1a7f37"
COLOR_EXPENSE = "#b91c1c"

COLUMN_ID_WIDTH = 60
COLUMN_DATE_WIDTH = 110
COLUMN_TYPE_WIDTH = 90
COLUMN_CATEGORY_WIDTH = 160
COLUMN_DESCRIPTION_WIDTH = 340
COLUMN_AMOUNT_WIDTH = 120

DEFAULT_CATEGORY = "General"
DEFAULT_TRANSACTION_TYPE = "Expense"
PROGRESS_MIN = 0.0
PROGRESS_MAX = 100.0

logger = logging.getLogger(__name__)


class BudgetApp(tk.Tk):
    """Main application window for Budget Tracker."""

    def __init__(self, model: BudgetModel, storage: "ExcelStorage") -> None:
        """
        Initialize the Budget Tracker application.

        Args:
            model: BudgetModel instance containing transaction data
            storage: ExcelStorage instance for persistence
        """
        super().__init__()
        self.title("Budget Tracker - Expenses and Savings")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.model = model
        self.storage = storage

        self._init_state_variables()
        self._build_ui()
        self._refresh_all()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_state_variables(self) -> None:
        """Initialize all Tkinter StringVar and state variables."""
        # Edit state
        self._edit_tx_id: Optional[int] = None

        # Filter variables
        self._filter_year = tk.StringVar(value="All")
        self._filter_month = tk.StringVar(value="All")
        self._filter_type = tk.StringVar(value="All")
        self._filter_category = tk.StringVar(value="All")
        self._filter_search = tk.StringVar(value="")

        # Summary display variables
        self.var_income = tk.StringVar(value="$0.00")
        self.var_expenses = tk.StringVar(value="$0.00")
        self.var_net = tk.StringVar(value="$0.00")
        self.var_goal = tk.StringVar(value="$0.00")
        self.var_progress_text = tk.StringVar(value="0% of goal")

    def _build_ui(self) -> None:
        """Build all UI components."""
        self._build_summary_frame()
        self._build_form_frame()
        self._build_filter_frame()
        self._build_table_frame()

    def _build_summary_frame(self) -> None:
        """Build the summary statistics frame."""
        frame = ttk.Frame(self, padding=PADDING_STANDARD)
        frame.pack(fill="x")

        # Income row
        ttk.Label(frame, text="Income:", width=10).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame, textvariable=self.var_income, foreground=COLOR_INCOME, width=18
        ).grid(row=0, column=1, sticky="w")

        # Expenses row
        ttk.Label(frame, text="Expenses:", width=10).grid(row=0, column=2, sticky="w")
        ttk.Label(
            frame, textvariable=self.var_expenses, foreground=COLOR_EXPENSE, width=18
        ).grid(row=0, column=3, sticky="w")

        # Net row
        ttk.Label(frame, text="Net:", width=10).grid(row=0, column=4, sticky="w")
        ttk.Label(frame, textvariable=self.var_net, width=18).grid(row=0, column=5, sticky="w")

        # Savings goal row
        self._build_savings_goal_row(frame)

        # Configure column weights
        for i in range(6):
            frame.columnconfigure(i, weight=1)

    def _build_savings_goal_row(self, parent: ttk.Frame) -> None:
        """
        Build the savings goal input and progress bar row.

        Args:
            parent: Parent frame to add widgets to
        """
        ttk.Label(parent, text="Savings goal:", width=14).grid(
            row=1, column=0, sticky="w", pady=(PADDING_SMALL, 0)
        )

        self.entry_goal = ttk.Entry(parent)
        self.entry_goal.grid(row=1, column=1, sticky="we", pady=(PADDING_SMALL, 0))
        self.entry_goal.insert(0, f"{self.model.savings_goal:.2f}")

        btn_set_goal = ttk.Button(parent, text="Set goal", command=self._on_set_goal)
        btn_set_goal.grid(row=1, column=2, padx=PADDING_FORM, pady=(PADDING_SMALL, 0))

        self.progress = ttk.Progressbar(parent, mode="determinate")
        self.progress.grid(
            row=1, column=3, columnspan=2, sticky="we", padx=PADDING_FORM, pady=(PADDING_SMALL, 0)
        )

        ttk.Label(parent, textvariable=self.var_progress_text).grid(
            row=1, column=5, sticky="w", pady=(PADDING_SMALL, 0)
        )

    def _build_form_frame(self) -> None:
        """Build the transaction form frame."""
        lf = ttk.LabelFrame(self, text="Add / Edit Transaction", padding=PADDING_STANDARD)
        lf.pack(fill="x", padx=PADDING_STANDARD, pady=PADDING_SMALL)

        self._build_form_date_field(lf)
        self._build_form_type_field(lf)
        self._build_form_category_field(lf)
        self._build_form_description_field(lf)
        self._build_form_amount_field(lf)
        self._build_form_submit_button(lf)

        # Configure column weights
        for i in range(5):
            lf.columnconfigure(i, weight=1)

    def _build_form_date_field(self, parent: ttk.Frame) -> None:
        """Build date input field."""
        ttk.Label(parent, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        self.entry_date = ttk.Entry(parent, width=16)
        self.entry_date.grid(row=1, column=0, sticky="w", padx=(0, PADDING_FORM))
        self.entry_date.insert(0, date_to_str(date.today()))

    def _build_form_type_field(self, parent: ttk.Frame) -> None:
        """Build transaction type radio buttons."""
        ttk.Label(parent, text="Type").grid(row=0, column=1, sticky="w")
        self.type_var = tk.StringVar(value=DEFAULT_TRANSACTION_TYPE)
        frm_type = ttk.Frame(parent)
        frm_type.grid(row=1, column=1, sticky="w", padx=(0, PADDING_FORM))
        ttk.Radiobutton(
            frm_type, text="Expense", value="Expense", variable=self.type_var
        ).pack(side="left", padx=(0, PADDING_FORM))
        ttk.Radiobutton(
            frm_type, text="Income", value="Income", variable=self.type_var
        ).pack(side="left")

    def _build_form_category_field(self, parent: ttk.Frame) -> None:
        """Build category selection and addition fields."""
        ttk.Label(parent, text="Category").grid(row=0, column=2, sticky="w")
        self.combo_category = ttk.Combobox(
            parent, values=self.model.categories, state="readonly", width=24
        )
        self.combo_category.grid(row=1, column=2, sticky="we", padx=(0, PADDING_FORM))
        self._set_category_combo_default()

        self.entry_new_category = ttk.Entry(parent, width=18)
        self.entry_new_category.grid(row=1, column=3, sticky="we")

        btn_add_cat = ttk.Button(parent, text="Add category", command=self._on_add_category)
        btn_add_cat.grid(row=1, column=4, padx=(PADDING_FORM, 0))

    def _set_category_combo_default(self) -> None:
        """Set category combobox to default value."""
        default = self.model.categories[0] if self.model.categories else DEFAULT_CATEGORY
        self.combo_category.set(default)

    def _build_form_description_field(self, parent: ttk.Frame) -> None:
        """Build description input field."""
        ttk.Label(parent, text="Description").grid(row=2, column=0, sticky="w", pady=(PADDING_FORM, 0))
        self.entry_description = ttk.Entry(parent, width=40)
        self.entry_description.grid(
            row=3, column=0, columnspan=2, sticky="we", padx=(0, PADDING_FORM)
        )

    def _build_form_amount_field(self, parent: ttk.Frame) -> None:
        """Build amount input field."""
        ttk.Label(parent, text="Amount").grid(row=2, column=2, sticky="w", pady=(PADDING_FORM, 0))
        self.entry_amount = ttk.Entry(parent, width=18)
        self.entry_amount.grid(row=3, column=2, sticky="w", padx=(0, PADDING_FORM))

    def _build_form_submit_button(self, parent: ttk.Frame) -> None:
        """Build form submission button."""
        self.btn_submit = ttk.Button(parent, text="Add", command=self._on_submit)
        self.btn_submit.grid(row=3, column=4, sticky="e")

    def _build_filter_frame(self) -> None:
        """Build the filters frame."""
        lf = ttk.LabelFrame(self, text="Filters", padding=PADDING_STANDARD)
        lf.pack(fill="x", padx=PADDING_STANDARD, pady=(0, PADDING_SMALL))

        self._build_filter_year_field(lf)
        self._build_filter_month_field(lf)
        self._build_filter_type_field(lf)
        self._build_filter_category_field(lf)
        self._build_filter_search_field(lf)
        self._build_filter_buttons(lf)

        # Configure column weights
        for i in range(7):
            lf.columnconfigure(i, weight=1)

    def _build_filter_year_field(self, parent: ttk.Frame) -> None:
        """Build year filter dropdown."""
        ttk.Label(parent, text="Year").grid(row=0, column=0, sticky="w")
        self.combo_year = ttk.Combobox(
            parent, textvariable=self._filter_year, state="readonly", width=10
        )
        self.combo_year.grid(row=1, column=0, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_month_field(self, parent: ttk.Frame) -> None:
        """Build month filter dropdown."""
        ttk.Label(parent, text="Month").grid(row=0, column=1, sticky="w")
        self.combo_month = ttk.Combobox(
            parent, textvariable=self._filter_month, state="readonly", width=10
        )
        self.combo_month.grid(row=1, column=1, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_type_field(self, parent: ttk.Frame) -> None:
        """Build type filter dropdown."""
        ttk.Label(parent, text="Type").grid(row=0, column=2, sticky="w")
        self.combo_type = ttk.Combobox(
            parent, textvariable=self._filter_type, state="readonly", width=12
        )
        self.combo_type.grid(row=1, column=2, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_category_field(self, parent: ttk.Frame) -> None:
        """Build category filter dropdown."""
        ttk.Label(parent, text="Category").grid(row=0, column=3, sticky="w")
        self.combo_filter_category = ttk.Combobox(
            parent, textvariable=self._filter_category, state="readonly", width=22
        )
        self.combo_filter_category.grid(row=1, column=3, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_search_field(self, parent: ttk.Frame) -> None:
        """Build search filter input."""
        ttk.Label(parent, text="Search").grid(row=0, column=4, sticky="w")
        self.entry_search = ttk.Entry(parent, textvariable=self._filter_search, width=24)
        self.entry_search.grid(row=1, column=4, sticky="we", padx=(0, PADDING_FORM))

    def _build_filter_buttons(self, parent: ttk.Frame) -> None:
        """Build filter action buttons."""
        btn_apply = ttk.Button(parent, text="Apply", command=self._on_apply_filters)
        btn_apply.grid(row=1, column=5, sticky="w", padx=(0, PADDING_FORM))

        btn_reset = ttk.Button(parent, text="Reset", command=self._on_reset_filters)
        btn_reset.grid(row=1, column=6, sticky="w", padx=(0, PADDING_FORM))

    def _build_table_frame(self) -> None:
        """Build the transactions table frame."""
        frame = ttk.Frame(self, padding=PADDING_STANDARD)
        frame.pack(fill="both", expand=True)

        self._build_treeview(frame)
        self._build_table_buttons(frame)

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_treeview(self, parent: ttk.Frame) -> None:
        """
        Build the transactions treeview table.

        Args:
            parent: Parent frame for the treeview
        """
        columns = ("ID", "Date", "Type", "Category", "Description", "Amount")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")

        # Set column headings
        for col in columns:
            self.tree.heading(col, text=col)

        # Configure column widths and alignment
        self.tree.column("ID", width=COLUMN_ID_WIDTH, anchor="e")
        self.tree.column("Date", width=COLUMN_DATE_WIDTH, anchor="center")
        self.tree.column("Type", width=COLUMN_TYPE_WIDTH, anchor="center")
        self.tree.column("Category", width=COLUMN_CATEGORY_WIDTH, anchor="w")
        self.tree.column("Description", width=COLUMN_DESCRIPTION_WIDTH, anchor="w")