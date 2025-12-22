from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import benchmarks, models, test_cases, results
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LLM Benchmark Platform",
    description="A platform for benchmarking LLM coding capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(benchmarks.router, prefix="/api/benchmarks", tags=["benchmarks"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(test_cases.router, prefix="/api/test-cases", tags=["test-cases"])
app.include_router(results.router, prefix="/api/results", tags=["results"])


@app.get("/")
async def root():
    return {"message": "LLM Benchmark Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
