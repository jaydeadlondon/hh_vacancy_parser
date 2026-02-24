import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.parser.filters import apply_local_filters, build_hh_params
from app.parser.hh_client import HHClient
from app.publisher.rabbitmq import RabbitMQPublisher
from app.services.dedup import DeduplicationService
from app.services.vacancy_saver import get_or_create_vacancy
from shared.models.user import User
from shared.models.user_filter import UserFilter
from shared.models.vacancy_analysis import VacancyAnalysis
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class ParserWorker:
    """
    Главный воркер парсера
    Каждый час обходит всех пользователей и их фильтры
    """

    def __init__(self) -> None:
        self._engine = create_async_engine(settings.database_url, echo=False)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.dedup = DeduplicationService()
        self.publisher = RabbitMQPublisher()

    async def start(self) -> None:
        """Запуск воркера"""
        await self.dedup.connect()
        await self.publisher.connect()
        logger.info("🚀 Parser Worker запущен")

    async def stop(self) -> None:
        """Остановка воркера"""
        await self.dedup.disconnect()
        await self.publisher.disconnect()
        await self._engine.dispose()
        logger.info("👋 Parser Worker остановлен")

    async def run_once(self) -> None:
        """
        Один цикл парсинга
        Запускается по расписанию каждый час
        """
        logger.info("🔄 Начинаем цикл парсинга...")

        async with self._session_factory() as db:
            result = await db.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()

            if not users:
                logger.info("Нет активных пользователей")
                return

            logger.info(f"Найдено пользователей: {len(users)}")

            for user in users:
                await self._process_user(db, user)

        logger.info("✅ Цикл парсинга завершён")

    async def _process_user(self, db: AsyncSession, user: User) -> None:
        """Обрабатываем одного пользователя — все его фильтры"""
        result = await db.execute(
            select(UserFilter).where(
                UserFilter.user_id == user.id,
                UserFilter.is_active == True,
            )
        )
        filters = result.scalars().all()

        if not filters:
            logger.debug(f"У пользователя {user.id} нет активных фильтров")
            return

        logger.info(f"👤 Пользователь {user.username}: {len(filters)} фильтров")

        async with HHClient() as hh:
            for user_filter in filters:
                await self._process_filter(db, hh, user, user_filter)

    async def _process_filter(
        self,
        db: AsyncSession,
        hh: HHClient,
        user: User,
        user_filter: UserFilter,
    ) -> None:
        """Обрабатываем один фильтр пользователя"""
        logger.info(
            f"🔍 Фильтр [{user_filter.id}] '{user_filter.name}' "
            f"для пользователя {user.username}"
        )

        hh_params = build_hh_params(user_filter)

        vacancies = await hh.get_all_vacancies(hh_params)
        logger.info(f"Получено вакансий от HH: {len(vacancies)}")

        new_count = 0
        for vacancy_data in vacancies:
            hh_id = str(vacancy_data.get("id", ""))
            if not hh_id:
                continue

            if not apply_local_filters(vacancy_data, user_filter):
                continue

            if await self.dedup.is_seen(hh_id, user.id):
                continue

            vacancy, is_new = await get_or_create_vacancy(db, vacancy_data)

            await self.dedup.mark_seen(hh_id, user.id)

            analysis = VacancyAnalysis(
                vacancy_id=vacancy.id,
                user_id=user.id,
                status="pending",
            )
            db.add(analysis)
            await db.flush()

            await self.publisher.publish_vacancy(
                vacancy_id=vacancy.id,
                user_id=user.id,
                filter_id=user_filter.id,
            )

            new_count += 1

        await db.commit()
        logger.info(
            f"✅ Фильтр [{user_filter.id}]: "
            f"новых вакансий {new_count} из {len(vacancies)}"
        )


async def main() -> None:
    """Точка входа — запускаем воркер по расписанию"""
    worker = ParserWorker()
    await worker.start()

    try:
        while True:
            await worker.run_once()
            logger.info(
                f"😴 Следующий запуск через "
                f"{settings.parser_interval_seconds} секунд"
            )
            await asyncio.sleep(settings.parser_interval_seconds)

    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
