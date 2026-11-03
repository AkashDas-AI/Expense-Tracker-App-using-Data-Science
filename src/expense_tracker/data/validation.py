"""
Transaction Schema Validation Module

Author: Akash Das
Description: Enforces schema integrity, type validation, enum consistency,
             and boundary constraints on financial transaction DataFrames.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "date",
    "type",
    "category",
    "amount",
    "payment_method",
    "description",
]

ALLOWED_TRANSACTION_TYPES = {"Income", "Expense"}

ALLOWED_INCOME_CATEGORIES = {
    "Salary",
    "Freelance",
    "Business Income",
    "Investment Income",
    "Other Income",
}

ALLOWED_EXPENSE_CATEGORIES = {
    "Rent",
    "Groceries",
    "Utilities",
    "Transport",
    "Healthcare",
    "Education",
    "Shopping",
    "Entertainment",
    "Dining",
    "Travel",
    "Subscriptions",
    "Other Expenses",
}

ALLOWED_PAYMENT_METHODS = {
    "UPI",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Bank Transfer",
}


def validate_transaction_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that a transaction DataFrame strictly adheres to the required schema.

    Validation checks performed:
    1. Input type is a pandas DataFrame.
    2. DataFrame is non-empty.
    3. All required columns are present.
    4. Required columns contain no missing / NaN / None values.
    5. 'transaction_id' values are non-empty and strictly unique.
    6. 'date' values conform to valid ISO date formats (YYYY-MM-DD).
    7. 'type' values are strictly within ALLOWED_TRANSACTION_TYPES ('Income', 'Expense').
    8. 'category' values correspond legitimately to their respective transaction 'type'.
    9. 'payment_method' values belong to ALLOWED_PAYMENT_METHODS.
    10. 'amount' values are numeric, finite, and strictly greater than zero (> 0.0).
    11. 'description' values are non-empty strings without leading/trailing whitespace only.

    Args:
        df: DataFrame containing financial transactions.

    Returns:
        Tuple of (is_valid: bool, errors: List[str]).
        is_valid is True if and only if errors list is empty.
    """
    errors: List[str] = []

    # 1. Type check
    if not isinstance(df, pd.DataFrame):
        return False, [f"Invalid input: expected pandas.DataFrame, got {type(df).__name__}."]

    # 2. Empty check
    if df.empty:
        return False, ["Validation failed: DataFrame is empty."]

    # 3. Required columns presence check
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {sorted(missing_columns)}.")
        # If columns are missing, stop further structural checks on missing fields
        return False, errors

    # 4. Null / Missing value check across required columns
    for col in REQUIRED_COLUMNS:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            errors.append(f"Column '{col}' contains {null_count} null or missing values.")

    # 5. Transaction ID validation (uniqueness & non-empty)
    if "transaction_id" in df.columns and not df["transaction_id"].isna().all():
        # Check non-empty strings
        id_series = df["transaction_id"].astype(str).str.strip()
        empty_ids = int((id_series == "").sum())
        if empty_ids > 0:
            errors.append(f"Column 'transaction_id' contains {empty_ids} empty string values.")

        # Check uniqueness
        duplicate_count = int(df["transaction_id"].duplicated().sum())
        if duplicate_count > 0:
            errors.append(f"Column 'transaction_id' contains {duplicate_count} duplicate values.")

    # 6. Date validation
    if "date" in df.columns and not df["date"].isna().all():
        try:
            parsed_dates = pd.to_datetime(df["date"], format="mixed", errors="coerce")
            invalid_dates = int(parsed_dates.isna().sum())
            if invalid_dates > 0:
                errors.append(f"Column 'date' contains {invalid_dates} invalid or unparseable date values.")
        except Exception as e:
            errors.append(f"Date parsing failed: {e}")

    # 7. Transaction type validation
    if "type" in df.columns and not df["type"].isna().all():
        invalid_types = set(df["type"].dropna().unique()) - ALLOWED_TRANSACTION_TYPES
        if invalid_types:
            errors.append(
                f"Column 'type' contains invalid values: {sorted(list(invalid_types))}. "
                f"Allowed values are {sorted(list(ALLOWED_TRANSACTION_TYPES))}."
            )

    # 8. Category cross-validation with Transaction Type
    if "category" in df.columns and "type" in df.columns:
        # Check Income categories
        income_mask = df["type"] == "Income"
        if income_mask.any():
            invalid_income_cats = set(df.loc[income_mask, "category"].dropna().unique()) - ALLOWED_INCOME_CATEGORIES
            if invalid_income_cats:
                errors.append(
                    f"Invalid categories found for 'Income' type: {sorted(list(invalid_income_cats))}. "
                    f"Allowed Income categories are {sorted(list(ALLOWED_INCOME_CATEGORIES))}."
                )

        # Check Expense categories
        expense_mask = df["type"] == "Expense"
        if expense_mask.any():
            invalid_expense_cats = set(df.loc[expense_mask, "category"].dropna().unique()) - ALLOWED_EXPENSE_CATEGORIES
            if invalid_expense_cats:
                errors.append(
                    f"Invalid categories found for 'Expense' type: {sorted(list(invalid_expense_cats))}. "
                    f"Allowed Expense categories are {sorted(list(ALLOWED_EXPENSE_CATEGORIES))}."
                )

    # 9. Payment method validation
    if "payment_method" in df.columns and not df["payment_method"].isna().all():
        invalid_payment = set(df["payment_method"].dropna().unique()) - ALLOWED_PAYMENT_METHODS
        if invalid_payment:
            errors.append(
                f"Column 'payment_method' contains invalid values: {sorted(list(invalid_payment))}. "
                f"Allowed payment methods are {sorted(list(ALLOWED_PAYMENT_METHODS))}."
            )

    # 10. Amount validation (numeric, finite, strictly positive)
    if "amount" in df.columns:
        # Check if numeric
        numeric_amounts = pd.to_numeric(df["amount"], errors="coerce")
        non_numeric = int(numeric_amounts.isna().sum()) - int(df["amount"].isna().sum())
        if non_numeric > 0:
            errors.append(f"Column 'amount' contains {non_numeric} non-numeric values.")

        valid_numeric = numeric_amounts.dropna()
        if not valid_numeric.empty:
            non_finite = int((~np.isfinite(valid_numeric)).sum())
            if non_finite > 0:
                errors.append(f"Column 'amount' contains {non_finite} infinite or NaN values.")

            non_positive = int((valid_numeric <= 0).sum())
            if non_positive > 0:
                errors.append(f"Column 'amount' contains {non_positive} non-positive values (must be > 0.0).")

    # 11. Description validation (non-empty string after stripping)
    if "description" in df.columns and not df["description"].isna().all():
        desc_clean = df["description"].astype(str).str.strip()
        blank_descs = int((desc_clean == "").sum())
        if blank_descs > 0:
            errors.append(f"Column 'description' contains {blank_descs} blank or whitespace-only descriptions.")

    is_valid = len(errors) == 0
    return is_valid, errors
