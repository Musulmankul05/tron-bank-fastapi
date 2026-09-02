import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
DB_ADMIN = os.getenv("DB_ADMIN", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "tron_db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{DB_ADMIN}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)

new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with new_session() as session:
        yield session


class Base(DeclarativeBase): ...
