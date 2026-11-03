"""
Database Connection Module

Author: Akash Das
Description: SQLite connection lifecycle management with path configuration,
             parent directory auto-creation, and context-managed cleanup.
"""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator, Optional, Union
from expense_tracker.config.settings import DATABASE_PATH


def get_db_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Establish and return an SQLite database connection.

    Ensures the parent directory exists, enables foreign keys, and configures
    row factory for dictionary-like column access.

    Args:
        db_path: Path to SQLite database file. Defaults to settings.DATABASE_PATH.

    Returns:
        sqlite3.Connection object.

    Raises:
        sqlite3.Error: If the database cannot be opened or initialized.
    """
    if db_path is None:
        target_path = DATABASE_PATH
    else:
        target_path = Path(db_path)

    try:
        # Automatically create directory structure if not already present
        if target_path != Path(":memory:"):
            target_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(target_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to connect to database at '{target_path}': {e}") from e


@contextmanager
def get_db_context(db_path: Optional[Union[str, Path]] = None) -> Iterator[sqlite3.Connection]:
    """Context manager for SQLite database connection and guaranteed closure.

    Args:
        db_path: Path to SQLite database file.

    Yields:
        sqlite3.Connection: Active database connection.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
