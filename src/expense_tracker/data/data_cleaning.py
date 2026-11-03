"""
Data Cleaning Module

Author: Akash Das
Description: Non-destructive transaction data cleaning, text normalization,
             date standardization, and numeric coercion. Reuses schema validation
             without silently dropping invalid rows.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from expense_tracker.data.validation import (
    ALLOWED_TRANSACTION_TYPES,
    ALLOWED_INCOME_CATEGORIES,
    ALLOWED_EXPENSE_CATEGORIES,
    ALLOWED_PAYMENT_METHODS,
    REQUIRED_COLUMNS,
    validate_transaction_schema,
)

# Explicitly supported date formats: ISO, Slash ISO, and Indian DD-MM-YYYY
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y")


def parse_explicit_date(val: Any) -> Optional[str]:
    """Parse a date value strictly using supported explicit formats:
    - YYYY-MM-DD (%Y-%m-%d)
    - YYYY/MM/DD (%Y/%m/%d)
    - DD-MM-YYYY (%d-%m-%Y)

    Interprets DD-MM-YYYY (e.g. '01-02-2026') as Day-Month-Year (1 February 2026).
    ISO dates (e.g. '2026-02-01') resolve to 1 February 2026.
    Rejects invalid dates (e.g. '2026-02-31') and unsupported formats (e.g. MM/DD/YYYY).

    Args:
        val: Raw date input (string, datetime, or Timestamp).

    Returns:
        ISO formatted 'YYYY-MM-DD' string if valid, None otherwise.
    """
    if val is None or pd.isna(val):
        return None

    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("nan", "none", "nat", ""):
        return None

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None

# Canonical lookup dictionaries for case-insensitive normalization
_TYPE_LOOKUP = {t.lower(): t for t in ALLOWED_TRANSACTION_TYPES}
_PAYMENT_LOOKUP = {p.lower(): p for p in ALLOWED_PAYMENT_METHODS}
_CATEGORY_LOOKUP = {
    c.lower(): c
    for c in (list(ALLOWED_INCOME_CATEGORIES) + list(ALLOWED_EXPENSE_CATEGORIES))
}


def clean_transactions(
    df: pd.DataFrame,
    return_report: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Dict[str, Any]]]:
    """Clean and normalize a transaction DataFrame without silently dropping rows.

    Transformations performed:
    1. Input isolation: Creates a deep copy so input DataFrame is never mutated.
    2. Empty DataFrame handling: Returns empty DataFrame immediately.
    3. Whitespace trimming: Strips leading/trailing spaces across all text columns.
    4. Text normalization:
       - 'type' normalized to canonical casing ('Income', 'Expense').
       - 'category' normalized to canonical taxonomy casing.
       - 'payment_method' normalized to canonical casing ('UPI', 'Credit Card', etc.).
    5. Date standardization: Parses diverse date formats into standard 'YYYY-MM-DD'.
    6. Amount coercion: Coerces numeric strings, strips currency symbols ('₹', '$', commas),
       and converts to float rounded to 2 decimal places.
    7. Validation & reporting: Reuses Phase 2 schema validator to check the cleaned
       dataset and reports any invalid rows and reasons.

    Args:
        df: Input raw transaction DataFrame.
        return_report: If True, returns a tuple of (cleaned_df, cleaning_report).
                       If False (default), returns cleaned_df.

    Returns:
        pd.DataFrame or Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned DataFrame,
        optionally accompanied by the validation and quality report.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        report: Dict[str, Any] = {
            "total_rows": 0,
            "is_valid": False,
            "validation_errors": ["DataFrame is empty."],
            "invalid_rows_count": 0,
            "invalid_records": [],
        }
        return (df.copy(), report) if return_report else df.copy()

    # Deep copy to guarantee no unexpected mutation of caller's DataFrame
    cleaned = df.copy()

    # 1. Whitespace trimming for all string/object columns
    text_columns = ["transaction_id", "date", "type", "category", "payment_method", "description"]
    for col in text_columns:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.strip()

    # 2. Normalize 'type'
    if "type" in cleaned.columns:
        cleaned["type"] = cleaned["type"].apply(
            lambda x: _TYPE_LOOKUP.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )

    # 3. Normalize 'payment_method'
    if "payment_method" in cleaned.columns:
        cleaned["payment_method"] = cleaned["payment_method"].apply(
            lambda x: _PAYMENT_LOOKUP.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )

    # 4. Normalize 'category'
    if "category" in cleaned.columns:
        cleaned["category"] = cleaned["category"].apply(
            lambda x: _CATEGORY_LOOKUP.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )

    # 5. Standardize dates to ISO YYYY-MM-DD using explicit supported formats
    # Enforces explicit formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY (01-02-2026 -> 2026-02-01).
    # Rejects invalid dates (e.g. 2026-02-31) and unsupported / ambiguous formats (e.g. MM/DD/YYYY).
    date_format_errors: List[str] = []
    if "date" in cleaned.columns:
        parsed_dates = []
        for idx, val in cleaned["date"].items():
            parsed = parse_explicit_date(val)
            parsed_dates.append(parsed)
            if val is not None and pd.notna(val) and str(val).strip() not in ("", "nan", "none", "nat") and parsed is None:
                date_format_errors.append(
                    f"Row {idx}: Date '{val}' is invalid or does not match supported formats ('YYYY-MM-DD', 'YYYY/MM/DD', 'DD-MM-YYYY')."
                )
        cleaned["date"] = parsed_dates

    # 6. Normalize amounts (strip currency symbols and commas if present, convert to numeric)
    if "amount" in cleaned.columns:
        if not pd.api.types.is_numeric_dtype(cleaned["amount"]):
            # Remove symbols like ₹, $, commas, and extra whitespace
            clean_amount_str = (
                cleaned["amount"]
                .astype(str)
                .str.replace("₹", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            cleaned["amount"] = pd.to_numeric(clean_amount_str, errors="coerce")
        else:
            cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")

        # Round numeric values to 2 decimal places
        cleaned["amount"] = cleaned["amount"].round(2)

    # 7. Quality audit using Phase 2 schema validator
    is_valid, validation_errors = validate_transaction_schema(cleaned)
    if date_format_errors:
        is_valid = False
        validation_errors = list(validation_errors) + date_format_errors

    # Identify any individual invalid rows for detailed reporting
    invalid_records: List[Dict[str, Any]] = []
    if not is_valid:
        for idx, row in cleaned.iterrows():
            row_df = pd.DataFrame([row])
            row_valid, row_errs = validate_transaction_schema(row_df)
            row_date_errs = [err for err in date_format_errors if err.startswith(f"Row {idx}:")]
            if not row_valid or row_date_errs:
                invalid_records.append({
                    "row_index": idx,
                    "transaction_id": row.get("transaction_id", "N/A"),
                    "reasons": list(row_errs) + row_date_errs,
                })

    report = {
        "total_rows": len(cleaned),
        "is_valid": is_valid,
        "validation_errors": validation_errors,
        "invalid_rows_count": len(invalid_records),
        "invalid_records": invalid_records,
    }

    if return_report:
        return cleaned, report

    return cleaned


def inspect_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect data quality of a transaction DataFrame and return validation report.

    Args:
        df: Transaction DataFrame to inspect.

    Returns:
        Dict detailing validity, error messages, and list of invalid records.
    """
    _, report = clean_transactions(df, return_report=True)
    return report
