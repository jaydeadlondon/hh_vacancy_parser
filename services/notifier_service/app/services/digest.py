from datetime import datetime, timezone, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models.notification import Notification
from shared.models.vacancy import Vacancy
from shared.models.vacancy_analysis import VacancyAnalysis
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def get_top_vacancies(
    db: AsyncSession,
    user_id: int,
    top_n: int = 10,
    days_back: int = 7,
) -> list[tuple[Vacancy, VacancyAnalysis]]:
    """
    Получаем топ-N вакансий за последние N дней
    Сортируем по attractiveness_score
    """
    since = datetime.now(timezone.utc) - timedelta(days=days_back)

    result = await db.execute(
        select(Vacancy, VacancyAnalysis)
        .join(VacancyAnalysis, VacancyAnalysis.vacancy_id == Vacancy.id)
        .where(
            VacancyAnalysis.user_id == user_id,
            VacancyAnalysis.status == "done",
            VacancyAnalysis.analyzed_at >= since,
            VacancyAnalysis.attractiveness_score.isnot(None),
        )
        .order_by(desc(VacancyAnalysis.attractiveness_score))
        .limit(top_n)
    )

    return [(row.Vacancy, row.VacancyAnalysis) for row in result.all()]


async def save_notifications(
    db: AsyncSession,
    user_id: int,
    notification_type: str,
    message: str,
    vacancy_id: int | None = None,
) -> Notification:
    """Сохраняем запись об уведомлении"""
    notification = Notification(
        user_id=user_id,
        vacancy_id=vacancy_id,
        type=notification_type,
        message=message,
        status="pending",
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


async def mark_notification_sent(
    db: AsyncSession,
    notification: Notification,
) -> None:
    """Помечаем уведомление как отправленное"""
    notification.status = "sent"
    notification.sent_at = datetime.now(timezone.utc)
    await db.flush()


async def mark_notification_failed(
    db: AsyncSession,
    notification: Notification,
    error: str,
) -> None:
    """Помечаем уведомление как неудавшееся"""
    notification.status = "failed"
    notification.error_message = error
    await db.flush()
