from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class UserFilter(Base, TimestampMixin):
    __tablename__ = "user_filters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="Мой фильтр",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Слова которые ДОЛЖНЫ быть в вакансии",
    )
    excluded_keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Слова которые НЕ должны быть в вакансии",
    )
    min_salary: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    max_salary: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    experience_level: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    remote_ok: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    tech_stack: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    extra_params: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="filters",
    )
