"""
Database Operations Module

Author: Akash Das
Description: Schema initialization, CRUD operations, parameterized queries,
             and transactional integrity for the SQLite storage layer.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from expense_tracker.database.connection import get_db_connection, get_db_context


CREATE_TRANSACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
    category TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('UPI', 'Cash', 'Debit Card', 'Credit Card', 'Bank Transfer')),
    description TEXT NOT NULL,
    CHECK (
        (type = 'Income' AND category IN (
            'Salary', 'Freelance', 'Business Income', 'Investment Income', 'Other Income'
        ))
        OR
        (type = 'Expense' AND category IN (
            'Rent', 'Groceries', 'Utilities', 'Transport', 'Healthcare',
            'Education', 'Shopping', 'Entertainment', 'Dining', 'Travel',
            'Subscriptions', 'Other Expenses'
        ))
    )
);
"""

CREATE_TRANSACTIONS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
"""


def initialize_database(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize database tables, schema constraints, and performance indices.

    Args:
        db_path: Optional path to target SQLite database.
    """
    with get_db_context(db_path) as conn:
        with conn:
            conn.execute(CREATE_TRANSACTIONS_TABLE_SQL)
            conn.executescript(CREATE_TRANSACTIONS_INDEX_SQL)


def transaction_exists(
    transaction_id: str,
    db_path: Optional[Union[str, Path]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Check whether a transaction ID already exists in the transactions table.

    Args:
        transaction_id: Unique transaction identifier to verify.
        db_path: Optional path to target SQLite database.
        conn: Optional existing open sqlite3 connection.

    Returns:
        bool: True if transaction exists, False otherwise.
    """
    query = "SELECT 1 FROM transactions WHERE transaction_id = ? LIMIT 1;"

    if conn is not None:
        cursor = conn.execute(query, (transaction_id,))
        return cursor.fetchone() is not None

    with get_db_context(db_path) as local_conn:
        cursor = local_conn.execute(query, (transaction_id,))
        return cursor.fetchone() is not None


def insert_transaction(
    record: Dict[str, Any],
    db_path: Optional[Union[str, Path]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Insert a single transaction dictionary into the database.

    Args:
        record: Dictionary with transaction fields matching schema.
        db_path: Optional path to target SQLite database.
        conn: Optional existing open sqlite3 connection.

    Returns:
        bool: True if inserted, False if skipped due to existing ID.

    Raises:
        sqlite3.IntegrityError: If constraints fail (e.g. non-positive amount or invalid type).
    """
    insert_sql = """
    INSERT INTO transactions (
        transaction_id, date, type, category, amount, payment_method, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    params = (
        str(record["transaction_id"]),
        str(record["date"]),
        str(record["type"]),
        str(record["category"]),
        float(record["amount"]),
        str(record["payment_method"]),
        str(record["description"]),
    )

    if conn is not None:
        conn.execute(insert_sql, params)
        return True

    with get_db_context(db_path) as local_conn:
        with local_conn:
            local_conn.execute(insert_sql, params)
        return True


def insert_transactions(
    df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
    on_conflict: str = "skip",
) -> int:
    """Insert multiple transactions from a DataFrame into SQLite.

    Duplicate Handling Policy:
    - on_conflict == "skip" (default): Checks existing IDs in database and within batch;
      existing transaction IDs are skipped without overwriting existing data.
      Only new, unique records are inserted.
    - on_conflict == "fail": Attempts insert directly; raises sqlite3.IntegrityError
      if duplicate IDs exist and rolls back the transaction atomically.

    Transaction Atomicity:
    All insertions occur inside an atomic database transaction context. If any row
    violates a table constraint (e.g. negative amount, invalid type), the entire
    batch operation is rolled back to prevent inconsistent partial state.

    Args:
        df: DataFrame conforming to transaction schema.
        db_path: Optional path to target SQLite database.
        on_conflict: Conflict resolution policy ('skip' or 'fail').

    Returns:
        int: Total number of rows successfully inserted.

    Raises:
        ValueError: If DataFrame is missing required columns or on_conflict is unrecognized.
        sqlite3.IntegrityError: If constraints fail or on_conflict == 'fail' with duplicates.
    """
    if df.empty:
        return 0

    required = ["transaction_id", "date", "type", "category", "amount", "payment_method", "description"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Cannot insert transactions: missing required columns {missing}.")

    if on_conflict not in ("skip", "fail"):
        raise ValueError(f"Unknown on_conflict policy '{on_conflict}'. Must be 'skip' or 'fail'.")

    # Ensure schema initialized
    initialize_database(db_path)

    insert_sql = """
    INSERT INTO transactions (
        transaction_id, date, type, category, amount, payment_method, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """

    inserted_count = 0

    with get_db_context(db_path) as conn:
        with conn:  # Context manager starts atomic transaction
            if on_conflict == "skip":
                # Find existing IDs in DB to skip them
                cursor = conn.execute("SELECT transaction_id FROM transactions;")
                existing_ids = {row[0] for row in cursor.fetchall()}

                # Track seen IDs in current batch to prevent duplicates within input df
                seen_batch_ids = set()

                batch_params: List[Tuple[Any, ...]] = []
                for _, row in df.iterrows():
                    tid = str(row["transaction_id"])
                    if tid in existing_ids or tid in seen_batch_ids:
                        continue
                    seen_batch_ids.add(tid)
                    batch_params.append((
                        tid,
                        str(row["date"]),
                        str(row["type"]),
                        str(row["category"]),
                        float(row["amount"]),
                        str(row["payment_method"]),
                        str(row["description"]),
                    ))

                if batch_params:
                    conn.executemany(insert_sql, batch_params)
                    inserted_count = len(batch_params)

            else:  # on_conflict == "fail"
                batch_params = [
                    (
                        str(row["transaction_id"]),
                        str(row["date"]),
                        str(row["type"]),
                        str(row["category"]),
                        float(row["amount"]),
                        str(row["payment_method"]),
                        str(row["description"]),
                    )
                    for _, row in df.iterrows()
                ]
                conn.executemany(insert_sql, batch_params)
                inserted_count = len(batch_params)

    return inserted_count


def query_transactions(
    filters: Optional[Dict[str, Any]] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Retrieve transactions from SQLite as a DataFrame with optional parameterized filters.

    Supported filters:
    - 'start_date': Minimum transaction date (inclusive, 'YYYY-MM-DD').
    - 'end_date': Maximum transaction date (inclusive, 'YYYY-MM-DD').
    - 'type': 'Income' or 'Expense'.
    - 'category': Specific category string or list of category strings.
    - 'payment_method': Payment method string or list of payment methods.
    - 'min_amount': Minimum amount (inclusive).
    - 'max_amount': Maximum amount (inclusive).

    Args:
        filters: Dictionary of query constraints.
        db_path: Optional path to target SQLite database.

    Returns:
        pd.DataFrame containing matching transactions.
    """
    initialize_database(db_path)

    base_query = """
    SELECT transaction_id, date, type, category, amount, payment_method, description
    FROM transactions
    """
    clauses: List[str] = []
    params: List[Any] = []

    if filters:
        if "start_date" in filters and filters["start_date"]:
            clauses.append("date >= ?")
            params.append(str(filters["start_date"]))

        if "end_date" in filters and filters["end_date"]:
            clauses.append("date <= ?")
            params.append(str(filters["end_date"]))

        if "type" in filters and filters["type"]:
            clauses.append("type = ?")
            params.append(str(filters["type"]))

        if "category" in filters and filters["category"]:
            cat = filters["category"]
            if isinstance(cat, (list, tuple, set)):
                placeholders = ", ".join(["?"] * len(cat))
                clauses.append(f"category IN ({placeholders})")
                params.extend([str(c) for c in cat])
            else:
                clauses.append("category = ?")
                params.append(str(cat))

        if "payment_method" in filters and filters["payment_method"]:
            pm = filters["payment_method"]
            if isinstance(pm, (list, tuple, set)):
                placeholders = ", ".join(["?"] * len(pm))
                clauses.append(f"payment_method IN ({placeholders})")
                params.extend([str(m) for m in pm])
            else:
                clauses.append("payment_method = ?")
                params.append(str(pm))

        if "min_amount" in filters and filters["min_amount"] is not None:
            clauses.append("amount >= ?")
            params.append(float(filters["min_amount"]))

        if "max_amount" in filters and filters["max_amount"] is not None:
            clauses.append("amount <= ?")
            params.append(float(filters["max_amount"]))

    if clauses:
        base_query += " WHERE " + " AND ".join(clauses)

    base_query += " ORDER BY date ASC, transaction_id ASC;"

    with get_db_context(db_path) as conn:
        cursor = conn.execute(base_query, params)
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]

    if not rows:
        return pd.DataFrame(columns=[
            "transaction_id", "date", "type", "category", "amount", "payment_method", "description"
        ])

    return pd.DataFrame([dict(row) for row in rows], columns=cols)
