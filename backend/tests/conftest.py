"""
Pytest configuration for the Mathsprout tests.

Run with:
    cd backend
    python -m pytest tests/ -v

    # With coverage:
    pip install pytest-cov
    python -m pytest tests/ -v --cov=app --cov-report=term-missing
"""

import pytest
import sys
from pathlib import Path

# Ensure the backend directory is on sys.path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear the settings LRU cache between tests."""
    from app.core.config import get_settings
    get_settings.cache_clear()
