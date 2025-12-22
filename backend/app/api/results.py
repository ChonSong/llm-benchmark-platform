from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models import BenchmarkResult


router = APIRouter()


class ResultResponse(BaseModel):
    id: int
    benchmark_id: int
    model_name: str
    test_case_name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    latency_ms: Optional[float]
    input_tokens: int
    output_tokens: int
    total_cost: float
    generated_code: Optional[str]
    lines_of_code: int
    overall_score: float
    adherence_score: float
    completeness_score: float
    security_score: float
    architecture_score: float
    defensiveness_score: float
    precision_score: float
    verbosity_score: float
    score_breakdown: Dict[str, Any]
    issues_found: List[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class ResultSummary(BaseModel):
    model_name: str
    test_case_name: str
    overall_score: float
    latency_ms: Optional[float]
    total_cost: float
    lines_of_code: int


class ComparisonResponse(BaseModel):
    benchmark_id: int
    results: List[ResultResponse]
    summary: Dict[str, Any]


class RadarChartData(BaseModel):
    model_name: str
    completeness: float
    defensiveness: float
    precision: float
    security: float
    architecture: float


@router.get("/benchmark/{benchmark_id}", response_model=List[ResultResponse])
async def get_benchmark_results(benchmark_id: int, db: AsyncSession = Depends(get_db)):
    """Get all results for a benchmark."""
    result = await db.execute(
        select(BenchmarkResult).where(BenchmarkResult.benchmark_id == benchmark_id)
    )
    return result.scalars().all()


@router.get("/benchmark/{benchmark_id}/comparison", response_model=ComparisonResponse)
async def get_comparison(benchmark_id: int, db: AsyncSession = Depends(get_db)):
    """Get comparison data for a benchmark."""
    result = await db.execute(
        select(BenchmarkResult).where(BenchmarkResult.benchmark_id == benchmark_id)
    )
    results = result.scalars().all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this benchmark")
    
    # Calculate summary statistics
    models = {}
    for r in results:
        if r.model_name not in models:
            models[r.model_name] = {
                "total_score": 0,
                "total_cost": 0,
                "total_latency": 0,
                "total_loc": 0,
                "count": 0
            }
        models[r.model_name]["total_score"] += r.overall_score
        models[r.model_name]["total_cost"] += r.total_cost
        models[r.model_name]["total_latency"] += r.latency_ms or 0
        models[r.model_name]["total_loc"] += r.lines_of_code
        models[r.model_name]["count"] += 1
    
    summary = {
        "by_model": {
            name: {
                "avg_score": data["total_score"] / data["count"],
                "total_cost": data["total_cost"],
                "avg_latency_ms": data["total_latency"] / data["count"],
                "avg_loc": data["total_loc"] / data["count"]
            }
            for name, data in models.items()
        },
        "best_overall": max(models.keys(), key=lambda m: models[m]["total_score"] / models[m]["count"]),
        "most_cost_effective": min(models.keys(), key=lambda m: models[m]["total_cost"]),
        "fastest": min(models.keys(), key=lambda m: models[m]["total_latency"])
    }
    
    return ComparisonResponse(
        benchmark_id=benchmark_id,
        results=results,
        summary=summary
    )


@router.get("/benchmark/{benchmark_id}/radar", response_model=List[RadarChartData])
async def get_radar_data(benchmark_id: int, db: AsyncSession = Depends(get_db)):
    """Get radar chart data for model comparison."""
    result = await db.execute(
        select(BenchmarkResult).where(BenchmarkResult.benchmark_id == benchmark_id)
    )
    results = result.scalars().all()
    
    # Aggregate by model
    models = {}
    for r in results:
        if r.model_name not in models:
            models[r.model_name] = {
                "completeness": [],
                "defensiveness": [],
                "precision": [],
                "security": [],
                "architecture": []
            }
        models[r.model_name]["completeness"].append(r.completeness_score)
        models[r.model_name]["defensiveness"].append(r.defensiveness_score)
        models[r.model_name]["precision"].append(r.precision_score)
        models[r.model_name]["security"].append(r.security_score)
        models[r.model_name]["architecture"].append(r.architecture_score)
    
    radar_data = []
    for model_name, scores in models.items():
        radar_data.append(RadarChartData(
            model_name=model_name,
            completeness=sum(scores["completeness"]) / len(scores["completeness"]) if scores["completeness"] else 0,
            defensiveness=sum(scores["defensiveness"]) / len(scores["defensiveness"]) if scores["defensiveness"] else 0,
            precision=sum(scores["precision"]) / len(scores["precision"]) if scores["precision"] else 0,
            security=sum(scores["security"]) / len(scores["security"]) if scores["security"] else 0,
            architecture=sum(scores["architecture"]) / len(scores["architecture"]) if scores["architecture"] else 0
        ))
    
    return radar_data


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(result_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific result."""
    result = await db.execute(
        select(BenchmarkResult).where(BenchmarkResult.id == result_id)
    )
    benchmark_result = result.scalar_one_or_none()
    
    if not benchmark_result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return benchmark_result


@router.get("/{result_id}/code")
async def get_result_code(result_id: int, db: AsyncSession = Depends(get_db)):
    """Get the generated code for a result."""
    result = await db.execute(
        select(BenchmarkResult).where(BenchmarkResult.id == result_id)
    )
    benchmark_result = result.scalar_one_or_none()
    
    if not benchmark_result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "model_name": benchmark_result.model_name,
        "test_case_name": benchmark_result.test_case_name,
        "generated_code": benchmark_result.generated_code,
        "lines_of_code": benchmark_result.lines_of_code
    }
