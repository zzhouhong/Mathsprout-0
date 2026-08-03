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


# ---------- Async DB fixtures (for memory_service, etc.) ----------

try:
    import pytest_asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.database import Base
    # Import all models so metadata.create_all sees every table
    import app.models  # noqa: F401

    @pytest_asyncio.fixture
    async def async_engine():
        """In-memory SQLite async engine for tests."""
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    @pytest_asyncio.fixture
    async def db_session(async_engine):
        """Async session bound to the in-memory test DB."""
        session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
        async with session_factory() as session:
            yield session
except ImportError:
    pass  # aiosqlite / pytest-asyncio not installed — DB fixtures unavailable
