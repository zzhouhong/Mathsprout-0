"""
Async PostgreSQL database setup with SQLAlchemy and Alembic support.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# SQLite doesn't support connection pool settings
_engine_kwargs: dict = {"echo": settings.DEBUG}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session with auto-commit/rollback."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Check if the database is reachable (with short timeout)."""
    import asyncio
    try:
        async with asyncio.timeout(3):  # 3-second timeout
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Database not available: {type(e).__name__}")
        return False


async def init_db():
    """
    Create all tables from ORM metadata.
    For production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created from ORM metadata.")


async def run_migrations():
    """
    Run Alembic migrations programmatically.
    Use this in production to ensure the schema is up to date.
    """
    try:
        from alembic.config import Config
        from alembic import command
        from pathlib import Path

        alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def get_db_stats() -> dict:
    """Get basic database statistics."""
    stats = {}
    try:
        async with engine.connect() as conn:
            for table in ["children", "worksheets", "analysis_results", "reports"]:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count
    except Exception as e:
        logger.warning(f"Could not get DB stats: {e}")
        stats["error"] = str(e)
    return stats
