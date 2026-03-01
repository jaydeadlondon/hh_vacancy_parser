from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from shared.models.user import User
from shared.models.vacancy import Vacancy
from shared.models.vacancy_analysis import VacancyAnalysis

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


class VacancyResponse(BaseModel):
    id: int
    title: str
    company: str | None
    url: str
    salary_from: int | None
    salary_to: int | None
    salary_currency: str | None
    location: str | None
    is_remote: bool
    attractiveness_score: float | None = None
    detected_level: str | None = None
    detected_stack: list[str] | None = None
    ai_summary: str | None = None

    model_config = {"from_attributes": True}


def _build_vacancy_response(vacancy: Vacancy, analysis: VacancyAnalysis) -> dict:
    return {
        "id": vacancy.id,
        "title": vacancy.title,
        "company": vacancy.company,
        "url": vacancy.url,
        "salary_from": vacancy.salary_from,
        "salary_to": vacancy.salary_to,
        "salary_currency": vacancy.salary_currency,
        "location": vacancy.location,
        "is_remote": vacancy.is_remote,
        "attractiveness_score": analysis.attractiveness_score,
        "detected_level": analysis.detected_level,
        "detected_stack": analysis.detected_stack,
        "ai_summary": analysis.ai_summary,
    }


@router.get("/list", response_model=list[VacancyResponse])
async def list_vacancies(
    limit: int = Query(default=50, le=200),
    min_score: float | None = Query(default=None),
    level: str | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Список вакансий с фильтрами для дашборда"""
    query = (
        select(Vacancy, VacancyAnalysis)
        .join(VacancyAnalysis, VacancyAnalysis.vacancy_id == Vacancy.id)
        .where(
            VacancyAnalysis.user_id == current_user.id,
            VacancyAnalysis.status == "done",
        )
    )

    if min_score is not None:
        query = query.where(VacancyAnalysis.attractiveness_score >= min_score)

    if level:
        query = query.where(VacancyAnalysis.detected_level == level)

    if q:
        query = query.where(Vacancy.title.ilike(f"%{q}%"))

    query = query.order_by(desc(VacancyAnalysis.attractiveness_score)).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [_build_vacancy_response(row.Vacancy, row.VacancyAnalysis) for row in rows]


@router.get("/top", response_model=list[VacancyResponse])
async def get_top_vacancies(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Топ вакансий по score"""
    result = await db.execute(
        select(Vacancy, VacancyAnalysis)
        .join(VacancyAnalysis, VacancyAnalysis.vacancy_id == Vacancy.id)
        .where(
            VacancyAnalysis.user_id == current_user.id,
            VacancyAnalysis.status == "done",
        )
        .order_by(desc(VacancyAnalysis.attractiveness_score))
        .limit(limit)
    )
    rows = result.all()
    return [_build_vacancy_response(row.Vacancy, row.VacancyAnalysis) for row in rows]


@router.get("/search", response_model=list[VacancyResponse])
async def search_vacancies(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=5, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Поиск вакансий"""
    result = await db.execute(
        select(Vacancy, VacancyAnalysis)
        .join(VacancyAnalysis, VacancyAnalysis.vacancy_id == Vacancy.id)
        .where(
            VacancyAnalysis.user_id == current_user.id,
            VacancyAnalysis.status == "done",
            Vacancy.title.ilike(f"%{q}%"),
        )
        .order_by(desc(VacancyAnalysis.attractiveness_score))
        .limit(limit)
    )
    rows = result.all()
    return [_build_vacancy_response(row.Vacancy, row.VacancyAnalysis) for row in rows]
