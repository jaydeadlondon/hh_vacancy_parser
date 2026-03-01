import asyncio
import json
import re
from typing import Any
import httpx
from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1"


class GigaChatClient:
    """
    Клиент для GigaChat API
    Документация: https://developers.sber.ru/docs/ru/gigachat/api/overview
    """

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_access_token(self) -> str:
        """
        Получаем OAuth токен для GigaChat
        Токен живёт 30 минут — кэшируем
        """
        import time

        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        import uuid
        import base64

        credentials = f"{settings.gigachat_client_id}:{settings.gigachat_client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                GIGACHAT_AUTH_URL,
                headers={
                    "Authorization": f"Basic {encoded}",
                    "RqUID": str(uuid.uuid4()),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": settings.gigachat_scope},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        self._token_expires_at = data.get("expires_at", 0) / 1000
        logger.info("✅ GigaChat токен получен")

        return self._access_token

    async def complete(self, prompt: str) -> str:
        """
        Отправляем запрос в GigaChat
        Возвращаем текст ответа
        """
        token = await self._get_access_token()

        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        for attempt in range(settings.max_retries):
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    response = await client.post(
                        f"{GIGACHAT_API_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                text = data["choices"][0]["message"]["content"]
                logger.debug(f"GigaChat ответ: {text[:100]}...")
                return text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("Токен устарел, обновляем...")
                    self._access_token = None
                    token = await self._get_access_token()
                    continue

                logger.error(f"HTTP ошибка GigaChat: {e.response.status_code}")
                if attempt == settings.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)

            except httpx.RequestError as e:
                logger.error(f"Ошибка запроса GigaChat: {e}")
                if attempt == settings.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)

        raise RuntimeError("GigaChat не ответил после всех попыток")

    async def analyze_vacancy(self, prompt: str) -> dict[str, Any]:
        """
        Анализируем вакансию — получаем структурированный JSON
        """
        raw_response = await self.complete(prompt)

        try:
            cleaned = re.sub(r"```json\s*|\s*```", "", raw_response).strip()
            result = json.loads(cleaned)
            return result

        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            logger.error(f"Не удалось распарсить JSON от GigaChat: {raw_response}")
            return {
                "detected_stack": [],
                "detected_level": "Unknown",
                "attractiveness_score": 0.0,
                "ai_summary": "Не удалось проанализировать вакансию",
                "pros": [],
                "cons": [],
            }
