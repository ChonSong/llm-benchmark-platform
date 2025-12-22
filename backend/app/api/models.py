from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.models import ModelConfig


router = APIRouter()


class ModelConfigCreate(BaseModel):
    name: str
    provider: str
    model_id: str
    display_name: str
    temperature: float = 0.0
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    is_active: bool = True
    supports_code_mode: bool = True
    supports_ask_mode: bool = True
    extra_params: Dict[str, Any] = {}


class ModelConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_active: Optional[bool] = None
    extra_params: Optional[Dict[str, Any]] = None


class ModelConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    model_id: str
    display_name: str
    temperature: float
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    is_active: bool
    supports_code_mode: bool
    supports_ask_mode: bool
    extra_params: Dict[str, Any]
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ModelConfigResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    """List all model configurations."""
    result = await db.execute(select(ModelConfig))
    return result.scalars().all()


@router.post("/", response_model=ModelConfigResponse)
async def create_model(data: ModelConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create a new model configuration."""
    # Check if model already exists
    existing = await db.execute(select(ModelConfig).where(ModelConfig.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Model with this name already exists")
    
    model = ModelConfig(**data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.get("/{model_name}", response_model=ModelConfigResponse)
async def get_model(model_name: str, db: AsyncSession = Depends(get_db)):
    """Get a specific model configuration."""
    result = await db.execute(select(ModelConfig).where(ModelConfig.name == model_name))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model


@router.patch("/{model_name}", response_model=ModelConfigResponse)
async def update_model(model_name: str, data: ModelConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update a model configuration."""
    result = await db.execute(select(ModelConfig).where(ModelConfig.name == model_name))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
    
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/{model_name}")
async def delete_model(model_name: str, db: AsyncSession = Depends(get_db)):
    """Delete a model configuration."""
    result = await db.execute(select(ModelConfig).where(ModelConfig.name == model_name))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    await db.delete(model)
    await db.commit()
    return {"message": "Model deleted"}


@router.post("/seed-defaults")
async def seed_default_models(db: AsyncSession = Depends(get_db)):
    """Seed the database with default model configurations."""
    default_models = [
        {
            "name": "gpt-4o",
            "provider": "openai",
            "model_id": "gpt-4o",
            "display_name": "GPT-4o",
            "temperature": 0.0,
            "max_tokens": 4096,
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
        },
        {
            "name": "claude-sonnet",
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "display_name": "Claude Sonnet 4",
            "temperature": 0.0,
            "max_tokens": 4096,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
        },
        {
            "name": "gemini-2.0-flash",
            "provider": "google",
            "model_id": "gemini-2.0-flash",
            "display_name": "Gemini 2.0 Flash",
            "temperature": 0.0,
            "max_tokens": 4096,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.001,
        },
    ]
    
    created = []
    for model_data in default_models:
        existing = await db.execute(select(ModelConfig).where(ModelConfig.name == model_data["name"]))
        if not existing.scalar_one_or_none():
            model = ModelConfig(**model_data)
            db.add(model)
            created.append(model_data["name"])
    
    await db.commit()
    return {"message": f"Created models: {created}"}
