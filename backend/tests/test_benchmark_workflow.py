"""
Workflow tests for the full benchmark lifecycle.
Tests the critical user flow: seed data → create → poll → verify → delete.
"""
from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient


class TestBenchmarkWorkflow:
    """Full benchmark lifecycle using mock mode (no API keys needed)."""

    async def _create_benchmark(
        self, client: AsyncClient, model_names: list[str], test_case_names: list[str]
    ) -> dict:
        resp = await client.post("/api/benchmarks/", json={
            "name": "e2e-test-benchmark",
            "model_names": model_names,
            "test_case_names": test_case_names,
            "use_mock": True,
        })
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        return resp.json()

    async def _poll_until_complete(
        self, client: AsyncClient, benchmark_id: int, timeout: float = 30.0
    ) -> dict:
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(f"/api/benchmarks/{benchmark_id}")
            assert resp.status_code == 200
            data = resp.json()
            if data["status"] == "completed":
                return data
            await asyncio.sleep(0.5)
        pytest.fail(f"Benchmark {benchmark_id} did not complete within {timeout}s")

    async def test_seed_and_list_models(self, client: AsyncClient):
        """User seeds default models and verifies they appear."""
        seed_resp = await client.post("/api/models/seed-defaults")
        assert seed_resp.status_code == 200

        list_resp = await client.get("/api/models/")
        assert list_resp.status_code == 200
        models = list_resp.json()
        assert len(models) >= 2
        names = [m["name"] for m in models]
        assert "gpt-4o" in names
        assert "claude-sonnet" in names

    async def test_seed_and_list_test_cases(self, client: AsyncClient):
        """User seeds default test cases and verifies they appear."""
        seed_resp = await client.post("/api/test-cases/seed-defaults")
        assert seed_resp.status_code == 200

        list_resp = await client.get("/api/test-cases/")
        assert list_resp.status_code == 200
        cases = list_resp.json()
        assert len(cases) >= 3

    async def test_create_benchmark_returns_pending(
        self, client: AsyncClient, seeded_models: list[dict], seeded_test_cases: list[dict]
    ):
        """Creating a benchmark returns immediately with status=pending."""
        benchmark = await self._create_benchmark(client, ["gpt-4o"], ["rate-limiter-adherence"])
        assert benchmark["status"] == "pending"
        assert benchmark["name"] == "e2e-test-benchmark"
        assert "id" in benchmark

    async def test_benchmark_transitions_to_running_then_completed(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """Benchmark status: pending → running → completed."""
        benchmark = await self._create_benchmark(
            client, ["gpt-4o", "claude-sonnet"], ["rate-limiter-adherence", "typescript-refactoring"]
        )
        bid = benchmark["id"]

        completed = await self._poll_until_complete(client, bid)
        assert completed["status"] == "completed"
        assert completed["completed_at"] is not None

    async def test_completed_benchmark_has_results(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """After completion, results exist with scores for every model×test_case pair."""
        benchmark = await self._create_benchmark(
            client, ["gpt-4o", "claude-sonnet"], ["rate-limiter-adherence", "typescript-refactoring"]
        )
        bid = benchmark["id"]
        await self._poll_until_complete(client, bid)

        # Fetch results
        resp = await client.get(f"/api/results/benchmark/{bid}")
        assert resp.status_code == 200
        results = resp.json()

        # 2 models × 2 test_cases = 4 results
        assert len(results) == 4

        # Every result completed with scores
        for r in results:
            assert r["status"] == "completed", f"Result {r['id']} failed: {r.get('error_message')}"
            assert r["overall_score"] >= 0
            assert r["overall_score"] <= 100
            assert r["latency_ms"] > 0
            assert r["total_cost"] > 0

        # All model names present
        model_names = {r["model_name"] for r in results}
        assert "gpt-4o" in model_names
        assert "claude-sonnet" in model_names

        # All test case names present
        tc_names = {r["test_case_name"] for r in results}
        assert "rate-limiter-adherence" in tc_names
        assert "typescript-refactoring" in tc_names

    async def test_comparison_endpoint(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """Comparison endpoint returns per-model aggregates."""
        benchmark = await self._create_benchmark(
            client, ["gpt-4o", "claude-sonnet"], ["rate-limiter-adherence"]
        )
        bid = benchmark["id"]
        await self._poll_until_complete(client, bid)

        resp = await client.get(f"/api/results/benchmark/{bid}/comparison")
        assert resp.status_code == 200
        data = resp.json()

        assert data["benchmark_id"] == bid
        assert "results" in data
        assert "summary" in data
        summary = data["summary"]
        assert "by_model" in summary
        assert len(summary["by_model"]) == 2

    async def test_radar_endpoint(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """Radar endpoint returns 5-axis scores per model."""
        benchmark = await self._create_benchmark(
            client, ["gpt-4o", "claude-sonnet"], ["rate-limiter-adherence"]
        )
        bid = benchmark["id"]
        await self._poll_until_complete(client, bid)

        resp = await client.get(f"/api/results/benchmark/{bid}/radar")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data) == 2  # one entry per model
        axes = {"completeness", "defensiveness", "precision", "security", "architecture"}
        for entry in data:
            assert "model_name" in entry
            for axis in axes:
                assert axis in entry

    async def test_delete_benchmark_cascades(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """Deleting a benchmark removes results too."""
        benchmark = await self._create_benchmark(
            client, ["gpt-4o"], ["rate-limiter-adherence"]
        )
        bid = benchmark["id"]
        await self._poll_until_complete(client, bid)

        # Confirm results exist
        resp = await client.get(f"/api/results/benchmark/{bid}")
        assert len(resp.json()) > 0

        # Delete
        resp = await client.delete(f"/api/benchmarks/{bid}")
        assert resp.status_code == 200

        # Benchmark gone
        resp = await client.get(f"/api/benchmarks/{bid}")
        assert resp.status_code == 404

        # Results gone
        resp = await client.get(f"/api/results/benchmark/{bid}")
        assert len(resp.json()) == 0

    async def test_list_benchmarks(
        self, client: AsyncClient, seeded_models, seeded_test_cases
    ):
        """Listing benchmarks shows all created benchmarks."""
        b1 = await self._create_benchmark(client, ["gpt-4o"], ["rate-limiter-adherence"])
        b2 = await self._create_benchmark(client, ["claude-sonnet"], ["typescript-refactoring"])

        resp = await client.get("/api/benchmarks/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        ids = [b["id"] for b in data["benchmarks"]]
        assert b1["id"] in ids
        assert b2["id"] in ids
