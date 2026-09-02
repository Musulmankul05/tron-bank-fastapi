from utils.rabbitmq import rabbitmq_service
from unittest.mock import AsyncMock
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest_asyncio
import redis.asyncio as aioredis
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_session
from main import app

load_dotenv()
DB_ADMIN = os.getenv("DB_ADMIN", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("TEST_DB_NAME", "tron-test")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_ADMIN}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    client = aioredis.from_url(
        os.getenv("REDIS_URL"),
        decode_responses=True,
    )

    try:
        await client.flushdb()
        yield
        await client.flushdb()
    finally:
        await client.aclose()

@pytest_asyncio.fixture(autouse=True)
def mock_rabbitmq(monkeypatch):
    mock_publish = AsyncMock()
    monkeypatch.setattr(rabbitmq_service, "connect", AsyncMock())
    monkeypatch.setattr(rabbitmq_service, "close", AsyncMock())
    monkeypatch.setattr(rabbitmq_service, "publish_event", mock_publish)
    return mock_publish


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
