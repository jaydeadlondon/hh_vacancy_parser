from typing import Any
from shared.models.user_filter import UserFilter
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def build_hh_params(user_filter: UserFilter) -> dict[str, Any]:
    """
    Конвертируем UserFilter в параметры для HH.ru API
    Документация параметров: https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij
    """
    params: dict[str, Any] = {
        "currency": "RUR",
        "only_with_salary": False,
    }

    if user_filter.keywords:
        params["text"] = " AND ".join(user_filter.keywords)
        params["search_field"] = ["name", "description"]

    if user_filter.min_salary:
        params["salary"] = user_filter.min_salary
        params["only_with_salary"] = True

    if user_filter.experience_level:
        params["experience"] = user_filter.experience_level

    if user_filter.location:
        area_id = CITY_TO_AREA_ID.get(user_filter.location.lower())
        if area_id:
            params["area"] = area_id
        else:
            logger.warning(f"Неизвестный город: {user_filter.location}")

    if user_filter.remote_ok:
        params["schedule"] = "remote"

    if user_filter.extra_params:
        params.update(user_filter.extra_params)

    logger.debug(f"Параметры HH для фильтра {user_filter.id}: {params}")
    return params


def apply_local_filters(
    vacancy: dict,
    user_filter: UserFilter,
) -> bool:
    """
    Локальная фильтрация после получения от API
    HH.ru не всегда точно фильтрует по keywords
    Возвращает True если вакансия проходит фильтр
    """
    title = vacancy.get("name", "").lower()
    snippet = vacancy.get("snippet", {})
    requirement = (snippet.get("requirement") or "").lower()
    responsibility = (snippet.get("responsibility") or "").lower()
    full_text = f"{title} {requirement} {responsibility}"

    if user_filter.excluded_keywords:
        for word in user_filter.excluded_keywords:
            if word.lower() in full_text:
                logger.debug(f"Вакансия отфильтрована по excluded_keyword: {word}")
                return False

    if user_filter.max_salary:
        salary = vacancy.get("salary")
        if salary:
            salary_to = salary.get("to")
            salary_from = salary.get("from")
            if salary_from and salary_from > user_filter.max_salary:
                return False

    return True


CITY_TO_AREA_ID: dict[str, int] = {
    "москва": 1,
    "санкт-петербург": 2,
    "спб": 2,
    "екатеринбург": 3,
    "новосибирск": 4,
    "казань": 88,
    "нижний новгород": 66,
    "челябинск": 104,
    "самара": 78,
    "омск": 68,
    "ростов-на-дону": 76,
    "уфа": 99,
    "красноярск": 26,
    "воронеж": 18,
    "пермь": 72,
    "волгоград": 24,
    "краснодар": 53,
    "минск": 153,
    "алматы": 160,
}
