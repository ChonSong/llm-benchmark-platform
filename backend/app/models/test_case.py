from sqlalchemy import Column, Integer, String, Text, JSON
from app.core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    task_type = Column(String, nullable=False)  # adherence, refactoring, extension
    description = Column(Text, nullable=True)
    
    # The prompt/instructions for the task
    prompt = Column(Text, nullable=False)
    
    # Input code (for refactoring/extension tasks)
    input_code = Column(Text, nullable=True)
    
    # Rules/requirements for scoring
    rules = Column(JSON, default=list)
    
    # Golden standard output (for comparison)
    golden_output = Column(Text, nullable=True)
    
    # Scoring weights
    scoring_config = Column(JSON, default=dict)
    
    # Mode: code or ask
    mode = Column(String, default="code")  # code, ask
