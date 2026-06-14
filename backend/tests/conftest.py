"""
Pytest configuration for llm-benchmark-platform backend tests.
Provides async test client, test database, and seed data fixtures.
"""
from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force test database before importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.core.database import async_session, engine, init_db
from app.main import app
from app.models.benchmark import Benchmark
from app.models.model_config import ModelConfig
from app.models.result import BenchmarkResult
from app.models.test_case import TestCase


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables before tests, drop after."""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Benchmark.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_database):
    """Clean all tables between tests."""
    yield
    async with engine.begin() as conn:
        for table in reversed(Benchmark.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client wrapping the app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


seed_models = [
    {
        "name": "gpt-4o",
        "provider": "openai",
        "model_id": "gpt-4o",
        "display_name": "GPT-4o",
        "temperature": 0.0,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015,
        "is_active": True,
        "supports_code_mode": True,
        "supports_ask_mode": True,
        "extra_params": {},
    },
    {
        "name": "claude-sonnet",
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-20250514",
        "display_name": "Claude Sonnet 4",
        "temperature": 0.0,
        "max_tokens": 4096,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "is_active": True,
        "supports_code_mode": True,
        "supports_ask_mode": True,
        "extra_params": {},
    },
]


@pytest_asyncio.fixture
async def seeded_models(client: AsyncClient) -> list[dict]:
    """Seed default models and return them."""
    resp = await client.post("/api/models/seed-defaults")
    assert resp.status_code == 200
    return resp.json()


seed_test_cases = [
    {
        "name": "rate-limiter-adherence",
        "task_type": "adherence",
        "description": "Build a TokenBucketRateLimiter in Python",
        "mode": "code",
        "prompt": "Build a TokenBucketLimiter class in Python.",
        "input_code": "",
        "rules": [
            {"description": "Class name is TokenBucketLimiter", "points": 10},
            {"description": "Uses time.monotonic()", "points": 10},
        ],
        "scoring_config": {},
    },
    {
        "name": "typescript-refactoring",
        "task_type": "refactoring",
        "description": "Refactor a TypeScript API handler",
        "mode": "code",
        "prompt": "Refactor the following TypeScript API handler code.",
        "input_code": "function handle(req, res) { res.json({ok:true}); }",
        "rules": [
            {"description": "SQL injection fixed", "points": 10},
        ],
        "scoring_config": {},
    },
]


@pytest_asyncio.fixture
async def seeded_test_cases(client: AsyncClient) -> list[dict]:
    """Seed default test cases and return them."""
    resp = await client.post("/api/test-cases/seed-defaults")
    assert resp.status_code == 200
    return resp.json()
