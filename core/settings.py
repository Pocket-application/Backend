from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --------------------------------------------------
    # Database
    # --------------------------------------------------
    database_url: str
    db_schema: str = "public"

    # --------------------------------------------------
    # Security
    # --------------------------------------------------
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    log_signing_key: str

    # --------------------------------------------------
    # Redis
    # --------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_ttl: int = 60 * 5  # 5 minutos

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings() # type: ignore[call-arg]