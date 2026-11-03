"""SQLite database management and persistence module."""

from expense_tracker.database.connection import get_db_connection, get_db_context
from expense_tracker.database.operations import (
    initialize_database,
    insert_transaction,
    insert_transactions,
    query_transactions,
    transaction_exists,
)

__all__ = [
    "get_db_connection",
    "get_db_context",
    "initialize_database",
    "insert_transaction",
    "insert_transactions",
    "query_transactions",
    "transaction_exists",
]
