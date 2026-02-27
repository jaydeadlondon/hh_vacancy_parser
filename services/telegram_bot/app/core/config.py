from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    telegram_bot_token: str = ""

    api_gateway_url: str = "http://api-gateway:8000"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    environment: str = "development"
    debug: bool = True

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/1"


settings = Settings()
