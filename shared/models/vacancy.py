from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .vacancy_analysis import VacancyAnalysis
    from .notification import Notification


class Vacancy(Base, TimestampMixin):
    __tablename__ = "vacancies"

    __table_args__ = (UniqueConstraint("hh_vacancy_id", name="uq_vacancies_hh_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    hh_vacancy_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(
        String(8), nullable=True, default="RUR"
    )
    salary_gross: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    experience: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    analyses: Mapped[list[VacancyAnalysis]] = relationship(
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )
