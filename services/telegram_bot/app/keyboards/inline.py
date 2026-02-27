from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура приветствия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Регистрация", callback_data="register"),
        InlineKeyboardButton(text="🔑 Войти", callback_data="login"),
    )
    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
    )
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню после авторизации"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Мои фильтры", callback_data="my_filters"),
        InlineKeyboardButton(text="➕ Новый фильтр", callback_data="create_filter"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Топ-10 вакансий", callback_data="top10"),
        InlineKeyboardButton(text="🔎 Поиск", callback_data="search"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
    )
    return builder.as_markup()


def get_filters_keyboard(filters: list[dict]) -> InlineKeyboardMarkup:
    """Список фильтров с кнопками удаления"""
    builder = InlineKeyboardBuilder()
    for f in filters:
        builder.row(
            InlineKeyboardButton(
                text=f"{'✅' if f.get('is_active') else '❌'} {f['name']}",
                callback_data=f"filter_view:{f['id']}",
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"filter_delete:{f['id']}",
            ),
        )
    builder.row(
        InlineKeyboardButton(text="➕ Создать фильтр", callback_data="create_filter"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Подтверждение действия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel"),
    )
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Выбор уровня опыта"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌱 Без опыта", callback_data="exp:noExperience"),
    )
    builder.row(
        InlineKeyboardButton(
            text="🟢 Junior (1-3 года)", callback_data="exp:between1And3"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🟡 Middle (3-6 лет)", callback_data="exp:between3And6"
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔴 Senior (6+ лет)", callback_data="exp:moreThan6"),
    )
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="exp:skip"),
    )
    return builder.as_markup()


def get_remote_keyboard() -> InlineKeyboardMarkup:
    """Выбор формата работы"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏠 Только удалённо", callback_data="remote:true"),
        InlineKeyboardButton(text="🏢 Офис/гибрид", callback_data="remote:false"),
    )
    builder.row(
        InlineKeyboardButton(text="⏭ Любой формат", callback_data="remote:skip"),
    )
    return builder.as_markup()
