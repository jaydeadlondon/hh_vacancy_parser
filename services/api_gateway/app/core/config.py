from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_user: str = "hhparser"
    postgres_password: str = "hhparser_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "hhparser_db"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    rabbitmq_user: str = "hhparser"
    rabbitmq_password: str = "hhparser_password"
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672

    api_secret_key: str = "change-me-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    environment: str = "development"
    debug: bool = True
    project_name: str = "HH Vacancy Parser"
    project_version: str = "0.1.0"

    @property
    def database_url(self) -> str:
        """Async URL для SQLAlchemy"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL для Alembic"""
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )


settings = Settings()
