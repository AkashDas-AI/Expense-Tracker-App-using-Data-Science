"""
Helper Utilities Module

Author: Akash Das
Description: Shared utility functions for formatting, date handling, and logging.
"""

from datetime import datetime
from typing import Union


def format_currency(amount: Union[int, float], currency_symbol: str = "$") -> str:
    """Format numeric value into readable currency string.

    Args:
        amount: Numeric amount to format.
        currency_symbol: Currency symbol prefix (defaults to '$').

    Returns:
        Formatted string (e.g., '$1,250.00').
    """
    return f"{currency_symbol}{amount:,.2f}"


def parse_date_safely(date_str: str) -> datetime:
    """Parse string date safely into datetime object.

    Args:
        date_str: String representation of a date.

    Returns:
        Parsed datetime object.
    """
    from dateutil import parser
    return parser.parse(date_str)

