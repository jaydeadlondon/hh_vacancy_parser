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
    location: str | None
    is_remote: bool
    attractiveness_score: float | None = None

    model_config = {"from_attributes": True}


@router.get("/top", response_model=list[VacancyResponse])
async def get_top_vacancies(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
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
    return [
        {
            **{c.name: getattr(row.Vacancy, c.name) for c in Vacancy.__table__.columns},
            "attractiveness_score": row.VacancyAnalysis.attractiveness_score,
        }
        for row in rows
    ]


@router.get("/search", response_model=list[VacancyResponse])
async def search_vacancies(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=5, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
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
    return [
        {
            **{c.name: getattr(row.Vacancy, c.name) for c in Vacancy.__table__.columns},
            "attractiveness_score": row.VacancyAnalysis.attractiveness_score,
        }
        for row in rows
    ]
