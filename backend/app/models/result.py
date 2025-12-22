from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True, index=True)
    benchmark_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    model_name = Column(String, nullable=False)
    test_case_name = Column(String, nullable=False)
    
    # Execution metrics
    status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Float, nullable=True)
    
    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Output
    generated_code = Column(Text, nullable=True)
    lines_of_code = Column(Integer, default=0)
    
    # Scores (0-100)
    overall_score = Column(Float, default=0.0)
    adherence_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    architecture_score = Column(Float, default=0.0)
    
    # Qualitative scores for radar chart
    defensiveness_score = Column(Float, default=0.0)  # GPT tendency
    precision_score = Column(Float, default=0.0)  # Gemini tendency
    verbosity_score = Column(Float, default=0.0)
    
    # Detailed breakdown
    score_breakdown = Column(JSON, default=dict)
    issues_found = Column(JSON, default=list)
    
    # Error info if failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    benchmark = relationship("Benchmark", back_populates="results")
