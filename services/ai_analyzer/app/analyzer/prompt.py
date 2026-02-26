from shared.models.user_filter import UserFilter


def build_analysis_prompt(
    vacancy_title: str,
    vacancy_description: str,
    vacancy_requirements: str,
    company: str,
    salary_from: int | None,
    salary_to: int | None,
    user_filter: UserFilter,
) -> str:
    """
    Строим промпт для GigaChat
    Передаём вакансию + желания пользователя
    Просим вернуть структурированный JSON
    """
    salary_str = "не указана"
    if salary_from and salary_to:
        salary_str = f"{salary_from} - {salary_to} руб."
    elif salary_from:
        salary_str = f"от {salary_from} руб."
    elif salary_to:
        salary_str = f"до {salary_to} руб."

    desired_stack = (
        ", ".join(user_filter.tech_stack) if user_filter.tech_stack else "не указан"
    )

    level_map = {
        "noExperience": "без опыта/стажёр",
        "between1And3": "Junior / Middle (1-3 года)",
        "between3And6": "Middle / Senior (3-6 лет)",
        "moreThan6": "Senior / Lead (6+ лет)",
    }
    desired_level = level_map.get(user_filter.experience_level or "", "не указан")

    prompt = f"""Ты — опытный HR-аналитик и технический рекрутер.
Проанализируй вакансию и дай оценку её привлекательности для конкретного кандидата.

## Вакансия

**Название:** {vacancy_title}
**Компания:** {company or "не указана"}
**Зарплата:** {salary_str}

**Описание и требования:**
{vacancy_description or vacancy_requirements or "не указано"}

## Профиль кандидата

**Желаемый стек технологий:** {desired_stack}
**Желаемый уровень:** {desired_level}
**Ключевые слова:** {", ".join(user_filter.keywords or []) or "не указаны"}

## Задача

Проанализируй вакансию и верни результат СТРОГО в формате JSON без markdown блоков:

{{
    "detected_stack": ["список", "технологий", "из", "вакансии"],
    "detected_level": "Junior или Middle или Senior или Lead",
    "attractiveness_score": число от 0 до 100,
    "ai_summary": "краткое резюме 2-3 предложения почему вакансия подходит или не подходит",
    "pros": ["плюс 1", "плюс 2"],
    "cons": ["минус 1", "минус 2"]
}}

## Правила оценки attractiveness_score

- 90-100: идеальное совпадение стека и уровня
- 70-89:  хорошее совпадение, небольшие расхождения
- 50-69:  частичное совпадение, есть чему учиться
- 30-49:  мало совпадений, вакансия скорее не подходит
- 0-29:   вакансия не подходит кандидату

Верни ТОЛЬКО JSON, без пояснений и markdown."""

    return prompt
