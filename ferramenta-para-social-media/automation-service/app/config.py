from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    cors_origins: str
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""
    frontend_url: str = ""
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_integration: str = "WHATSAPP-BAILEYS"
    evolution_webhook_url: str = ""
    n8n_api_url: str = ""
    n8n_api_key: str = ""
    typebot_viewer_url: str = ""
    typebot_builder_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self):
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @staticmethod
    def normalizar_url(valor: str) -> str:
        return valor.strip().rstrip("/")


settings = Settings()
