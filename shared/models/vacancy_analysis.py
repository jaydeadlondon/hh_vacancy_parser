from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .vacancy import Vacancy
    from .user import User


class VacancyAnalysis(Base, TimestampMixin):
    __tablename__ = "vacancy_analyses"

    __table_args__ = (
        CheckConstraint(
            "attractiveness_score >= 0 AND attractiveness_score <= 100",
            name="chk_attractiveness_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    detected_stack: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    detected_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    attractiveness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="pending / processing / done / failed",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    vacancy: Mapped[Vacancy] = relationship(back_populates="analyses")
    user: Mapped[User] = relationship(back_populates="vacancy_analyses")
