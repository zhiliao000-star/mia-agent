from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    model_name: str = Field(default="", alias="MODEL_NAME")

    convex_site_url: str = Field(default="", alias="CONVEX_SITE_URL")
    mia_internal_secret: str = Field(default="", alias="MIA_INTERNAL_SECRET")

    sendblue_api_key_id: str = Field(default="", alias="SENDBLUE_API_KEY_ID")
    sendblue_api_secret_key: str = Field(default="", alias="SENDBLUE_API_SECRET_KEY")
    sendblue_from_number: str = Field(default="", alias="SENDBLUE_FROM_NUMBER")
    sendblue_webhook_secret: str = Field(default="", alias="SENDBLUE_WEBHOOK_SECRET")
    sendblue_status_callback: str | None = Field(default=None, alias="SENDBLUE_STATUS_CALLBACK")
    owner_phone_number: str = Field(default="", alias="OWNER_PHONE_NUMBER")
    searxng_base_url: str = Field(default="", alias="SEARXNG_BASE_URL")

    sendblue_api_base_url: HttpUrl = Field(
        default="https://api.sendblue.co", alias="SENDBLUE_API_BASE_URL"
    )

    def validate_llm(self) -> None:
        missing = [
            name
            for name, value in {
                "OPENAI_API_KEY": self.openai_api_key,
                "OPENAI_BASE_URL": self.openai_base_url,
                "MODEL_NAME": self.model_name,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required LLM environment variables: {joined}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
