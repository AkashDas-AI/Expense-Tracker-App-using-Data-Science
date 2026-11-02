"""Tests for database operations scaffolding."""

import pytest
from expense_tracker.database.connection import get_db_connection
from expense_tracker.database.operations import initialize_database


def test_database_connection_scaffolding():
    """Verify database connection scaffolding placeholder."""
    with pytest.raises(NotImplementedError):
        get_db_connection()


def test_initialize_database_scaffolding():
    """Verify database initialization scaffolding placeholder."""
    with pytest.raises(NotImplementedError):
        initialize_database()

