from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    WORKSPACE_DIR: Optional[str] = None
    HOST_WORKSPACE_DIR: Optional[str] = None
    PORT: int = 5057
    MLE_KIT_IMAGE: str = (
        "phoenix120/holosophos_mle@sha256:be537e378315cb8796163ad5aabbc11077003e7afa141c9141f35a42091b4862"
    )

    GPU_TYPE: str = "RTX_3090"
    DISK_SPACE: int = 300
    EXISTING_INSTANCE_ID: Optional[int] = None
    EXISTING_SSH_KEY: Optional[str] = None
    VAST_AI_KEY: Optional[str] = None

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
