import redis.asyncio as aioredis
from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

VACANCY_KEY_PREFIX = "vacancy:seen:"
VACANCY_TTL_SECONDS = 60 * 60 * 24 * 7


class DeduplicationService:
    """
    Дедупликация вакансий через Redis
    Не даём обрабатывать одну вакансию дважды
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("✅ Redis подключён")

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.aclose()

    def _make_key(self, hh_vacancy_id: str, user_id: int) -> str:
        """
        Ключ уникален для пары вакансия + пользователь
        Разные пользователи должны получать одни и те же вакансии
        """
        return f"{VACANCY_KEY_PREFIX}{user_id}:{hh_vacancy_id}"

    async def is_seen(self, hh_vacancy_id: str, user_id: int) -> bool:
        """
        Проверяем — видел ли этот пользователь эту вакансию?
        True = уже видел, пропускаем
        """
        if not self._redis:
            raise RuntimeError("Redis не подключён")

        key = self._make_key(hh_vacancy_id, user_id)
        return bool(await self._redis.exists(key))

    async def mark_seen(self, hh_vacancy_id: str, user_id: int) -> None:
        """Помечаем вакансию как просмотренную для пользователя"""
        if not self._redis:
            raise RuntimeError("Redis не подключён")

        key = self._make_key(hh_vacancy_id, user_id)
        await self._redis.setex(key, VACANCY_TTL_SECONDS, "1")

    async def is_saved_in_db(self, hh_vacancy_id: str) -> bool:
        """
        Проверяем глобально — есть ли вакансия в БД уже?
        Используем отдельный ключ без user_id
        """
        if not self._redis:
            raise RuntimeError("Redis не подключён")

        key = f"vacancy:db:{hh_vacancy_id}"
        return bool(await self._redis.exists(key))

    async def mark_saved_in_db(self, hh_vacancy_id: str) -> None:
        """Помечаем что вакансия уже сохранена в БД"""
        if not self._redis:
            raise RuntimeError("Redis не подключён")

        key = f"vacancy:db:{hh_vacancy_id}"
        await self._redis.setex(key, VACANCY_TTL_SECONDS, "1")
