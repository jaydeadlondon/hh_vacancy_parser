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

    gigachat_client_id: str = ""
    gigachat_client_secret: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"

    min_attractiveness_score: float = 60.0
    max_retries: int = 3

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
