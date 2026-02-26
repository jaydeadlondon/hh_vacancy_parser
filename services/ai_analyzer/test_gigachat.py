import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from app.analyzer.gigachat_client import GigaChatClient
from app.analyzer.prompt import build_analysis_prompt
from shared.models.user_filter import UserFilter


async def test():
    mock_filter = UserFilter()
    mock_filter.keywords = ["Python", "FastAPI"]
    mock_filter.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis"]
    mock_filter.experience_level = "between1And3"

    prompt = build_analysis_prompt(
        vacancy_title="Python Backend Developer",
        vacancy_description="""
            Ищем Python разработчика в команду backend.
            Стек: Python 3.11, FastAPI, PostgreSQL, Redis, Docker.
            Задачи: разработка REST API, оптимизация запросов к БД,
            написание тестов, code review.
        """,
        vacancy_requirements="""
            Опыт Python от 1 года.
            Знание FastAPI или Django.
            Понимание SQL и работы с PostgreSQL.
            Опыт работы с Docker.
        """,
        company="Яндекс",
        salary_from=150000,
        salary_to=250000,
        user_filter=mock_filter,
    )

    print("📋 Промпт:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print()

    client = GigaChatClient()
    print("🧠 Отправляем запрос в GigaChat...")

    result = await client.analyze_vacancy(prompt)

    print("✅ Результат анализа:")
    print("=" * 60)
    import json

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test())
