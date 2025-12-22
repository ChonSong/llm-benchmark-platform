import asyncio
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Benchmark, BenchmarkResult, ModelConfig, TestCase
from app.services.llm_providers import get_provider, LLMResponse
from app.services.scoring_engine import ScoringEngine


class TestRunner:
    """Main test runner engine for executing benchmarks."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_engine = ScoringEngine()
    
    async def run_benchmark(self, benchmark_id: int, model_names: List[str], test_case_names: List[str]) -> Benchmark:
        """Run a complete benchmark with specified models and test cases."""
        # Get benchmark
        result = await self.db.execute(select(Benchmark).where(Benchmark.id == benchmark_id))
        benchmark = result.scalar_one_or_none()
        if not benchmark:
            raise ValueError(f"Benchmark {benchmark_id} not found")
        
        benchmark.status = "running"
        await self.db.commit()
        
        try:
            # Get models and test cases
            models_result = await self.db.execute(
                select(ModelConfig).where(ModelConfig.name.in_(model_names), ModelConfig.is_active == True)
            )
            models = models_result.scalars().all()
            
            test_cases_result = await self.db.execute(
                select(TestCase).where(TestCase.name.in_(test_case_names))
            )
            test_cases = test_cases_result.scalars().all()
            
            # Run each combination
            for model in models:
                for test_case in test_cases:
                    await self._run_single_test(benchmark, model, test_case)
            
            benchmark.status = "completed"
            benchmark.completed_at = datetime.utcnow()
            await self.db.commit()
            
        except Exception as e:
            benchmark.status = "failed"
            await self.db.commit()
            raise e
        
        return benchmark
    
    async def _run_single_test(self, benchmark: Benchmark, model: ModelConfig, test_case: TestCase) -> BenchmarkResult:
        """Run a single test case with a specific model."""
        # Create result record
        result = BenchmarkResult(
            benchmark_id=benchmark.id,
            model_name=model.name,
            test_case_name=test_case.name,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(result)
        await self.db.commit()
        
        try:
            # Get LLM provider
            provider = get_provider(
                model.provider,
                model.model_id,
                model.cost_per_1k_input,
                model.cost_per_1k_output
            )
            
            # Build prompt
            prompt = self._build_prompt(test_case)
            system_prompt = self._get_system_prompt(test_case)
            
            # Generate response
            llm_response = await provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=model.temperature,
                max_tokens=model.max_tokens
            )
            
            # Extract code from response
            generated_code = self._extract_code(llm_response.content)
            
            # Score the result
            score_result = self.scoring_engine.score(
                task_type=test_case.task_type,
                code=generated_code,
                original_code=test_case.input_code or "",
                mode=test_case.mode,
                rules=test_case.rules or []
            )
            
            # Update result
            result.status = "completed"
            result.completed_at = datetime.utcnow()
            result.latency_ms = llm_response.latency_ms
            result.input_tokens = llm_response.input_tokens
            result.output_tokens = llm_response.output_tokens
            result.total_cost = llm_response.cost
            result.generated_code = generated_code
            result.lines_of_code = len([l for l in generated_code.split('\n') if l.strip()])
            
            # Scores
            result.overall_score = score_result.overall_score
            result.adherence_score = score_result.adherence_score
            result.completeness_score = score_result.completeness_score
            result.security_score = score_result.security_score
            result.architecture_score = score_result.architecture_score
            result.defensiveness_score = score_result.defensiveness_score
            result.precision_score = score_result.precision_score
            result.verbosity_score = score_result.verbosity_score
            result.score_breakdown = score_result.breakdown
            result.issues_found = score_result.issues
            
            await self.db.commit()
            
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            await self.db.commit()
        
        return result
    
    def _build_prompt(self, test_case: TestCase) -> str:
        """Build the full prompt for a test case."""
        prompt = test_case.prompt
        
        if test_case.input_code:
            prompt += f"\n\n## Input Code:\n```\n{test_case.input_code}\n```"
        
        if test_case.rules:
            rules_text = "\n".join([f"{i+1}. {r.get('description', r)}" for i, r in enumerate(test_case.rules)])
            prompt += f"\n\n## Rules to Follow:\n{rules_text}"
        
        return prompt
    
    def _get_system_prompt(self, test_case: TestCase) -> str:
        """Get system prompt based on test case type."""
        if test_case.mode == "ask":
            return "You are a senior software architect. Analyze the provided code and answer questions about its architecture, patterns, and potential issues."
        else:
            return "You are an expert software developer. Generate clean, production-ready code that follows the exact specifications provided. Do not add unnecessary features or defensive code unless explicitly requested."
    
    def _extract_code(self, response: str) -> str:
        """Extract code blocks from LLM response."""
        # Try to find code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            return '\n\n'.join(code_blocks)
        
        # If no code blocks, return the whole response
        return response


class MockTestRunner:
    """Mock test runner for testing without API calls."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_engine = ScoringEngine()
    
    async def run_mock_benchmark(self, benchmark_id: int, model_names: List[str], test_case_names: List[str]) -> Benchmark:
        """Run a mock benchmark with simulated responses."""
        import random
        
        result = await self.db.execute(select(Benchmark).where(Benchmark.id == benchmark_id))
        benchmark = result.scalar_one_or_none()
        if not benchmark:
            raise ValueError(f"Benchmark {benchmark_id} not found")
        
        benchmark.status = "running"
        await self.db.commit()
        
        # Simulated model characteristics
        model_profiles = {
            "gpt-4o": {"defensiveness": 75, "precision": 60, "verbosity": 80, "cost_mult": 1.0},
            "claude-sonnet": {"defensiveness": 50, "precision": 85, "verbosity": 70, "cost_mult": 0.8},
            "gemini-2.0-flash": {"defensiveness": 30, "precision": 90, "verbosity": 40, "cost_mult": 0.5},
        }
        
        for model_name in model_names:
            profile = model_profiles.get(model_name, {"defensiveness": 50, "precision": 70, "verbosity": 60, "cost_mult": 1.0})
            
            for test_case_name in test_case_names:
                # Create mock result
                base_score = random.uniform(65, 95)
                
                mock_result = BenchmarkResult(
                    benchmark_id=benchmark_id,
                    model_name=model_name,
                    test_case_name=test_case_name,
                    status="completed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    latency_ms=random.uniform(2000, 15000) * profile["cost_mult"],
                    input_tokens=random.randint(500, 2000),
                    output_tokens=random.randint(200, 1500),
                    total_cost=random.uniform(0.01, 0.05) * profile["cost_mult"],
                    generated_code="# Mock generated code\nclass Example:\n    pass",
                    lines_of_code=random.randint(30, 150),
                    overall_score=base_score,
                    adherence_score=base_score * (profile["precision"] / 100),
                    completeness_score=base_score * 0.9,
                    security_score=random.uniform(70, 100),
                    architecture_score=random.uniform(60, 95),
                    defensiveness_score=profile["defensiveness"] + random.uniform(-10, 10),
                    precision_score=profile["precision"] + random.uniform(-10, 10),
                    verbosity_score=profile["verbosity"] + random.uniform(-10, 10),
                    score_breakdown={"mock": True},
                    issues_found=[]
                )
                self.db.add(mock_result)
        
        benchmark.status = "completed"
        benchmark.completed_at = datetime.utcnow()
        await self.db.commit()
        
        return benchmark
