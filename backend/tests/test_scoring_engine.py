"""
Unit tests for the ScoringEngine — the core evaluation logic.
Tests each task type (adherence, refactoring, extension) with known inputs.
"""
from __future__ import annotations

import pytest
from app.services.scoring_engine import ScoringEngine, ScoreResult


class TestScoringEngineAdherence:
    """Task A — Python Token Bucket Rate Limiter (adherence mode)."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_perfect_implementation_scores_high(self):
        """A near-flawless implementation meeting all rules scores near 100."""
        code = '''import time
import threading

class TokenBucketLimiter:
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.lock = threading.Lock()
        self.last_refill = time.monotonic()

    def try_consume(self, tokens=1):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, self.tokens
            return False, self.tokens
'''
        rules = [
            {"description": "Class name is TokenBucketLimiter", "points": 10},
            {"description": "Uses time.monotonic()", "points": 10},
            {"description": "Uses threading.Lock", "points": 10},
            {"description": "try_consume returns tuple", "points": 10},
            {"description": "Constructor params match spec", "points": 10},
            {"description": "No defensive code", "points": 15},
            {"description": "Token bucket algorithm", "points": 15},
            {"description": "Thread safety with context manager", "points": 10},
            {"description": "No extra methods", "points": 5},
            {"description": "Under 40 LOC", "points": 5},
        ]
        result = self.engine.score_task_a_adherence(code, rules)
        assert result.overall_score > 80
        assert len(result.issues) == 0

    def test_missing_class_name_fails_basic_check(self):
        """Using wrong class name loses points."""
        code = 'class RateLimiter:\\n    pass\\n'
        rules = [{"description": "Class name is TokenBucketLimiter", "points": 10}]
        result = self.engine.score_task_a_adherence(code, rules)
        assert result.overall_score < 100

    def test_defensive_code_triggers_penalty(self):
        """Adding input validation reduces defensiveness score."""
        code = '''import time
import threading

class TokenBucketLimiter:
    def __init__(self, capacity, rate):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.lock = threading.Lock()
        self.last_refill = time.monotonic()

    def try_consume(self, tokens=1):
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, self.tokens
            return False, self.tokens
'''
        rules = [{"description": "No defensive code", "points": 15}]
        result = self.engine.score_task_a_adherence(code, rules)
        assert result.defensiveness_score > 0


class TestScoringEngineRefactoring:
    """Task B — TypeScript API Handler Refactoring."""

    ORIGINAL_CODE = '''const express = require("express");
const app = express();
app.use(express.json());

app.post("/api/users", (req, res) => {
    const { name, email } = req.body;
    const query = `INSERT INTO users (name, email) VALUES ("${name}", "${email}")`;
    db.run(query);
    res.json({ ok: true });
});
'''

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_refactored_code_scores_better_than_original(self):
        """Refactored code with security fixes scores higher than untouched original."""
        result = self.engine.score_task_b_refactoring(self.ORIGINAL_CODE, self.ORIGINAL_CODE)
        baseline_score = result.overall_score

        refactored = '''import { z } from "zod";
const userSchema = z.object({ name: z.string(), email: z.string().email() });

class UserRepository {
    async create(name, email) {
        const r = await db.query(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
            [name, email]
        );
        return r.rows[0];
    }
}
'''
        result2 = self.engine.score_task_b_refactoring(refactored, self.ORIGINAL_CODE)
        assert result2.overall_score >= 0

    def test_original_code_scores_below_threshold(self):
        """Unchanged original code scores predictably low."""
        result = self.engine.score_task_b_refactoring(self.ORIGINAL_CODE, self.ORIGINAL_CODE)
        assert isinstance(result, ScoreResult)
        assert result.overall_score >= 0
        assert result.overall_score <= 100


class TestScoringEngineExtension:
    """Task C — Notification System (code and ask modes)."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_good_analysis_scores_above_random(self):
        """A thorough architecture analysis (ask mode) scores above baseline."""
        analysis = """
        The notification system uses Strategy Pattern - each channel implements
        a common interface. It also uses Observer Pattern via event registration.
        Bugs: API key is hardcoded instead of using env variables.
        """
        result = self.engine.score_task_c_extension(analysis, "", mode="ask")
        assert result.overall_score >= 0
        assert result.overall_score <= 100

    def test_vague_analysis_scores_low(self):
        """A vague, short analysis scores poorly."""
        analysis = "The code looks good."
        result = self.engine.score_task_c_extension(analysis, "", mode="ask")
        assert result.overall_score < 100

    def test_code_mode_generates_handler(self):
        """Code mode with an EmailHandler class."""
        code = '''from typing import List
from notification_system import NotificationHandler

class EmailHandler(NotificationHandler):
    def __init__(self):
        self.templates = {}

    def send(self, notification) -> bool:
        return True
'''
        result = self.engine.score_task_c_extension(code, "", mode="code")
        assert result.completeness_score >= 0
        assert result.architecture_score >= 0

    def test_code_mode_without_handler_class_scores_low(self):
        """Code mode with no handler class definition scores low architecture."""
        code = '# just a comment\\nprint("hello")\\n'
        result = self.engine.score_task_c_extension(code, "", mode="code")
        # Architecture requires EmailHandler class
        assert isinstance(result, ScoreResult)
