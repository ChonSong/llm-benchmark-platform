from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os

from app.core.config import settings


router = APIRouter()


class APIKeysStatus(BaseModel):
    openai_configured: bool
    anthropic_configured: bool
    google_configured: bool


class APIKeysUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None


def mask_key(key: Optional[str]) -> str:
    """Mask an API key for display, showing only last 4 characters."""
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return "*" * (len(key) - 4) + key[-4:]


@router.get("/api-keys", response_model=APIKeysStatus)
async def get_api_keys_status():
    """Get the status of configured API keys (not the actual keys)."""
    return APIKeysStatus(
        openai_configured=bool(settings.OPENAI_API_KEY),
        anthropic_configured=bool(settings.ANTHROPIC_API_KEY),
        google_configured=bool(settings.GOOGLE_API_KEY),
    )


@router.get("/api-keys/masked")
async def get_masked_api_keys():
    """Get masked versions of API keys for display."""
    return {
        "openai": mask_key(settings.OPENAI_API_KEY),
        "anthropic": mask_key(settings.ANTHROPIC_API_KEY),
        "google": mask_key(settings.GOOGLE_API_KEY),
    }


@router.put("/api-keys")
async def update_api_keys(data: APIKeysUpdate):
    """Update API keys. Keys are stored in memory and environment variables."""
    updated = []
    
    if data.openai_api_key is not None:
        if data.openai_api_key == "":
            settings.OPENAI_API_KEY = None
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            settings.OPENAI_API_KEY = data.openai_api_key
            os.environ["OPENAI_API_KEY"] = data.openai_api_key
        updated.append("openai")
    
    if data.anthropic_api_key is not None:
        if data.anthropic_api_key == "":
            settings.ANTHROPIC_API_KEY = None
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            settings.ANTHROPIC_API_KEY = data.anthropic_api_key
            os.environ["ANTHROPIC_API_KEY"] = data.anthropic_api_key
        updated.append("anthropic")
    
    if data.google_api_key is not None:
        if data.google_api_key == "":
            settings.GOOGLE_API_KEY = None
            os.environ.pop("GOOGLE_API_KEY", None)
        else:
            settings.GOOGLE_API_KEY = data.google_api_key
            os.environ["GOOGLE_API_KEY"] = data.google_api_key
        updated.append("google")
    
    return {
        "message": f"Updated API keys: {updated}",
        "status": {
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
            "google_configured": bool(settings.GOOGLE_API_KEY),
        }
    }
