from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str = ""
    JWT_SECRET: str = "local-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    ANTHROPIC_API_KEY: str = ""

    FACTURAMA_API_KEY: str = ""
    FACTURAMA_USER: str = ""
    FACTURAMA_PASSWORD: str = ""
    FACTURAMA_BASE_URL: str = "https://apisandbox.facturama.mx"

    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS — comma-separated en .env. Default: localhost dev (Next.js + FastAPI).
    # AUDIT C3: cerramos el wildcard que era CSRF/XSS prone.
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://localhost:8000,http://127.0.0.1:3000"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS comma-separated to list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
