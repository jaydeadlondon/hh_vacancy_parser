# services/parser_service/test_hh.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.parser.hh_client import HHClient
from app.parser.filters import build_hh_params, apply_local_filters
from shared.models.user_filter import UserFilter


async def test():
    async with HHClient() as hh:
        # Симулируем фильтр пользователя
        mock_filter = UserFilter()
        mock_filter.id = 1
        mock_filter.user_id = 1
        mock_filter.name = "Python Backend"
        mock_filter.keywords = ["Python"]
        mock_filter.excluded_keywords = ["QA", "тестировщик", "аналитик", "1С"]
        mock_filter.min_salary = 100000
        mock_filter.max_salary = None
        mock_filter.experience_level = "between1And3"
        mock_filter.location = "москва"
        mock_filter.remote_ok = False
        mock_filter.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        mock_filter.extra_params = None

        # Строим параметры для HH API
        hh_params = build_hh_params(mock_filter)
        print(f"📋 Параметры запроса к HH: {hh_params}")
        print()

        # Получаем вакансии
        data = await hh.search_vacancies(hh_params)
        items = data.get("items", [])

        print(f"📦 Всего найдено: {data.get('found', 0)} вакансий")
        print(f"📄 На странице: {len(items)}")
        print()

        # Применяем локальные фильтры
        passed = []
        rejected = []
        for v in items:
            if apply_local_filters(v, mock_filter):
                passed.append(v)
            else:
                rejected.append(v)

        print(f"✅ Прошли фильтр: {len(passed)}")
        print(f"❌ Отфильтрованы: {len(rejected)}")
        print()

        print("=" * 60)
        print("✅ ПРОШЕДШИЕ ФИЛЬТР:")
        print("=" * 60)
        for v in passed[:5]:  # показываем первые 5
            salary = v.get("salary")
            salary_str = "не указана"
            if salary:
                sal_from = salary.get("from", "?")
                sal_to = salary.get("to", "?")
                salary_str = f"{sal_from} - {sal_to} {salary.get('currency', '')}"

            snippet = v.get("snippet", {})
            requirement = snippet.get("requirement", "")

            print(f"  📌 {v['name']}")
            print(f"     Компания:  {v.get('employer', {}).get('name', 'н/д')}")
            print(f"     Зарплата:  {salary_str}")
            print(f"     Опыт:      {v.get('experience', {}).get('name', 'н/д')}")
            print(f"     Требования: {requirement[:100] if requirement else 'н/д'}...")
            print(f"     Ссылка:    {v.get('alternate_url')}")
            print()


if __name__ == "__main__":
    asyncio.run(test())
