"""Application configuration — paths, auth, and database."""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SSG_", extra="ignore")

    app_name: str = "Arawind Skill Gap"
    api_prefix: str = "/api/v1"
    max_upload_mb: int = 8
    # Paths
    base_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = base_dir / "data"
    taxonomy_dir: Path = data_dir / "taxonomy"
    sample_jds_dir: Path = data_dir / "sample_jds"
    processed_dir: Path = data_dir / "processed"
    models_dir: Path = Path(__file__).resolve().parents[1] / "models"
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_sentence_transformers: bool = False
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    # Database — SQLite by default for local/dev; Compose overrides with Postgres
    database_url: str = "sqlite:///./arawind.db"
    # Auth / JWT
    jwt_secret: str = "change-me-in-production-arawind-ssg-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    # Seed admin (created on startup if missing)
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin@Arawind2026"
    admin_name: str = "Arawind Admin"


settings = Settings()
