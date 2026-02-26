from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models.vacancy_analysis import VacancyAnalysis
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def save_analysis(
    db: AsyncSession,
    vacancy_id: int,
    user_id: int,
    analysis_result: dict[str, Any],
) -> VacancyAnalysis:
    """
    Сохраняем результат AI анализа в БД
    Обновляем существующую запись (она создана парсером со статусом pending)
    """
    from sqlalchemy import select

    result = await db.execute(
        select(VacancyAnalysis).where(
            VacancyAnalysis.vacancy_id == vacancy_id,
            VacancyAnalysis.user_id == user_id,
            VacancyAnalysis.status == "pending",
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        analysis = VacancyAnalysis(
            vacancy_id=vacancy_id,
            user_id=user_id,
        )
        db.add(analysis)

    analysis.detected_stack = analysis_result.get("detected_stack", [])
    analysis.detected_level = analysis_result.get("detected_level")
    analysis.attractiveness_score = float(
        analysis_result.get("attractiveness_score", 0)
    )
    analysis.ai_summary = analysis_result.get("ai_summary")
    analysis.analysis_details = {
        "pros": analysis_result.get("pros", []),
        "cons": analysis_result.get("cons", []),
        "raw": analysis_result,
    }
    analysis.status = "done"
    analysis.analyzed_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(analysis)

    logger.info(
        f"✅ Анализ сохранён: vacancy_id={vacancy_id} "
        f"user_id={user_id} "
        f"score={analysis.attractiveness_score}"
    )

    return analysis


async def mark_analysis_failed(
    db: AsyncSession, vacancy_id: int, user_id: int, error: str
) -> None:
    """Помечаем анализ как неудавшийся"""
    from sqlalchemy import select

    result = await db.execute(
        select(VacancyAnalysis).where(
            VacancyAnalysis.vacancy_id == vacancy_id,
            VacancyAnalysis.user_id == user_id,
            VacancyAnalysis.status.in_(["pending", "processing"]),
        )
    )
    analysis = result.scalar_one_or_none()

    if analysis:
        analysis.status = "failed"
        analysis.error_message = error
        analysis.analyzed_at = datetime.now(timezone.utc)
        await db.flush()
