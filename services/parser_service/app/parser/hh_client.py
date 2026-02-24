import asyncio
from typing import Any

import httpx

from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class HHClient:
    """
    HTTP клиент для работы с HH.ru API
    """

    BASE_URL = settings.hh_api_base_url

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "User-Agent": settings.hh_user_agent,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(30.0),
        )

    async def close(self) -> None:
        """Закрываем клиент"""
        await self._client.aclose()

    async def __aenter__(self) -> "HHClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Базовый GET запрос с обработкой rate limit
        """
        for attempt in range(3):
            try:
                response = await self._client.get(url, params=params)

                if response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limit HH.ru. Ждём {wait}с...")
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP ошибка {e.response.status_code}: {url}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)

            except httpx.RequestError as e:
                logger.error(f"Ошибка запроса: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)

        return {}

    async def search_vacancies(
        self,
        params: dict[str, Any],
        page: int = 0,
    ) -> dict[str, Any]:
        """Поиск вакансий"""
        search_params = {
            **params,
            "page": page,
            "per_page": settings.parser_per_page,
        }
        return await self._get("/vacancies", search_params)

    async def get_vacancy(self, vacancy_id: str) -> dict[str, Any]:
        """Детальная информация о вакансии"""
        return await self._get(f"/vacancies/{vacancy_id}", {})

    async def get_all_vacancies(
        self,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Все вакансии по фильтру постранично"""
        all_vacancies: list[dict[str, Any]] = []

        for page in range(settings.parser_max_pages):
            logger.info(f"Загружаем страницу {page + 1}/{settings.parser_max_pages}")

            data = await self.search_vacancies(params, page=page)

            if not data:
                break

            items = data.get("items", [])
            all_vacancies.extend(items)

            total_pages = data.get("pages", 0)
            if page >= total_pages - 1:
                logger.info(f"Все страницы загружены. Всего: {len(all_vacancies)}")
                break

            await asyncio.sleep(0.5)

        return all_vacancies
