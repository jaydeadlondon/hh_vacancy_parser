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

    hh_api_base_url: str = "https://api.hh.ru"
    hh_user_agent: str = "HH-Parser-1.0"

    parser_interval_seconds: int = 3600
    parser_max_pages: int = 5
    parser_per_page: int = 50

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
