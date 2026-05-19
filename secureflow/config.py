"""
SecureFlow — Configuration
=========================
Centralized configuration using pydantic-settings BaseSettings.
Loads from environment variables and .env file automatically.
Falls back to safe defaults for local development.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    In production, these are injected via Cloud Run env vars
    backed by Secret Manager. In development, they are loaded
    from a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Google Cloud ---
    gcp_project: str = "your-project-id"
    gcp_region: str = "us-central1"
    gcp_service_account: str = "secureflow@your-project.iam.gserviceaccount.com"

    # --- GitLab ---
    gitlab_token: str = "mock-token"
    gitlab_webhook_secret: str = "mock-secret"

    # --- Gemini / AI Studio ---
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"  # Cheapest current model, great for agents

    # --- Vertex AI ---
    vertex_ai_location: str = "us-central1"

    # --- Pub/Sub ---
    pubsub_topic: str = "secureflow-events"
    pubsub_subscription: str = "secureflow-worker"

    # --- BigQuery ---
    bq_dataset: str = "secureflow"

    # --- App ---
    environment: str = "development"
    log_level: str = "INFO"
    hitl_timeout_minutes: int = 15

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def bq_full_dataset(self) -> str:
        """Returns the fully-qualified BigQuery dataset ID."""
        return f"{self.gcp_project}.{self.bq_dataset}"


# Singleton instance — import this everywhere
settings = Settings()
