from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (or backend/.env locally)."""

    app_name: str = "ClinicFlow API"
    # Set to the Git commit SHA by the Docker build / Helm chart so every running
    # pod can be traced back to the exact commit that produced it.
    app_version: str = "dev"
    database_url: str = "postgresql+psycopg://clinicflow:clinicflow@localhost:5432/clinicflow"
    seed_demo_data: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
