from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)