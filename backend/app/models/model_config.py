from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.core.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=False)  # openai, anthropic, google
    model_id = Column(String, nullable=False)  # gpt-4, claude-3-opus, gemini-pro
    display_name = Column(String, nullable=False)
    
    # Model parameters
    temperature = Column(Float, default=0.0)
    max_tokens = Column(Integer, default=4096)
    
    # Cost per 1K tokens (input/output)
    cost_per_1k_input = Column(Float, default=0.0)
    cost_per_1k_output = Column(Float, default=0.0)
    
    # Feature flags
    is_active = Column(Boolean, default=True)
    supports_code_mode = Column(Boolean, default=True)
    supports_ask_mode = Column(Boolean, default=True)
    
    # Additional settings
    extra_params = Column(JSON, default=dict)
