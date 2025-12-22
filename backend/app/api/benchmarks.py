from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db, async_session
from app.models import Benchmark, BenchmarkResult
from app.services.test_runner import TestRunner, MockTestRunner


router = APIRouter()


class BenchmarkCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_names: List[str]
    test_case_names: List[str]
    use_mock: bool = False


class BenchmarkResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BenchmarkListResponse(BaseModel):
    benchmarks: List[BenchmarkResponse]
    total: int


@router.post("/", response_model=BenchmarkResponse)
async def create_benchmark(
    data: BenchmarkCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create and start a new benchmark run."""
    benchmark = Benchmark(
        name=data.name,
        description=data.description,
        status="pending"
    )
    db.add(benchmark)
    await db.commit()
    await db.refresh(benchmark)
    
    # Run benchmark in background
    async def run_benchmark_task():
        async with async_session() as session:
            if data.use_mock:
                runner = MockTestRunner(session)
                await runner.run_mock_benchmark(benchmark.id, data.model_names, data.test_case_names)
            else:
                runner = TestRunner(session)
                await runner.run_benchmark(benchmark.id, data.model_names, data.test_case_names)
    
    background_tasks.add_task(run_benchmark_task)
    
    return benchmark


@router.get("/", response_model=BenchmarkListResponse)
async def list_benchmarks(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List all benchmarks."""
    result = await db.execute(
        select(Benchmark).order_by(Benchmark.created_at.desc()).offset(skip).limit(limit)
    )
    benchmarks = result.scalars().all()
    
    count_result = await db.execute(select(Benchmark))
    total = len(count_result.scalars().all())
    
    return BenchmarkListResponse(benchmarks=benchmarks, total=total)


@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(benchmark_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific benchmark."""
    result = await db.execute(select(Benchmark).where(Benchmark.id == benchmark_id))
    benchmark = result.scalar_one_or_none()
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    return benchmark


@router.delete("/{benchmark_id}")
async def delete_benchmark(benchmark_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a benchmark and its results."""
    result = await db.execute(select(Benchmark).where(Benchmark.id == benchmark_id))
    benchmark = result.scalar_one_or_none()
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    await db.delete(benchmark)
    await db.commit()
    
    return {"message": "Benchmark deleted"}
