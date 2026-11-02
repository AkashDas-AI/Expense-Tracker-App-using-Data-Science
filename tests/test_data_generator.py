"""Tests for data generation module scaffolding."""

import pytest
from expense_tracker.data.data_generator import generate_synthetic_transactions


def test_generate_synthetic_transactions_scaffolding():
    """Verify function signature and scaffolding placeholder behavior."""
    with pytest.raises(NotImplementedError, match="Phase 2"):
        generate_synthetic_transactions(num_records=10)

