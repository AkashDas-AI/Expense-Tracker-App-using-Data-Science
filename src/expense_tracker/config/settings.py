"""
Application Configuration and Path Settings

Author: Akash Das
Description: Centralized configuration module using project-relative paths.
"""

from pathlib import Path
import os

# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Application Metadata
APP_NAME = "Expense Tracker App"
APP_VERSION = "0.1.0"
AUTHOR = "Akash Das"

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EXPORTS_DIR = OUTPUTS_DIR / "exports"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"

# Database Configuration
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(PROCESSED_DATA_DIR / "expenses.db")))

# Environment Settings
APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = os.getenv("APP_DEBUG", "True").lower() in ("true", "1", "yes")
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

