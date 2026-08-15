from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    cors_origins: str
    omniroute_base_url: str = ""
    omniroute_api_key: str = ""
    omniroute_text_model: str = "auto/best-chat"
    omniroute_image_model: str = ""
    omniroute_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def omniroute_enabled(self) -> bool:
        return bool(self.omniroute_base_url.strip())


settings = Settings()
