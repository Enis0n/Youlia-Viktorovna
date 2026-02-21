from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import *
from config import ADMIN_IDS, CLUB_NAMES
from utils import format_club_info

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_club = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user

    # Сохраняем пользователя в базу данных
    await db.add_user(
        user_id=user.id,
        username=user.username or '',
        first_name=user.first_name,
        last_name=user.last_name or ''
    )

    is_admin = user.id in ADMIN_IDS
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот для управления школьными кружками и секциями.
С моей помощью ты можешь:
• Просматривать список доступных кружков
• Записываться на кружки
• Отслеживать свои записи
• Отменять регистрацию
"""

    if is_admin:
        welcome_text += "\n👑 У вас есть права администратора!"

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin)
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📚 *Доступные команды:*

/start - Начать работу с ботом
/help - Показать это сообщение
/stop - Остановить бота (выйти из меню)

Также вы можете использовать кнопки меню для навигации.
    """
    await message.answer(help_text, parse_mode='Markdown')


@router.message(Command('stop'))
async def cmd_stop(message: Message):
    """Обработчик команды /stop"""
    await message.answer(
        "👋 До свидания! Чтобы начать заново, нажмите /start",
        reply_markup=None
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    is_admin = callback.from_user.id in ADMIN_IDS
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard(is_admin)
    )
    await callback.answer()


@router.callback_query(F.data == "list_clubs")
async def list_clubs(callback: CallbackQuery):
    """Показывает список кружков"""
    text = "📋 *Список доступных кружков:*\n\n"

    for club_name in CLUB_NAMES:
        stats = await db.get_club_stats(club_name)
        text += format_club_info(club_name, stats['total_members'], stats['max_seats'])
        text += "\n" + "─" * 20 + "\n"

    await callback.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "register_club")
async def register_club_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс регистрации на кружок"""
    await callback.message.edit_text(
        "Выберите кружок для записи:",
        reply_markup=get_clubs_keyboard("register")
    )
    await state.set_state(RegistrationStates.waiting_for_club)
    await callback.answer()


@router.callback_query(RegistrationStates.waiting_for_club, F.data.startswith("register:"))
async def process_registration(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор кружка для регистрации"""
    club_name = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    success, message = await db.register_for_club(user_id, club_name)

    await callback.message.edit_text(
        message,
        reply_markup=get_back_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "my_registrations")
async def my_registrations(callback: CallbackQuery):
    """Показывает записи пользователя"""
    user_clubs = await db.get_user_clubs(callback.from_user.id)

    if not user_clubs:
        text = "Вы пока не записаны ни на один кружок."
    else:
        text = "📝 *Ваши записи на кружки:*\n\n"
        for club in user_clubs:
            stats = await db.get_club_stats(club)
            text += f"• {club}\n"
            text += f"  👥 Участников: {stats['total_members']}/{stats['max_seats']}\n\n"

    await callback.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_registration")
async def cancel_registration_start(callback: CallbackQuery):
    """Начинает процесс отмены регистрации"""
    user_clubs = await db.get_user_clubs(callback.from_user.id)

    if not user_clubs:
        await callback.message.edit_text(
            "У вас нет активных записей на кружки.",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите кружок для отмены записи:",
        reply_markup=get_clubs_keyboard("cancel")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:"))
async def process_cancellation(callback: CallbackQuery):
    """Обрабатывает отмену регистрации"""
    club_name = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    success = await db.cancel_registration(user_id, club_name)

    if success:
        text = f"✅ Запись на кружок '{club_name}' успешно отменена."
    else:
        text = "❌ Произошла ошибка при отмене записи."

    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
