from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models.vacancy import Vacancy
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def parse_salary(
    salary_data: dict | None,
) -> tuple[int | None, int | None, str | None, bool | None]:
    """
    Парсим зарплату из ответа HH.ru
    Возвращаем (from, to, currency, gross)
    """
    if not salary_data:
        return None, None, None, None

    return (
        salary_data.get("from"),
        salary_data.get("to"),
        salary_data.get("currency", "RUR"),
        salary_data.get("gross"),
    )


def parse_vacancy_from_hh(hh_data: dict[str, Any]) -> dict[str, Any]:
    """
    Конвертируем сырой ответ HH.ru в наш формат
    """
    salary_from, salary_to, currency, gross = parse_salary(hh_data.get("salary"))

    address = hh_data.get("address")
    area = hh_data.get("area", {})
    location = None
    if address:
        location = address.get("city") or area.get("name")
    elif area:
        location = area.get("name")

    schedule = hh_data.get("schedule", {})
    is_remote = schedule.get("id") == "remote" if schedule else False

    employer = hh_data.get("employer", {})
    company = employer.get("name") if employer else None

    experience = hh_data.get("experience", {})
    experience_id = experience.get("id") if experience else None

    published_at = None
    if pub_date := hh_data.get("published_at"):
        try:
            published_at = datetime.fromisoformat(pub_date)
        except ValueError:
            pass

    description = hh_data.get("description")

    snippet = hh_data.get("snippet", {})
    requirements = snippet.get("requirement") if snippet else None
    if not requirements and hh_data.get("key_skills"):
        skills = hh_data.get("key_skills", [])
        requirements = ", ".join(s.get("name", "") for s in skills)

    return {
        "hh_vacancy_id": str(hh_data["id"]),
        "title": hh_data.get("name", ""),
        "company": company,
        "url": hh_data.get("alternate_url", ""),
        "salary_from": salary_from,
        "salary_to": salary_to,
        "salary_currency": currency,
        "salary_gross": gross,
        "description": description,
        "requirements": requirements,
        "location": location,
        "is_remote": is_remote,
        "experience": experience_id,
        "published_at": published_at,
        "parsed_at": datetime.now(timezone.utc),
        "raw_data": hh_data,
    }


async def get_or_create_vacancy(
    db: AsyncSession,
    hh_data: dict[str, Any],
) -> tuple[Vacancy, bool]:
    """
    Получаем вакансию из БД или создаём новую
    Возвращает (vacancy, is_new)
    """
    hh_vacancy_id = str(hh_data["id"])

    result = await db.execute(
        select(Vacancy).where(Vacancy.hh_vacancy_id == hh_vacancy_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing, False

    vacancy_data = parse_vacancy_from_hh(hh_data)
    vacancy = Vacancy(**vacancy_data)
    db.add(vacancy)
    await db.flush()
    await db.refresh(vacancy)

    logger.info(
        f"✅ Новая вакансия сохранена: [{vacancy.hh_vacancy_id}] {vacancy.title}"
    )
    return vacancy, True
