from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from app.api.client import APIClient
from app.keyboards.inline import (
    get_back_keyboard,
    get_experience_keyboard,
    get_filters_keyboard,
    get_main_menu_keyboard,
    get_remote_keyboard,
    get_confirm_keyboard,
)
from shared.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


class FilterCreateStates(StatesGroup):
    waiting_name = State()
    waiting_keywords = State()
    waiting_excluded = State()
    waiting_salary = State()
    waiting_experience = State()
    waiting_remote = State()
    waiting_stack = State()
    waiting_location = State()


@router.message(Command("filters"))
@router.callback_query(F.data == "my_filters")
async def show_filters(event: Message | CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    client = APIClient(token=token)
    result = await client.get_filters()

    if result["status"] != 200:
        text = "❌ Ошибка получения фильтров"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.edit_text(text, reply_markup=get_back_keyboard())
        return

    filters = result["data"]

    if not filters:
        text = (
            "🔍 <b>Мои фильтры</b>\n\n"
            "У тебя пока нет фильтров.\n"
            "Создай первый — я начну искать вакансии!"
        )
    else:
        text = f"🔍 <b>Мои фильтры</b> ({len(filters)} шт.)\n\nВыбери фильтр:"

    keyboard = get_filters_keyboard(filters)

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith("filter_delete:"))
async def confirm_delete_filter(callback: CallbackQuery) -> None:
    filter_id = callback.data.split(":")[1]
    await callback.message.edit_text(
        "🗑 Удалить этот фильтр?",
        reply_markup=get_confirm_keyboard(f"delete_filter:{filter_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delete_filter:"))
async def delete_filter(callback: CallbackQuery, state: FSMContext) -> None:
    filter_id = int(callback.data.split(":")[2])
    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    client = APIClient(token=token)
    result = await client.delete_filter(filter_id)

    if result["status"] in (200, 204):
        await callback.message.edit_text(
            "✅ Фильтр удалён",
            reply_markup=get_back_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка удаления фильтра",
            reply_markup=get_back_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "create_filter")
async def start_create_filter(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FilterCreateStates.waiting_name)
    await state.update_data(new_filter={})
    await callback.message.edit_text(
        "➕ <b>Создание фильтра</b>\n\n"
        "Шаг 1/8: Как назовём фильтр?\n"
        "<i>Например: Python Backend, Frontend React</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(FilterCreateStates.waiting_name)
async def filter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("❌ Введи название фильтра")
        return

    await state.update_data(new_filter={"name": name})
    await state.set_state(FilterCreateStates.waiting_keywords)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Шаг 2/8: Ключевые слова для поиска\n"
        "<i>Через запятую. Например: Python, FastAPI, Django\n"
        "Отправь — чтобы пропустить</i>",
        parse_mode="HTML",
    )


@router.message(FilterCreateStates.waiting_keywords)
async def filter_keywords(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if text and text != "-":
        keywords = [k.strip() for k in text.split(",") if k.strip()]
        new_filter["keywords"] = keywords

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_excluded)
    await message.answer(
        "Шаг 3/8: Исключить слова\n"
        "<i>Вакансии с этими словами не покажу.\n"
        "Например: 1С, QA, тестировщик\n"
        "Отправь — чтобы пропустить</i>",
        parse_mode="HTML",
    )


@router.message(FilterCreateStates.waiting_excluded)
async def filter_excluded(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if text and text != "-":
        excluded = [k.strip() for k in text.split(",") if k.strip()]
        new_filter["excluded_keywords"] = excluded

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_salary)
    await message.answer(
        "Шаг 4/8: Минимальная зарплата (руб.)\n"
        "<i>Например: 100000\n"
        "Отправь — чтобы пропустить</i>",
        parse_mode="HTML",
    )


@router.message(FilterCreateStates.waiting_salary)
async def filter_salary(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if text and text != "-":
        try:
            new_filter["min_salary"] = int(text.replace(" ", ""))
        except ValueError:
            await message.answer("❌ Введи число. Например: 100000")
            return

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_experience)
    await message.answer(
        "Шаг 5/8: Уровень опыта",
        reply_markup=get_experience_keyboard(),
    )


@router.callback_query(F.data.startswith("exp:"))
async def filter_experience(callback: CallbackQuery, state: FSMContext) -> None:
    exp_value = callback.data.split(":")[1]
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if exp_value != "skip":
        new_filter["experience_level"] = exp_value

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_remote)
    await callback.message.edit_text(
        "Шаг 6/8: Формат работы",
        reply_markup=get_remote_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remote:"))
async def filter_remote(callback: CallbackQuery, state: FSMContext) -> None:
    remote_value = callback.data.split(":")[1]
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if remote_value != "skip":
        new_filter["remote_ok"] = remote_value == "true"

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_stack)
    await callback.message.edit_text(
        "Шаг 7/8: Желаемый стек технологий\n"
        "<i>AI будет сравнивать вакансии с этим стеком.\n"
        "Например: Python, FastAPI, PostgreSQL, Redis\n"
        "Отправь — чтобы пропустить</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(FilterCreateStates.waiting_stack)
async def filter_stack(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if text and text != "-":
        stack = [s.strip() for s in text.split(",") if s.strip()]
        new_filter["tech_stack"] = stack

    await state.update_data(new_filter=new_filter)
    await state.set_state(FilterCreateStates.waiting_location)
    await message.answer(
        "Шаг 8/8: Город\n"
        "<i>Например: Москва, Санкт-Петербург\n"
        "Отправь — для любого города</i>",
        parse_mode="HTML",
    )


@router.message(FilterCreateStates.waiting_location)
async def filter_location(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    new_filter = data.get("new_filter", {})

    if text and text != "-":
        new_filter["location"] = text

    token = data.get("jwt_token")
    client = APIClient(token=token)
    result = await client.create_filter(new_filter)

    await state.set_state(None)

    if result["status"] == 201:
        name = new_filter.get("name", "Новый фильтр")
        keywords = new_filter.get("keywords", [])
        stack = new_filter.get("tech_stack", [])
        salary = new_filter.get("min_salary", "не указана")

        summary = (
            f"✅ <b>Фильтр создан!</b>\n\n"
            f"📌 <b>{name}</b>\n"
            f"🔑 Ключевые слова: {', '.join(keywords) or 'не указаны'}\n"
            f"🛠 Стек: {', '.join(stack) or 'не указан'}\n"
            f"💰 Мин. зарплата: {salary} руб.\n\n"
            f"Парсер запустится в ближайший час и найдёт вакансии! 🚀"
        )
        await message.answer(
            summary,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        error = result["data"].get("detail", "Неизвестная ошибка")
        await message.answer(
            f"❌ Ошибка создания фильтра: {error}",
            reply_markup=get_back_keyboard(),
        )
