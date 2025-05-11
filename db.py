import os
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,     # Test connections before using them (efficient reconnection)
    pool_size=5,            # Maintain reasonable pool size
    max_overflow=10,        # Allow overflow connections during high load
    pool_timeout=10,        # Shorter timeout for faster error response
    # Note: Not using pool_recycle to allow connections to naturally timeout after 5 mins
    # This is more cost-efficient since we're not keeping connections alive unnecessarily
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db_context():
    """Provides a database session with automatic reconnection."""
    session = AsyncSessionLocal()
    try:
        # No explicit connection verification - let pool_pre_ping handle it
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()

# Shared async get_db dependency
async def get_db():
    async with get_db_context() as session:
        yield session 