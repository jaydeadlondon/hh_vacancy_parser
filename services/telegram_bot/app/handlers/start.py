from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.api.client import APIClient
from app.keyboards.inline import get_main_menu_keyboard, get_start_keyboard
from shared.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


class RegisterStates(StatesGroup):
    waiting_username = State()
    waiting_email = State()
    waiting_password = State()


class LoginStates(StatesGroup):
    waiting_username = State()
    waiting_password = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    if token:
        await message.answer(
            "👋 С возвращением!\n\nЧто хочешь сделать?",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(
            "👋 Привет! Я помогу найти лучшие вакансии на HH.ru\n\n"
            "🤖 Что я умею:\n"
            "• Парсить вакансии по твоим фильтрам\n"
            "• Анализировать их через AI\n"
            "• Уведомлять о лучших предложениях\n"
            "• Делать еженедельный дайджест\n\n"
            "Начнём?",
            reply_markup=get_start_keyboard(),
        )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыбери действие:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery) -> None:
    help_text = (
        "❓ <b>Помощь</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/filters — управление фильтрами\n"
        "/top10 — топ вакансий\n"
        "/search — поиск вакансий\n\n"
        "<b>Как работает бот:</b>\n"
        "1. Создай фильтр с нужными параметрами\n"
        "2. Каждый час парсер ищет новые вакансии\n"
        "3. AI анализирует каждую вакансию\n"
        "4. Лучшие вакансии приходят мгновенно\n"
        "5. Каждую неделю — дайджест топ-10"
    )
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Профиль ──────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    token = state_data.get("jwt_token")

    client = APIClient(token=token)
    result = await client.get_me()

    if result["status"] != 200:
        await callback.answer("❌ Ошибка загрузки профиля", show_alert=True)
        return

    user = result["data"]

    # Проверяем telegram_chat_id правильно
    tg_id = user.get("telegram_chat_id")
    tg_username = user.get("telegram_username")

    if tg_id:
        tg_str = f"@{tg_username}" if tg_username else f"ID: {tg_id}"
    else:
        tg_str = "не привязан"

    text = (
        f"👤 <b>Мой профиль</b>\n\n"
        f"🔑 Логин: <b>{user['username']}</b>\n"
        f"📧 Email: <b>{user['email']}</b>\n"
        f"💬 Telegram: <b>{tg_str}</b>\n"
        f"✅ Активен: <b>{'Да' if user['is_active'] else 'Нет'}</b>\n"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Регистрация ──────────────────────────────────────────────────────────────


@router.callback_query(F.data == "register")
async def start_register(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegisterStates.waiting_username)
    await callback.message.edit_text(
        "📝 <b>Регистрация</b>\n\n"
        "Шаг 1/3: Придумай имя пользователя\n"
        "<i>Только буквы, цифры, _ и - (от 3 до 64 символов)</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RegisterStates.waiting_username)
async def register_username(message: Message, state: FSMContext) -> None:
    username = message.text.strip() if message.text else ""
    if len(username) < 3:
        await message.answer("❌ Слишком короткое имя. Минимум 3 символа.")
        return

    await state.update_data(reg_username=username)
    await state.set_state(RegisterStates.waiting_email)
    await message.answer(
        f"✅ Имя: <b>{username}</b>\n\nШаг 2/3: Введи email адрес",
        parse_mode="HTML",
    )


@router.message(RegisterStates.waiting_email)
async def register_email(message: Message, state: FSMContext) -> None:
    email = message.text.strip() if message.text else ""
    if "@" not in email or "." not in email:
        await message.answer("❌ Некорректный email. Попробуй ещё раз.")
        return

    await state.update_data(reg_email=email)
    await state.set_state(RegisterStates.waiting_password)
    await message.answer(
        "Шаг 3/3: Придумай пароль\n<i>Минимум 8 символов</i>",
        parse_mode="HTML",
    )


@router.message(RegisterStates.waiting_password)
async def register_password(message: Message, state: FSMContext) -> None:
    password = message.text.strip() if message.text else ""
    await message.delete()

    if len(password) < 8:
        await message.answer("❌ Пароль слишком короткий. Минимум 8 символов.")
        return

    data = await state.get_data()
    username = data["reg_username"]
    email = data["reg_email"]

    client = APIClient()
    result = await client.register(username, email, password)

    if result["status"] == 201:
        login_result = await client.login(username, password)
        if login_result["status"] == 200:
            token = login_result["data"]["access_token"]
            await state.update_data(jwt_token=token)

            authed_client = APIClient(token=token)
            tg_result = await authed_client.link_telegram(
                telegram_chat_id=message.chat.id,
                telegram_username=message.from_user.username,
            )
            logger.info(f"Привязка Telegram: {tg_result}")

        await state.set_state(None)
        await message.answer(
            f"🎉 <b>Регистрация успешна!</b>\n\n"
            f"Добро пожаловать, <b>{username}</b>!\n"
            f"Telegram аккаунт привязан ✅\n\n"
            f"Создай первый фильтр чтобы начать получать вакансии 👇",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        error = result["data"].get("detail", "Неизвестная ошибка")
        await state.set_state(None)
        await message.answer(
            f"❌ Ошибка регистрации: {error}\n\nПопробуй ещё раз /start"
        )


# ─── Авторизация ──────────────────────────────────────────────────────────────


@router.callback_query(F.data == "login")
async def start_login(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LoginStates.waiting_username)
    await callback.message.edit_text(
        "🔑 <b>Вход в аккаунт</b>\n\nВведи имя пользователя:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(LoginStates.waiting_username)
async def login_username(message: Message, state: FSMContext) -> None:
    await state.update_data(login_username=message.text.strip())
    await state.set_state(LoginStates.waiting_password)
    await message.answer("Введи пароль:")


@router.message(LoginStates.waiting_password)
async def login_password(message: Message, state: FSMContext) -> None:
    password = message.text.strip() if message.text else ""
    await message.delete()

    data = await state.get_data()
    username = data["login_username"]

    client = APIClient()
    result = await client.login(username, password)

    if result["status"] == 200:
        token = result["data"]["access_token"]
        await state.update_data(jwt_token=token)
        await state.set_state(None)

        authed_client = APIClient(token=token)
        tg_result = await authed_client.link_telegram(
            telegram_chat_id=message.chat.id,
            telegram_username=message.from_user.username,
        )
        logger.info(f"Привязка Telegram при логине: {tg_result}")

        await message.answer(
            "✅ <b>Вход выполнен!</b>\n\nЧто хочешь сделать?",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await state.set_state(None)
        await message.answer(
            "❌ Неверный логин или пароль.\nПопробуй ещё раз /start",
        )
