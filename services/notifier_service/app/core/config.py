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

    rabbitmq_user: str = "hhparser"
    rabbitmq_password: str = "hhparser_password"
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672

    telegram_bot_token: str = ""

    min_score_for_instant: float = 70.0
    digest_top_count: int = 10

    environment: str = "development"
    debug: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )


settings = Settings()
