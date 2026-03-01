from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from app.api.client import APIClient
from app.keyboards.inline import get_back_keyboard
from shared.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


class SearchStates(StatesGroup):
    waiting_query = State()


@router.message(Command("top10"))
@router.callback_query(F.data == "top10")
async def show_top10(event: Message | CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    if isinstance(event, CallbackQuery):
        await event.message.edit_text("⏳ Загружаю топ вакансий...")
        await event.answer()
    else:
        loading_msg = await event.answer("⏳ Загружаю топ вакансий...")

    client = APIClient(token=token)
    result = await client.get_top_vacancies(limit=10)

    if result["status"] != 200:
        text = "❌ Ошибка получения вакансий"
        if isinstance(event, Message):
            await loading_msg.edit_text(text)
        else:
            await event.message.edit_text(text, reply_markup=get_back_keyboard())
        return

    vacancies = result["data"]

    if not vacancies:
        text = (
            "📭 Пока нет проанализированных вакансий.\n\n"
            "Создай фильтр и дождись первого цикла парсера!"
        )
        if isinstance(event, Message):
            await loading_msg.edit_text(text, reply_markup=get_back_keyboard())
        else:
            await event.message.edit_text(text, reply_markup=get_back_keyboard())
        return

    lines = ["🏆 <b>Топ вакансий для тебя:</b>\n"]
    for i, v in enumerate(vacancies, 1):
        score = v.get("attractiveness_score", 0)
        salary_from = v.get("salary_from")
        salary_to = v.get("salary_to")

        if salary_from and salary_to:
            salary_str = f"{salary_from:,}–{salary_to:,}"
        elif salary_from:
            salary_str = f"от {salary_from:,}"
        else:
            salary_str = "з/п не указана"

        lines.append(
            f"{i}. <b>{v['title']}</b>\n"
            f"   🏢 {v.get('company', 'н/д')} | "
            f"💰 {salary_str} | "
            f"⭐ {score:.0f}%\n"
            f"   🔗 <a href='{v['url']}'>Открыть</a>"
        )

    text = "\n\n".join(lines)

    if isinstance(event, Message):
        await loading_msg.edit_text(
            text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await event.message.edit_text(
            text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@router.message(Command("search"))
@router.callback_query(F.data == "search")
async def start_search(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_query)

    text = (
        "🔎 <b>Поиск вакансий</b>\n\n"
        "Введи поисковый запрос:\n"
        "<i>Например: Python Middle, React Frontend, Data Science</i>"
    )

    if isinstance(event, Message):
        await event.answer(text, parse_mode="HTML")
    else:
        await event.message.edit_text(text, parse_mode="HTML")
        await event.answer()


@router.message(SearchStates.waiting_query)
async def do_search(message: Message, state: FSMContext) -> None:
    query = message.text.strip() if message.text else ""
    if not query:
        await message.answer("❌ Введи поисковый запрос")
        return

    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    loading = await message.answer(f"🔍 Ищу: <b>{query}</b>...", parse_mode="HTML")

    client = APIClient(token=token)
    result = await client.search_vacancies(query=query, limit=5)

    await state.set_state(None)

    if result["status"] != 200:
        await loading.edit_text("❌ Ошибка поиска")
        return

    vacancies = result["data"]

    if not vacancies:
        await loading.edit_text(
            f"😔 По запросу <b>{query}</b> ничего не найдено.\n\n"
            "Попробуй другой запрос или создай фильтр!",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
        )
        return

    lines = [f'🔎 <b>Результаты по запросу "{query}":</b>\n']
    for i, v in enumerate(vacancies, 1):
        score = v.get("attractiveness_score", 0)
        lines.append(
            f"{i}. <b>{v['title']}</b>\n"
            f"   🏢 {v.get('company', 'н/д')} | ⭐ {score:.0f}%\n"
            f"   🔗 <a href='{v['url']}'>Открыть</a>"
        )

    await loading.edit_text(
        "\n\n".join(lines),
        reply_markup=get_back_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
