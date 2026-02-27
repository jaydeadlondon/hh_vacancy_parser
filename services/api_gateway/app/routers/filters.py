from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from shared.models.user import User
from shared.models.user_filter import UserFilter
from pydantic import BaseModel


class FilterCreate(BaseModel):
    name: str = "Мой фильтр"
    keywords: list[str] | None = None
    excluded_keywords: list[str] | None = None
    min_salary: int | None = None
    max_salary: int | None = None
    experience_level: str | None = None
    location: str | None = None
    remote_ok: bool = False
    tech_stack: list[str] | None = None


class FilterResponse(BaseModel):
    id: int
    name: str
    keywords: list[str] | None
    excluded_keywords: list[str] | None
    min_salary: int | None
    max_salary: int | None
    experience_level: str | None
    location: str | None
    remote_ok: bool
    tech_stack: list[str] | None
    is_active: bool

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("", response_model=list[FilterResponse])
async def get_filters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserFilter]:
    result = await db.execute(
        select(UserFilter).where(UserFilter.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post("", response_model=FilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    data: FilterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserFilter:
    user_filter = UserFilter(user_id=current_user.id, **data.model_dump())
    db.add(user_filter)
    await db.flush()
    await db.refresh(user_filter)
    return user_filter


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    filter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(UserFilter).where(
            UserFilter.id == filter_id,
            UserFilter.user_id == current_user.id,
        )
    )
    user_filter = result.scalar_one_or_none()
    if not user_filter:
        raise HTTPException(status_code=404, detail="Фильтр не найден")
    await db.delete(user_filter)
