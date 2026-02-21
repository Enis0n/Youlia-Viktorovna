import csv
import io
from datetime import datetime
from typing import List, Dict
from database import db


async def generate_attendance_report(club_name: str) -> io.BytesIO:
    """Генерирует отчет о посещаемости в формате CSV"""
    stats = await db.get_club_stats(club_name)

    output = io.BytesIO()
    writer = csv.writer(output)

    # Заголовок
    writer.writerow(['Отчет по посещаемости', club_name])
    writer.writerow(['Дата создания:', datetime.now().strftime('%Y-%m-%d %H:%M')])
    writer.writerow([])

    # Общая статистика
    writer.writerow(['Общая статистика:'])
    writer.writerow(['Всего участников:', stats['total_members']])
    writer.writerow(['Максимум мест:', stats['max_seats']])
    writer.writerow([])

    # Список участников с пропусками
    writer.writerow(['Список участников с пропусками:'])
    writer.writerow(['ID пользователя', 'Количество пропусков'])

    for user_id, absences in stats['absences'].items():
        writer.writerow([user_id, absences])

    output.seek(0)
    return output


def format_club_info(club_name: str, members_count: int, max_seats: int) -> str:
    """Форматирует информацию о кружке"""
    return f"""
🏫 *{club_name}*

👥 Участников: {members_count}/{max_seats}
📊 Свободных мест: {max_seats - members_count}
    """


def format_user_info(user_data: Dict) -> str:
    """Форматирует информацию о пользователе"""
    name_parts = [user_data.get('first_name', '')]
    if user_data.get('last_name'):
        name_parts.append(user_data['last_name'])

    return f"""
👤 *Информация о пользователе*

Имя: {' '.join(name_parts)}
Username: @{user_data.get('username', 'отсутствует')}
Зарегистрирован: {user_data.get('registered_at', 'неизвестно')[:10]}
    """