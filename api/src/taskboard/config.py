"""Application settings, loaded from environment variables and validated at startup."""

from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class StorageBackend(StrEnum):
    LOCAL = "local"
    S3 = "s3"


class Settings(BaseSettings):
    """Settings come from the environment. Secrets have no defaults."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore", frozen=True)

    environment: Environment = Environment.PRODUCTION
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")

    database_url: SecretStr
    migration_database_url: SecretStr | None = None
    db_pool_size: int = Field(default=5, ge=1, le=50)

    redis_url: SecretStr | None = None
    cache_ttl_seconds: int = Field(default=300, ge=1, le=86_400)

    service_auth_secret: SecretStr = Field(min_length=32)
    public_base_url: HttpUrl

    session_ttl_seconds: int = Field(default=8 * 3600, ge=300, le=7 * 86_400)
    reset_token_ttl_seconds: int = Field(default=1800, ge=300, le=86_400)

    storage_backend: StorageBackend = StorageBackend.LOCAL
    storage_local_path: str = "/data/attachments"
    s3_bucket: str | None = None
    aws_region: str | None = None
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)

    webhook_signing_secret: SecretStr = Field(min_length=32)
    webhook_allow_http: bool = False
    webhook_allow_private_targets: bool = False
    webhook_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    webhook_max_attempts: int = Field(default=3, ge=1, le=5)

    login_max_failures: int = Field(default=5, ge=1)
    login_max_account_failures: int = Field(default=50, ge=1)
    login_max_attempts_per_ip: int = Field(default=20, ge=1)
    forgot_max_per_ip: int = Field(default=5, ge=1)
    register_max_per_ip: int = Field(default=10, ge=1)
    rate_limit_window_seconds: int = Field(default=900, ge=1)

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.storage_backend is StorageBackend.S3 and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        if self.environment is Environment.PRODUCTION:
            if self.webhook_allow_http or self.webhook_allow_private_targets:
                raise ValueError(
                    "webhook HTTP or private targets must not be enabled in production"
                )
            if self.public_base_url.scheme != "https":
                raise ValueError("PUBLIC_BASE_URL must use https in production")
        return self

    @property
    def migrations_url(self) -> str:
        """Owner credentials for Alembic; falls back to the application URL."""
        url = self.migration_database_url or self.database_url
        return url.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process. Fails fast on invalid configuration."""
    return Settings()
