from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    cors_origins: str = ""
    omniroute_base_url: str = ""
    omniroute_api_key: str = ""
    omniroute_text_model: str = "auto/best-chat"
    omniroute_image_model: str = ""
    omniroute_timeout_seconds: float = 180
    scheduler_interval_seconds: int = 60
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""
    frontend_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self):
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
