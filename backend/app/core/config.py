"""Central Configuration Module (Owner: Baibhav).

Composes CoreSettings and DetectionSettings according to the blueprint.
"""

import os
from functools import lru_cache

from pydantic import BaseModel, Field

from app.detection.detection_settings import DetectionSettings


class CoreSettings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    trusted_proxy_count: int = Field(
        default_factory=lambda: int(os.getenv("TRUSTED_PROXY_COUNT", "0"))
    )
    enable_sandbox: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_SANDBOX", "true").lower() in ("true", "1", "yes")
    )
    static_dir: str = Field(default_factory=lambda: os.getenv("STATIC_DIR", "app/static"))


class Settings(BaseModel):
    core: CoreSettings = Field(default_factory=CoreSettings)
    detection: DetectionSettings = Field(default_factory=DetectionSettings)

    @property
    def app_env(self) -> str:
        return self.core.app_env

    @property
    def log_level(self) -> str:
        return self.core.log_level

    @property
    def trusted_proxy_count(self) -> int:
        return self.core.trusted_proxy_count

    @property
    def enable_sandbox(self) -> bool:
        return self.core.enable_sandbox

    @property
    def static_dir(self) -> str:
        return self.core.static_dir


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
