import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from typing import Optional

from models import BudgetModel, Transaction
from utils import format_currency, parse_float, parse_date, date_to_str

# Configure logging
logger = logging.getLogger(__name__)

# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600
PADDING_STANDARD = 8
PADDING_SMALL = 4
PADDING_FORM = 6

# Color Constants
COLOR_INCOME = "#1a7f37"
COLOR_EXPENSE = "#b91c1c"

# Column widths for transaction table
COLUMN_WIDTHS = {
    "ID": 60,
    "Date": 110,
    "Type": 90,
    "Category": 160,
    "Description": 340,
    "Amount": 120,
}

# Transaction table columns
TABLE_COLUMNS = ("ID", "Date", "Type", "Category", "Description", "Amount")

# Filter options
FILTER_TYPES = ["All", "Income", "Expense"]
MONTHS_LIST = ["All"] + [str(m) for m in range(1, 13)]

# Default values
DEFAULT_CATEGORY = "General"
DEFAULT_GOAL_VALUE = 0.0
PROGRESS_MIN = 0.0
PROGRESS_MAX = 100.0


class BudgetApp(tk.Tk):
    """Main Budget Tracker application window."""

    def __init__(self, model: BudgetModel, storage):
        """
        Initialize the Budget Tracker application.

        Args:
            model: BudgetModel instance containing transaction data
            storage: Storage backend for persisting data
        """
        super().__init__()
        self.title("Budget Tracker - Expenses and Savings")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.model = model
        self.storage = storage

        # State for filters and edit
        self._edit_tx_id: Optional[int] = None
        self._filter_year = tk.StringVar(value="All")
        self._filter_month = tk.StringVar(value="All")
        self._filter_type = tk.StringVar(value="All")
        self._filter_category = tk.StringVar(value="All")
        self._filter_search = tk.StringVar(value="")

        # Summary variables
        self.var_income = tk.StringVar(value="$0.00")
        self.var_expenses = tk.StringVar(value="$0.00")
        self.var_net = tk.StringVar(value="$0.00")
        self.var_goal = tk.StringVar(value="$0.00")
        self.var_progress_text = tk.StringVar(value="0% of goal")

        self._build_ui()
        self._refresh_summary()
        self._refresh_filters()
        self._refresh_table()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        ttk.Label(frame, textvariable=self.var_income, foreground=COLOR_INCOME, width=18).grid(
            row=0, column=1, sticky="w"
        )

        # Expenses row
        ttk.Label(frame, text="Expenses:", width=10).grid(row=0, column=2, sticky="w")
        ttk.Label(frame, textvariable=self.var_expenses, foreground=COLOR_EXPENSE, width=18).grid(
            row=0, column=3, sticky="w"
        )

        # Net row
        ttk.Label(frame, text="Net:", width=10).grid(row=0, column=4, sticky="w")
        ttk.Label(frame, textvariable=self.var_net, width=18).grid(row=0, column=5, sticky="w")

        # Savings goal row
        ttk.Label(frame, text="Savings goal:", width=14).grid(row=1, column=0, sticky="w", pady=(PADDING_FORM, 0))
        self.entry_goal = ttk.Entry(frame)
        self.entry_goal.grid(row=1, column=1, sticky="we", pady=(PADDING_FORM, 0))
        self.entry_goal.insert(0, f"{self.model.savings_goal:.2f}")

        btn_set_goal = ttk.Button(frame, text="Set goal", command=self._on_set_goal)
        btn_set_goal.grid(row=1, column=2, padx=PADDING_FORM, pady=(PADDING_FORM, 0))

        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.grid(row=1, column=3, columnspan=2, sticky="we", padx=PADDING_FORM, pady=(PADDING_FORM, 0))

        ttk.Label(frame, textvariable=self.var_progress_text).grid(row=1, column=5, sticky="w", pady=(PADDING_FORM, 0))

        # Configure column weights
        for i in range(6):
            frame.columnconfigure(i, weight=1)

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
        """Build date input field in form."""
        ttk.Label(parent, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        self.entry_date = ttk.Entry(parent, width=16)
        self.entry_date.grid(row=1, column=0, sticky="w", padx=(0, PADDING_STANDARD))
        self.entry_date.insert(0, date_to_str(date.today()))

    def _build_form_type_field(self, parent: ttk.Frame) -> None:
        """Build transaction type radio buttons in form."""
        ttk.Label(parent, text="Type").grid(row=0, column=1, sticky="w")
        self.type_var = tk.StringVar(value="Expense")
        frm_type = ttk.Frame(parent)
        frm_type.grid(row=1, column=1, sticky="w", padx=(0, PADDING_STANDARD))
        ttk.Radiobutton(frm_type, text="Expense", value="Expense", variable=self.type_var).pack(
            side="left", padx=(0, PADDING_STANDARD)
        )
        ttk.Radiobutton(frm_type, text="Income", value="Income", variable=self.type_var).pack(side="left")

    def _build_form_category_field(self, parent: ttk.Frame) -> None:
        """Build category selection and addition fields in form."""
        ttk.Label(parent, text="Category").grid(row=0, column=2, sticky="w")
        self.combo_category = ttk.Combobox(parent, values=self.model.categories, state="readonly", width=24)
        self.combo_category.grid(row=1, column=2, sticky="we", padx=(0, PADDING_STANDARD))
        self.combo_category.set(self.model.categories[0] if self.model.categories else DEFAULT_CATEGORY)

        self.entry_new_category = ttk.Entry(parent, width=18)
        self.entry_new_category.grid(row=1, column=3, sticky="we")

        btn_add_cat = ttk.Button(parent, text="Add category", command=self._on_add_category)
        btn_add_cat.grid(row=1, column=4, padx=(PADDING_FORM, 0))

    def _build_form_description_field(self, parent: ttk.Frame) -> None:
        """Build description input field in form."""
        ttk.Label(parent, text="Description").grid(row=2, column=0, sticky="w", pady=(PADDING_STANDARD, 0))
        self.entry_description = ttk.Entry(parent, width=40)
        self.entry_description.grid(row=3, column=0, columnspan=2, sticky="we", padx=(0, PADDING_STANDARD))

    def _build_form_amount_field(self, parent: ttk.Frame) -> None:
        """Build amount input field in form."""
        ttk.Label(parent, text="Amount").grid(row=2, column=2, sticky="w", pady=(PADDING_STANDARD, 0))
        self.entry_amount = ttk.Entry(parent, width=18)
        self.entry_amount.grid(row=3, column=2, sticky="w", padx=(0, PADDING_STANDARD))

    def _build_form_submit_button(self, parent: ttk.Frame) -> None:
        """Build submit button in form."""
        self.btn_submit = ttk.Button(parent, text="Add", command=self._on_submit)
        self.btn_submit.grid(row=3, column=4, sticky="e")

    def _build_filter_frame(self) -> None:
        """Build the filters frame."""
        lf = ttk.LabelFrame(self, text="Filters", padding=PADDING_STANDARD)
        lf.pack(fill="x", padx=PADDING_STANDARD, pady=(0, PADDING_SMALL))

        years = self._get_available_years()
        categories = self._get_available_categories()

        self._build_filter_year_field(lf, years)
        self._build_filter_month_field(lf)
        self._build_filter_type_field(lf)
        self._build_filter_category_field(lf, categories)
        self._build_filter_search_field(lf)
        self._build_filter_buttons(lf)

        # Configure column weights
        for i in range(7):
            lf.columnconfigure(i, weight=1)

    def _build_filter_year_field(self, parent: ttk.Frame, years: list) -> None:
        """Build year filter field."""
        ttk.Label(parent, text="Year").grid(row=0, column=0, sticky="w")
        self.combo_year = ttk.Combobox(parent, values=years, textvariable=self._filter_year, state="readonly", width=10)
        self.combo_year.grid(row=1, column=0, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_month_field(self, parent: ttk.Frame) -> None:
        """Build month filter field."""
        ttk.Label(parent, text="Month").grid(row=0, column=1, sticky="w")
        self.combo_month = ttk.Combobox(
            parent, values=MONTHS_LIST, textvariable=self._filter_month, state="readonly", width=10
        )
        self.combo_month.grid(row=1, column=1, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_type_field(self, parent: ttk.Frame) -> None:
        """Build type filter field."""
        ttk.Label(parent, text="Type").grid(row=0, column=2, sticky="w")
        self.combo_type = ttk.Combobox(
            parent, values=FILTER_TYPES, textvariable=self._filter_type, state="readonly", width=12
        )
        self.combo_type.grid(row=1, column=2, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_category_field(self, parent: ttk.Frame, categories: list) -> None:
        """Build category filter field."""
        ttk.Label(parent, text="Category").grid(row=0, column=3, sticky="w")
        self.combo_filter_category = ttk.Combobox(
            parent, values=categories, textvariable=self._filter_category, state="readonly", width=22
        )
        self.combo_filter_category.grid(row=1, column=3, sticky="w", padx=(0, PADDING_FORM))

    def _build_filter_search_field(self, parent: ttk.Frame) -> None:
        """Build search filter field."""
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
        """Build the transaction table frame."""
        frame = ttk.Frame(self, padding=PADDING_STANDARD)
        frame.pack(fill="both", expand=True)

        self._build_treeview(frame)
        self._build_table_buttons(frame)

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_treeview(self, parent: ttk.Frame) -> None:
        """Build the transaction treeview table."""
        self.tree = ttk.Treeview(parent, columns=TABLE_COLUMNS, show="headings", selectmode="browse")

        # Configure column headings and widths
        for col in TABLE_COLUMNS:
            self.tree.heading(col, text=col)
            width = COLUMN_WIDTHS.get(col, 100)
            anchor = "e" if col in ("ID", "Amount") else ("center" if col in ("Date", "Type") else "w")
            self.tree.column(col, width=width, anchor=anchor)

        # Configure scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        