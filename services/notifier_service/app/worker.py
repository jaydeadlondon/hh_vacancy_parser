import asyncio
import json
from datetime import datetime
import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.notifier.telegram_sender import TelegramSender
from app.services.digest import (
    get_top_vacancies,
    mark_notification_failed,
    mark_notification_sent,
    save_notification,
)
from shared.models.user import User
from shared.models.vacancy import Vacancy
from shared.models.vacancy_analysis import VacancyAnalysis
from shared.utils.logger import get_logger

logger = get_logger(__name__)

QUEUE_VACANCIES_ANALYZED = "vacancies.analyzed"


class NotifierWorker:
    """
    Воркер уведомлений
    1. Слушает vacancies.analyzed → мгновенные уведомления
    2. По крону раз в неделю → дайджест топ-10
    """

    def __init__(self) -> None:
        self._engine = create_async_engine(settings.database_url, echo=False)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.sender = TelegramSender()
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=5)
        logger.info("🚀 Notifier Worker запущен")

    async def stop(self) -> None:
        if self._connection:
            await self._connection.close()
        await self._engine.dispose()
        logger.info("👋 Notifier Worker остановлен")

    async def run(self) -> None:
        """Запускаем слушатель очереди + крон дайджеста"""
        if not self._channel:
            raise RuntimeError("Не подключён к RabbitMQ")

        await asyncio.gather(
            self._listen_queue(),
            self._digest_cron(),
        )

    async def _listen_queue(self) -> None:
        """Слушаем очередь vacancies.analyzed"""
        if not self._channel:
            return

        queue = await self._channel.declare_queue(
            QUEUE_VACANCIES_ANALYZED,
            durable=True,
        )

        logger.info(f"👂 Слушаем очередь: {QUEUE_VACANCIES_ANALYZED}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self._handle_message(message)

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        """Обрабатываем сообщение — решаем отправлять ли уведомление"""
        try:
            payload = json.loads(message.body.decode())
            vacancy_id = payload["vacancy_id"]
            user_id = payload["user_id"]
            score = float(payload["attractiveness_score"])
            analysis_id = payload["analysis_id"]

            logger.info(
                f"📨 Получено: vacancy_id={vacancy_id} "
                f"user_id={user_id} score={score}"
            )

            if score >= settings.min_score_for_instant:
                await self._send_instant_notification(
                    vacancy_id=vacancy_id,
                    user_id=user_id,
                    analysis_id=analysis_id,
                )
            else:
                logger.debug(
                    f"Score {score} ниже порога {settings.min_score_for_instant} "
                    f"— мгновенное уведомление не отправляем"
                )

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)

    async def _send_instant_notification(
        self,
        vacancy_id: int,
        user_id: int,
        analysis_id: int,
    ) -> None:
        """Мгновенное уведомление о хорошей вакансии"""
        async with self._session_factory() as db:
            try:
                vacancy_result = await db.execute(
                    select(Vacancy).where(Vacancy.id == vacancy_id)
                )
                vacancy = vacancy_result.scalar_one_or_none()

                analysis_result = await db.execute(
                    select(VacancyAnalysis).where(VacancyAnalysis.id == analysis_id)
                )
                analysis = analysis_result.scalar_one_or_none()

                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()

                if not all([vacancy, analysis, user]):
                    logger.error("Не найдены данные для уведомления")
                    return

                if not user.telegram_chat_id:
                    logger.debug(f"У пользователя {user_id} нет Telegram")
                    return

                message_text = self.sender.format_vacancy_message(vacancy, analysis)

                notification = await save_notification(
                    db=db,
                    user_id=user_id,
                    vacancy_id=vacancy_id,
                    notification_type="instant",
                    message=message_text,
                )

                success = await self.sender.send_message(
                    chat_id=user.telegram_chat_id,
                    text=message_text,
                )

                if success:
                    await mark_notification_sent(db, notification)
                    logger.info(
                        f"✅ Уведомление отправлено: "
                        f"user={user.username} vacancy={vacancy.title[:40]}"
                    )
                else:
                    await mark_notification_failed(
                        db, notification, "Telegram API вернул ошибку"
                    )

                await db.commit()

            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}", exc_info=True)
                await db.rollback()

    async def _digest_cron(self) -> None:
        """
        Крон для еженедельного дайджеста
        Каждый понедельник в 9:00
        """
        while True:
            now = datetime.now()

            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 9:
                days_until_monday = 7

            next_monday = now.replace(hour=9, minute=0, second=0, microsecond=0)
            next_monday = next_monday.replace(day=now.day + days_until_monday)

            wait_seconds = (next_monday - now).total_seconds()
            logger.info(
                f"📅 Следующий дайджест: {next_monday.strftime('%Y-%m-%d %H:%M')} "
                f"(через {wait_seconds/3600:.1f} часов)"
            )

            await asyncio.sleep(wait_seconds)
            await self._send_weekly_digest()

    async def _send_weekly_digest(self) -> None:
        """Отправляем дайджест всем пользователям"""
        logger.info("📊 Начинаем рассылку еженедельного дайджеста...")

        async with self._session_factory() as db:
            result = await db.execute(
                select(User).where(
                    User.is_active.is_(True),
                    User.telegram_chat_id.isnot(None),
                ),
            )
            users = result.scalars().all()

            week_number = datetime.now().isocalendar()[1]

            for user in users:
                await self._send_digest_to_user(db, user, week_number)

        logger.info("✅ Дайджест разослан")

    async def _send_digest_to_user(
        self,
        db: AsyncSession,
        user: User,
        week_number: int,
    ) -> None:
        """Отправляем дайджест одному пользователю"""
        try:
            top_vacancies = await get_top_vacancies(
                db=db,
                user_id=user.id,
                top_n=settings.digest_top_count,
            )

            if not top_vacancies:
                logger.debug(f"Нет вакансий для дайджеста: user={user.username}")
                return

            message_text = self.sender.format_digest_message(
                vacancies_with_analyses=top_vacancies,
                week_number=week_number,
            )

            notification = await save_notification(
                db=db,
                user_id=user.id,
                notification_type="weekly_digest",
                message=message_text,
            )

            success = await self.sender.send_message(
                chat_id=user.telegram_chat_id,
                text=message_text,
            )

            if success:
                await mark_notification_sent(db, notification)
                logger.info(f"✅ Дайджест отправлен: {user.username}")
            else:
                await mark_notification_failed(
                    db, notification, "Telegram API вернул ошибку"
                )

            await db.commit()

        except Exception as e:
            logger.error(
                f"Ошибка отправки дайджеста user={user.username}: {e}",
                exc_info=True,
            )
            await db.rollback()


async def main() -> None:
    worker = NotifierWorker()
    await worker.start()
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
