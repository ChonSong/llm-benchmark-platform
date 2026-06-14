#!/usr/bin/env python3
"""
Docker Compose E2E test for llm-benchmark-platform.
Brings up the full stack, waits for health, runs the benchmark workflow
against the real Docker services, captures logs on failure, tears down.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

COMPOSE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3008"
TIMEOUT = 60  # seconds to wait for stack health


def run(cmd, check=True, capture=True, timeout_val=30):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, timeout=timeout_val,
        cwd=COMPOSE_DIR
    )
    if check and result.returncode != 0:
        print(f"COMMAND FAILED: {cmd}")
        print(f"stdout: {result.stdout[-500:]}")
        print(f"stderr: {result.stderr[-500:]}")
        sys.exit(result.returncode)
    return result


def wait_for_health(url, timeout_sec=60):
    """Poll a URL until it returns 200 or timeout."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                return True
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
            pass
        time.sleep(2)
    return False


def api_get(path):
    """GET from the backend API."""
    url = f"{BACKEND_URL}{path}"
    resp = urllib.request.urlopen(url, timeout=10)
    return json.loads(resp.read())


def api_post(path, data):
    """POST JSON to the backend API."""
    url = f"{BACKEND_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def poll_benchmark(benchmark_id, timeout_sec=30):
    """Poll benchmark until completed."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        data = api_get(f"/api/benchmarks/{benchmark_id}")
        if data["status"] == "completed":
            return data
        time.sleep(1)
    raise TimeoutError(f"Benchmark {benchmark_id} not completed within {timeout_sec}s")


def main():
    step = 1
    failures = []

    def check(description, condition, detail=""):
        nonlocal step
        status = "PASS" if condition else "FAIL"
        print(f"  [{step}] {status}: {description} {detail}")
        if not condition:
            failures.append(description)
        step += 1

    # ---- Setup ----
    print("\n=== Docker Compose E2E: llm-benchmark-platform ===\n")
    print("Step 1: Bringing up Docker stack...")
    run("docker compose up -d --wait --wait-timeout 60", timeout_val=90)
    print("  Stack started.")

    # ---- Health Checks ----
    print("\nStep 2: Health checks...")
    backend_healthy = wait_for_health(f"{BACKEND_URL}/health", TIMEOUT)
    check("Backend /health endpoint", backend_healthy)

    frontend_up = wait_for_health(FRONTEND_URL, TIMEOUT)
    check("Frontend serves HTML", frontend_up)

    # ---- Seed Data ----
    print("\nStep 3: Seed data...")
    try:
        seed_models = api_post("/api/models/seed-defaults", {})
        check("Seed default models", True, f"({len(seed_models.get('message',''))} models)")
    except Exception as e:
        check("Seed default models", False, str(e))

    try:
        seed_cases = api_post("/api/test-cases/seed-defaults", {})
        check("Seed default test cases", True, f"({len(seed_cases.get('message',''))} cases)")
    except Exception as e:
        check("Seed default test cases", False, str(e))

    # ---- Model API ----
    print("\nStep 4: Model API...")
    try:
        models = api_get("/api/models/")
        check("List models returns data", len(models) >= 2, f"({len(models)} models)")
    except Exception as e:
        check("List models returns data", False, str(e))

    # ---- Test Cases API ----
    print("\nStep 5: Test Cases API...")
    try:
        cases = api_get("/api/test-cases/")
        check("List test cases returns data", len(cases) >= 3, f"({len(cases)} cases)")
    except Exception as e:
        check("List test cases returns data", False, str(e))

    # ---- Benchmark Workflow ----
    print("\nStep 6: Create benchmark (mock mode)...")
    try:
        model_names = [m["name"] for m in api_get("/api/models/")][:2]
        case_names = [c["name"] for c in api_get("/api/test-cases/")][:2]
        benchmark = api_post("/api/benchmarks/", {
            "name": "docker-e2e-test",
            "model_names": model_names,
            "test_case_names": case_names,
            "use_mock": True,
        })
        check("Benchmark created as pending", benchmark["status"] == "pending",
              f"(id={benchmark['id']})")
    except Exception as e:
        check("Benchmark created as pending", False, str(e))
        benchmark = None

    if benchmark:
        print("\nStep 7: Poll for completion...")
        try:
            completed = poll_benchmark(benchmark["id"])
            passed = completed["status"] == "completed"
            check("Benchmark completes", passed, f"(status={completed['status']})")
        except Exception as e:
            check("Benchmark completes", False, str(e))

        print("\nStep 8: Verify results...")
        try:
            results = api_get(f"/api/results/benchmark/{benchmark['id']}")
            check("Results exist", len(results) > 0, f"({len(results)} results)")
            all_completed = all(r["status"] == "completed" for r in results)
            check("All results completed", all_completed)
        except Exception as e:
            check("Results endpoint", False, str(e))

        print("\nStep 9: Comparison endpoint...")
        try:
            comparison = api_get(f"/api/results/benchmark/{benchmark['id']}/comparison")
            check("Comparison returns summary", "summary" in comparison)
        except Exception as e:
            check("Comparison endpoint", False, str(e))

        print("\nStep 10: Radar endpoint...")
        try:
            radar = api_get(f"/api/results/benchmark/{benchmark['id']}/radar")
            check("Radar returns data", len(radar) > 0, f"({len(radar)} models)")
        except Exception as e:
            check("Radar endpoint", False, str(e))

    # ---- Summary ----
    total = step - 1
    passed = total - len(failures)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    if failures:
        print(f"Failures: {', '.join(failures)}")
        # Capture logs for debugging
        run("docker compose logs backend --tail 50 > /tmp/docker-e2e-backend.log", check=False)
        run("docker compose logs frontend --tail 50 > /tmp/docker-e2e-frontend.log", check=False)
        print("Logs saved to /tmp/docker-e2e-*.log")
    else:
        print("All checks passed! 🎯")

    # ---- Teardown ----
    print("\nTearing down stack...")
    run("docker compose down -v", check=False)
    print("Done.")

    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
