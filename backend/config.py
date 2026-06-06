"""
Configuration Management for AI Lead Generation Backend

This module uses pydantic-settings to load and validate environment variables
with strong typing and automatic validation on application startup.
"""

import os
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory of the current file
# backend/config.py -> backend/
current_dir = Path(__file__).parent
# Go up one level to the root directory
# backend/ -> root/
root_dir = current_dir.parent
env_file_path = root_dir / ".env"

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    All required fields must be present in .env file or environment.
    Missing required fields will cause validation error on startup.
    """

    # AI Service APIs
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini AI API key for lead analysis and content generation"
    )

    serper_api_key: str = Field(
        ...,
        description="Serper API key for web search and lead discovery"
    )

    # Database
    supabase_url: str = Field(
        ...,
        description="Supabase project URL"
    )

    supabase_key: str = Field(
        ...,
        description="Supabase anonymous/service role key"
    )

    # Email Service
    resend_api_key: str = Field(
        ...,
        description="Resend API key for email outreach"
    )

    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins (or comma-separated string that will be parsed)"
    )

    # Optional Application Settings
    port: int = Field(
        default=8000,
        description="Port for FastAPI server"
    )

    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        """Convert comma-separated origins string to list, or pass through if already a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is valid."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is within valid range."""
        if not (1024 <= v <= 65535):
            raise ValueError("Port must be between 1024 and 65535")
        return v


# Global settings instance
# This will be initialized once and imported throughout the application
# type: ignore - pydantic-settings loads from environment automatically
settings = Settings()  # type: ignore[call-arg]
