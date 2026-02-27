from typing import Any
import httpx
from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class APIClient:
    """
    HTTP клиент к API Gateway
    Все запросы бота идут через него
    """

    def __init__(self, token: str | None = None) -> None:
        self._base_url = settings.api_gateway_url
        self._token = token  # JWT токен пользователя

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def register(
        self, username: str, email: str, password: str
    ) -> dict[str, Any]:
        """Регистрация нового пользователя"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/v1/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                },
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """Авторизация — получаем JWT токены"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def get_me(self) -> dict[str, Any]:
        """Получаем данные текущего пользователя"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/v1/auth/me",
                headers=self._get_headers(),
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def link_telegram(
        self, telegram_chat_id: int, telegram_username: str | None
    ) -> dict[str, Any]:
        """Привязываем Telegram аккаунт к профилю"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self._base_url}/api/v1/users/me/telegram",
                headers=self._get_headers(),
                json={
                    "telegram_chat_id": telegram_chat_id,
                    "telegram_username": telegram_username,
                },
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def get_filters(self) -> dict[str, Any]:
        """Получаем фильтры пользователя"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/v1/filters",
                headers=self._get_headers(),
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def create_filter(self, filter_data: dict[str, Any]) -> dict[str, Any]:
        """Создаём новый фильтр"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/v1/filters",
                headers=self._get_headers(),
                json=filter_data,
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def delete_filter(self, filter_id: int) -> dict[str, Any]:
        """Удаляем фильтр"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self._base_url}/api/v1/filters/{filter_id}",
                headers=self._get_headers(),
                timeout=15.0,
            )
            return {"status": response.status_code, "data": {}}

    async def get_top_vacancies(self, limit: int = 10) -> dict[str, Any]:
        """Топ вакансий по score"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/v1/vacancies/top",
                headers=self._get_headers(),
                params={"limit": limit},
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}

    async def search_vacancies(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Поиск вакансий"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/v1/vacancies/search",
                headers=self._get_headers(),
                params={"q": query, "limit": limit},
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
