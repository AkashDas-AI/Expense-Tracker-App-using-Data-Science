"""Dashboard presentation package."""

import sys
from pathlib import Path

# Ensure src/ directory is accessible on Python module search path
_SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


