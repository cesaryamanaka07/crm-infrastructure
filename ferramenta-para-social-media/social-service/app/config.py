from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    cors_origins: str
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    frontend_return_url: str
    social_public_base_url: str
    facebook_callback_url: str = ""
    instagram_callback_url: str = ""
    linkedin_callback_url: str = ""
    facebook_authorization_base_url: str = ""
    facebook_graph_base_url: str = ""
    instagram_authorization_url: str = ""
    instagram_token_url: str = ""
    instagram_graph_base_url: str = ""
    linkedin_authorization_url: str = ""
    linkedin_token_url: str = ""
    linkedin_userinfo_url: str = ""
    meta_client_id: str = ""
    meta_client_secret: str = ""
    meta_api_version: str = ""
    facebook_api_version: str = ""
    instagram_api_version: str = ""
    facebook_login_config_id: str = ""
    instagram_login_config_id: str = ""
    instagram_client_id: str = ""
    instagram_client_secret: str = ""
    instagram_auth_mode: str = "instagram"
    facebook_scopes: str = ""
    instagram_scopes: str = ""
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_scopes: str = "openid,profile,email,w_member_social"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self):
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def callback_url(self, provider: str) -> str:
        callback = {
            "facebook": self.facebook_callback_url,
            "instagram": self.instagram_callback_url,
            "linkedin": self.linkedin_callback_url,
        }.get(provider, "")
        if callback:
            return callback.rstrip("/")
        return f"{self.social_public_base_url.rstrip('/')}/oauth/{provider}/callback"

    def provider_endpoints_configured(self, provider: str) -> bool:
        if provider == "instagram" and self.instagram_auth_mode == "facebook":
            return bool(self.facebook_authorization_base_url.strip() and self.facebook_graph_base_url.strip())
        endpoints = {
            "facebook": (self.facebook_authorization_base_url, self.facebook_graph_base_url),
            "instagram": (self.instagram_authorization_url, self.instagram_token_url, self.instagram_graph_base_url),
            "linkedin": (self.linkedin_authorization_url, self.linkedin_token_url, self.linkedin_userinfo_url),
        }
        return all(value.strip() for value in endpoints.get(provider, ()))

    def client_id(self, provider: str) -> str:
        if provider == "instagram" and self.instagram_auth_mode == "facebook":
            return self.meta_client_id
        if provider == "instagram":
            return self.instagram_client_id
        if provider == "facebook":
            return self.meta_client_id
        return self.linkedin_client_id

    def client_secret(self, provider: str) -> str:
        if provider == "instagram" and self.instagram_auth_mode == "facebook":
            return self.meta_client_secret
        if provider == "instagram":
            return self.instagram_client_secret
        if provider == "facebook":
            return self.meta_client_secret
        return self.linkedin_client_secret

    def api_version(self, provider: str) -> str:
        if provider == "facebook":
            return self.facebook_api_version or self.meta_api_version
        if provider == "instagram":
            if self.instagram_auth_mode == "facebook":
                return self.facebook_api_version or self.meta_api_version
            return self.instagram_api_version or self.meta_api_version
        return ""

    def login_config_id(self, provider: str) -> str:
        if provider == "facebook":
            return self.facebook_login_config_id
        if provider == "instagram" and self.instagram_auth_mode == "facebook":
            return self.instagram_login_config_id or self.facebook_login_config_id
        return ""


settings = Settings()
