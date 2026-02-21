from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CLUB_NAMES


def get_main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Основная клавиатура для пользователей"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="📋 Список кружков",
        callback_data="list_clubs"
    ))
    builder.add(InlineKeyboardButton(
        text="✅ Записаться на кружок",
        callback_data="register_club"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 Мои записи",
        callback_data="my_registrations"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отменить запись",
        callback_data="cancel_registration"
    ))

    if is_admin:
        builder.add(InlineKeyboardButton(
            text="👑 Панель администратора",
            callback_data="admin_panel"
        ))

    builder.adjust(1)
    return builder.as_markup()


def get_clubs_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура со списком кружков для определенного действия"""
    builder = InlineKeyboardBuilder()

    for club in CLUB_NAMES:
        builder.add(InlineKeyboardButton(
            text=club,
            callback_data=f"{action}:{club}"
        ))

    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_main"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для администратора"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="📊 Статистика кружков",
        callback_data="admin_stats"
    ))
    builder.add(InlineKeyboardButton(
        text="✅ Отметить посещаемость",
        callback_data="admin_attendance"
    ))
    builder.add(InlineKeyboardButton(
        text="📤 Выгрузить списки",
        callback_data="admin_export"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Управление кружками",
        callback_data="admin_manage"
    ))
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_main"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_attendance_keyboard(club_name: str, members: list) -> InlineKeyboardMarkup:
    """Клавиатура для отметки посещаемости"""
    builder = InlineKeyboardBuilder()

    for member_id in members:
        # Здесь мы не можем использовать callback_data с произвольным текстом,
        # поэтому создадим упрощенную версию
        builder.add(InlineKeyboardButton(
            text=f"✅ {member_id}",  # В реальном проекте нужно получать имена
            callback_data=f"attendance:{club_name}:{member_id}"
        ))

    builder.add(InlineKeyboardButton(
        text="💾 Сохранить посещаемость",
        callback_data=f"save_attendance:{club_name}"
    ))
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="admin_panel"
    ))

    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_main"
    ))
    return builder.as_markup()