"""
Pytest Fixtures and Global Configuration

Author: Akash Das
"""

import sys
from pathlib import Path
import pytest

# Ensure src/ is on sys.path for test discovery and execution
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_transaction_dict():
    """Return a baseline raw transaction dictionary for testing."""
    return {
        "date": "2026-11-01",
        "description": "Starbucks Coffee",
        "amount": 5.75,
        "category": "Dining",
        "payment_method": "Credit Card",
    }

