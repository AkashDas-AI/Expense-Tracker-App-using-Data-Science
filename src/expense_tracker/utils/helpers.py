"""
Helper Utilities Module

Author: Akash Das
Description: Shared utility functions for currency formatting, percentages, date handling, and logging.
"""

from datetime import datetime
from typing import Optional, Union
import numpy as np
import pandas as pd


def format_currency(
    amount: Optional[Union[int, float]],
    currency_symbol: str = "₹",
    default: str = "N/A",
) -> str:
    """Format numeric value into readable currency string in Indian Rupees (₹ / INR).

    Handles negative values cleanly (-₹1,250.00 rather than ₹-1,250.00) and
    safely handles None/NaN inputs.

    Args:
        amount: Numeric amount to format.
        currency_symbol: Currency symbol prefix (defaults to '₹').
        default: Fallback string if amount is None or NaN.

    Returns:
        Formatted string (e.g., '₹1,250.00' or '-₹2,607,419.99').
    """
    if amount is None or pd.isna(amount) or np.isneginf(amount) or np.isposinf(amount):
        return default

    amount_val = float(amount)
    if amount_val < 0:
        return f"-{currency_symbol}{abs(amount_val):,.2f}"
    return f"{currency_symbol}{amount_val:,.2f}"


def format_percentage(
    value: Optional[Union[int, float]],
    include_sign: bool = False,
    default: str = "N/A",
) -> str:
    """Format numeric ratio or rate into a readable percentage string.

    Args:
        value: Numeric percentage value (e.g. 53.85 for 53.85%).
        include_sign: Whether to include explicit '+' for positive rates.
        default: Fallback string if value is None or NaN.

    Returns:
        Formatted string (e.g., '53.85%', '+12.40%', '-38.59%').
    """
    if value is None or pd.isna(value) or np.isneginf(value) or np.isposinf(value):
        return default

    val_float = float(value)
    if include_sign and val_float > 0:
        return f"+{val_float:.2f}%"
    return f"{val_float:.2f}%"


def parse_date_safely(date_str: str) -> datetime:
    """Parse string date safely into datetime object.

    Args:
        date_str: String representation of a date.

    Returns:
        Parsed datetime object.
    """
    from dateutil import parser
    return parser.parse(date_str)
