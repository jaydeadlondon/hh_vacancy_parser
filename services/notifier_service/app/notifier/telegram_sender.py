import httpx
from app.core.config import settings
from shared.models.vacancy import Vacancy
from shared.models.vacancy_analysis import VacancyAnalysis
from shared.utils.logger import get_logger

logger = get_logger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramSender:
    """
    Отправляем сообщения в Telegram через Bot API
    Используем httpx напрямую — без aiogram зависимости
    """

    def __init__(self) -> None:
        self._token = settings.telegram_bot_token
        self._base_url = f"https://api.telegram.org/bot{self._token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """
        Отправляем сообщение пользователю
        Возвращает True если успешно
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_web_page_preview,
                    },
                    timeout=15.0,
                )
                data = response.json()

                if not data.get("ok"):
                    logger.error(
                        f"Telegram API ошибка: {data.get('description')} "
                        f"для chat_id={chat_id}"
                    )
                    return False
                return True

            except httpx.RequestError as e:
                logger.error(f"Ошибка отправки в Telegram: {e}")
                return False

    def format_vacancy_message(
        self, vacancy: Vacancy, analysis: VacancyAnalysis
    ) -> str:
        """
        Форматируем сообщение о новой вакансии
        Используем HTML разметку Telegram
        """
        level_icons = {
            "Junior": "🟢",
            "Middle": "🟡",
            "Senior": "🔴",
            "Lead": "⭐",
        }
        level_icon = level_icons.get(analysis.detected_level or "", "⚪")

        score = analysis.attractiveness_score or 0
        score_bar = self._make_score_bar(score)

        salary_str = self._format_salary(vacancy)

        stack_str = ""
        if analysis.detected_stack:
            stack_str = " • ".join(analysis.detected_stack[:8])

        details = analysis.analysis_details or {}
        pros = details.get("pros", [])
        cons = details.get("cons", [])

        pros_str = "\n".join(f"  ✅ {p}" for p in pros[:3]) if pros else ""
        cons_str = "\n".join(f"  ❌ {c}" for c in cons[:2]) if cons else ""

        message = f"""🔔 <b>Новая вакансия!</b>

<b>{vacancy.title}</b>
🏢 {vacancy.company or "Компания не указана"}

{score_bar} <b>{score:.0f}%</b> привлекательность
{level_icon} Уровень: <b>{analysis.detected_level or "не определён"}</b>
💰 Зарплата: <b>{salary_str}</b>
📍 {vacancy.location or "локация не указана"}{"  🏠 Удалённо" if vacancy.is_remote else ""}

🛠 <b>Стек:</b> {stack_str or "не указан"}

💬 <i>{analysis.ai_summary or ""}</i>"""

        if pros_str:
            message += f"\n\n<b>Плюсы:</b>\n{pros_str}"

        if cons_str:
            message += f"\n\n<b>Минусы:</b>\n{cons_str}"

        message += f"\n\n🔗 <a href='{vacancy.url}'>Открыть вакансию</a>"

        return message

    def format_digest_message(
        self,
        vacancies_with_analyses: list[tuple[Vacancy, VacancyAnalysis]],
        week_number: int,
    ) -> str:
        """
        Форматируем еженедельный дайджест топ-10
        """
        header = f"""📊 <b>Еженедельный дайджест вакансий</b>
Неделя #{week_number} | Топ-{len(vacancies_with_analyses)} лучших вакансий

"""
        items = []
        for i, (vacancy, analysis) in enumerate(vacancies_with_analyses, 1):
            score = analysis.attractiveness_score or 0
            salary_str = self._format_salary(vacancy)

            item = (
                f"{i}. <b>{vacancy.title}</b>\n"
                f"   🏢 {vacancy.company or 'н/д'} | "
                f"💰 {salary_str} | "
                f"⭐ {score:.0f}%\n"
                f"   🔗 <a href='{vacancy.url}'>Открыть</a>"
            )
            items.append(item)

        return header + "\n\n".join(items)

    def _format_salary(self, vacancy: Vacancy) -> str:
        """Форматируем зарплату"""
        if vacancy.salary_from and vacancy.salary_to:
            return f"{vacancy.salary_from:,} – {vacancy.salary_to:,} {vacancy.salary_currency or 'RUR'}"
        elif vacancy.salary_from:
            return f"от {vacancy.salary_from:,} {vacancy.salary_currency or 'RUR'}"
        elif vacancy.salary_to:
            return f"до {vacancy.salary_to:,} {vacancy.salary_currency or 'RUR'}"
        return "не указана"

    def _make_score_bar(self, score: float) -> str:
        """Визуальная полоска оценки"""
        filled = int(score / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty
