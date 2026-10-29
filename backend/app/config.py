from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CampusMatch AI"
    app_env: Literal["development", "test", "production"] = "development"
    secret_key: str = Field(default="dev-only-change-me-use-32-chars-min!!")
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"
    backend_cors_origins: str = "http://localhost:3000"
    app_public_url: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://campus:campus@localhost:5432/campusmatch"

    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    access_token_expire_minutes: int = 60
    csrf_cookie_name: str = "csrf_token"
    auth_cookie_name: str = "access_token"

    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: str = "./data/resumes"
    resume_max_bytes: int = 5 * 1024 * 1024
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"

    embedding_enabled: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model_path: str = ""
    embedding_lazy_load: bool = True

    llm_provider: Literal["none", "openai", "compatible"] = "none"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 20
    llm_base_url: str = ""

    ocr_enabled: bool = False

    email_provider: Literal["none", "smtp"] = "none"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@localhost"

    allow_dev_seed: bool = False

    match_weight_required: float = 0.40
    match_weight_preferred: float = 0.15
    match_weight_semantic: float = 0.25
    match_weight_evidence: float = 0.20

    rate_limit_default: str = "120/minute"
    rate_limit_auth: str = "10/minute"

    @field_validator("secret_key")
    @classmethod
    def secret_not_empty(cls, v: str) -> str:
        if not v or len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
