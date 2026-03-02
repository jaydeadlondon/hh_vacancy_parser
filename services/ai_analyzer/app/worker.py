import asyncio
import json
import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.analyzer.gigachat_client import GigaChatClient
from app.analyzer.prompt import build_analysis_prompt
from app.core.config import settings
from app.publisher.rabbitmq import RabbitMQPublisher
from app.services.analysis_saver import mark_analysis_failed, save_analysis
from shared.models.user_filter import UserFilter
from shared.models.vacancy import Vacancy
from shared.utils.logger import get_logger

logger = get_logger(__name__)

QUEUE_VACANCIES_NEW = "vacancies.new"


class AIAnalyzerWorker:
    """
    Воркер AI анализатора
    Слушает очередь vacancies.new
    Для каждой вакансии запрашивает GigaChat
    Результат сохраняет в БД и отправляет в vacancies.analyzed
    """

    def __init__(self) -> None:
        self._engine = create_async_engine(settings.database_url, echo=False)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.gigachat = GigaChatClient()
        self.publisher = RabbitMQPublisher()
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def start(self) -> None:
        await self.publisher.connect()

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        await self._channel.set_qos(prefetch_count=1)

        logger.info("🚀 AI Analyzer Worker запущен")

    async def stop(self) -> None:
        await self.publisher.disconnect()
        if self._connection:
            await self._connection.close()
        await self._engine.dispose()
        logger.info("👋 AI Analyzer Worker остановлен")

    async def run(self) -> None:
        """Запускаем прослушивание очереди"""
        if not self._channel:
            raise RuntimeError("Не подключен к RabbitMQ")

        queue = await self._channel.declare_queue(
            QUEUE_VACANCIES_NEW,
            durable=True,
        )

        logger.info(f"👂 Слушаем очередь: {QUEUE_VACANCIES_NEW}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self._handle_message(message)

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        """Обрабатываем одно сообщение из очереди"""
        try:
            payload = json.loads(message.body.decode())
            vacancy_id = payload["vacancy_id"]
            user_id = payload["user_id"]
            filter_id = payload["filter_id"]

            logger.info(f"📨 Получено: vacancy_id={vacancy_id} user_id={user_id}")

            await self._analyze(vacancy_id, user_id, filter_id)

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)

    async def _analyze(
        self,
        vacancy_id: int,
        user_id: int,
        filter_id: int,
    ) -> None:
        """Основная логика анализа"""
        async with self._session_factory() as db:
            try:
                await asyncio.sleep(2)

                vacancy_result = await db.execute(
                    select(Vacancy).where(Vacancy.id == vacancy_id)
                )
                vacancy = vacancy_result.scalar_one_or_none()

                if not vacancy:
                    logger.error(f"Вакансия {vacancy_id} не найдена в БД")
                    return

                filter_result = await db.execute(
                    select(UserFilter).where(UserFilter.id == filter_id)
                )
                user_filter = filter_result.scalar_one_or_none()
                if not user_filter:
                    logger.error(f"Фильтр {filter_id} не найден")
                    return

                prompt = build_analysis_prompt(
                    vacancy_title=vacancy.title,
                    vacancy_description=vacancy.description or "",
                    vacancy_requirements=vacancy.requirements or "",
                    company=vacancy.company or "",
                    salary_from=vacancy.salary_from,
                    salary_to=vacancy.salary_to,
                    user_filter=user_filter,
                )

                logger.info(f"🧠 Анализируем вакансию: {vacancy.title[:50]}")
                analysis_result = await self.gigachat.analyze_vacancy(prompt)

                analysis = await save_analysis(
                    db=db,
                    vacancy_id=vacancy_id,
                    user_id=user_id,
                    analysis_result=analysis_result,
                )

                await db.commit()

                await self.publisher.publish_analyzed(
                    vacancy_id=vacancy_id,
                    user_id=user_id,
                    attractiveness_score=analysis.attractiveness_score or 0.0,
                    analysis_id=analysis.id,
                )

                logger.info(
                    f"✅ Анализ завершён: {vacancy.title[:40]} "
                    f"| score={analysis.attractiveness_score}"
                )

            except Exception as e:
                logger.error(
                    f"Ошибка анализа vacancy_id={vacancy_id}: {e}", exc_info=True
                )
                await mark_analysis_failed(
                    db=db,
                    vacancy_id=vacancy_id,
                    user_id=user_id,
                    error=str(e),
                )
                await db.commit()


async def main() -> None:
    worker = AIAnalyzerWorker()
    await worker.start()
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
