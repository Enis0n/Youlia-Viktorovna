from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import tempfile
import os
import csv
import io
from datetime import datetime

from database import db
from keyboards import *
from config import ADMIN_IDS, CLUB_NAMES, MAX_CLUB_SEATS

admin_router = Router()


class AttendanceStates(StatesGroup):
    waiting_for_club = State()
    marking_attendance = State()


# Фильтр для проверки прав администратора
async def admin_filter(callback: CallbackQuery) -> bool:
    return callback.from_user.id in ADMIN_IDS


@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Панель администратора"""
    if not await admin_filter(callback):
        await callback.answer("У вас нет прав администратора!", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 *Панель администратора*\n\nВыберите действие:",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показывает статистику по всем кружкам"""
    if not await admin_filter(callback):
        return

    text = "📊 *Статистика кружков:*\n\n"

    for club_name in CLUB_NAMES:
        stats = await db.get_club_stats(club_name)

        # Форматируем информацию о кружке
        text += f"*{club_name}*\n"
        text += f"👥 Участников: {stats['total_members']}/{stats['max_seats']}\n"
        text += f"📊 Свободных мест: {stats['max_seats'] - stats['total_members']}\n"

        # Добавляем информацию о пропусках
        if stats['absences']:
            text += "📈 *Пропуски:*\n"
            for user_id, absences in stats['absences'].items():
                # Получаем имя пользователя из БД
                users = await db.get_all_users()
                user_name = users.get(str(user_id), {}).get('first_name', f"ID:{user_id}")
                text += f"  • {user_name}: {absences} пропусков\n"
        else:
            text += "✅ Пропусков нет\n"

        text += "\n" + "─" * 20 + "\n"

    await callback.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_attendance")
async def admin_attendance_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс отметки посещаемости"""
    if not await admin_filter(callback):
        return

    await callback.message.edit_text(
        "Выберите кружок для отметки посещаемости:",
        reply_markup=get_clubs_keyboard("attendance")
    )
    await state.set_state(AttendanceStates.waiting_for_club)
    await callback.answer()


@admin_router.callback_query(AttendanceStates.waiting_for_club, F.data.startswith("attendance:"))
async def admin_attendance_club(callback: CallbackQuery, state: FSMContext):
    """Показывает список участников для отметки посещаемости"""
    if not await admin_filter(callback):
        return

    club_name = callback.data.split(":", 1)[1]
    members = await db.get_club_members(club_name)

    if not members:
        await callback.message.edit_text(
            f"На кружок '{club_name}' никто не записан.",
            reply_markup=get_back_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    # Получаем имена пользователей
    users = await db.get_all_users()
    members_list = []
    for member_id in members:
        user_info = users.get(member_id, {})
        name = user_info.get('first_name', f"ID:{member_id}")
        members_list.append(f"{name} (ID:{member_id})")

    text = f"📝 *Отметка посещаемости: {club_name}*\n\n"
    text += "Список участников:\n"
    for i, member in enumerate(members_list, 1):
        text += f"{i}. {member}\n"
    text += "\n❌ Функция отметки посещаемости в разработке"

    await callback.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    await state.clear()
    await callback.answer()


@admin_router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    """Выгружает отчеты по кружкам"""
    if not await admin_filter(callback):
        return

    try:
        # Создаем CSV файл в памяти
        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовок
        writer.writerow(['Отчет по посещаемости кружков'])
        writer.writerow(['Дата создания:', datetime.now().strftime('%Y-%m-%d %H:%M')])
        writer.writerow([])

        users = await db.get_all_users()

        for club_name in CLUB_NAMES:
            stats = await db.get_club_stats(club_name)

            writer.writerow([f"=== {club_name} ==="])
            writer.writerow(['Всего участников:', stats['total_members']])
            writer.writerow(['Максимум мест:', stats['max_seats']])
            writer.writerow([])

            if stats['absences']:
                writer.writerow(['Список участников с пропусками:'])
                writer.writerow(['Имя', 'ID', 'Количество пропусков'])

                for user_id, absences in stats['absences'].items():
                    user_info = users.get(str(user_id), {})
                    name = user_info.get('first_name', 'Неизвестно')
                    writer.writerow([name, user_id, absences])
            else:
                writer.writerow(['Пропусков нет'])

            writer.writerow([])
            writer.writerow(['-' * 30])
            writer.writerow([])

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
            tmp.write(output.getvalue())
            tmp_path = tmp.name

        # Отправляем файл
        await callback.message.answer_document(
            FSInputFile(tmp_path, filename=f"attendance_report_{datetime.now().strftime('%Y%m%d')}.csv"),
            caption="📊 Отчет по посещаемости"
        )

        # Удаляем временный файл
        os.unlink(tmp_path)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при создании отчета: {e}")

    await callback.answer()


@admin_router.callback_query(F.data == "admin_manage")
async def admin_manage(callback: CallbackQuery):
    """Управление кружками"""
    if not await admin_filter(callback):
        return

    text = "📋 *Управление кружками*\n\n"
    text += "Текущая квота мест:\n\n"

    for club_name in CLUB_NAMES:
        stats = await db.get_club_stats(club_name)
        text += f"• *{club_name}*: {stats['total_members']}/{stats['max_seats']} мест занято\n"
        text += f"  Свободно: {stats['max_seats'] - stats['total_members']} мест\n\n"

    text += "🔧 *Функции управления:*\n"
    text += "• Изменение квот - в разработке\n"
    text += "• Добавление кружков - в разработке\n"
    text += "• Удаление кружков - в разработке\n"

    await callback.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()