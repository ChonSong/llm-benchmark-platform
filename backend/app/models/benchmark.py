from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Benchmark(Base):
    __tablename__ = "benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    results = relationship("BenchmarkResult", back_populates="benchmark", cascade="all, delete-orphan")
