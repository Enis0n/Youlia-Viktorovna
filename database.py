import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, filename: str = 'data.json', admin_ids=None):
        self.filename = filename
        self.admin_ids = admin_ids or []  # Сохраняем admin_ids в объекте
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Создает файл базы данных, если его нет"""
        if not os.path.exists(self.filename):
            initial_data = {
                'users': {},
                'clubs': {},
                'attendance': {}
            }
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Создан файл базы данных: {self.filename}")
            except Exception as e:
                logger.error(f"Ошибка при создании файла БД: {e}")

    def _read_data_sync(self) -> Dict:
        """Синхронное чтение данных"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при чтении БД: {e}")
            return {'users': {}, 'clubs': {}, 'attendance': {}}

    def _write_data_sync(self, data: Dict):
        """Синхронная запись данных"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при записи в БД: {e}")

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = '') -> bool:
        """Добавляет или обновляет пользователя"""
        data = self._read_data_sync()

        user_id_str = str(user_id)
        is_new = user_id_str not in data['users']

        # Проверяем, является ли пользователь администратором
        is_admin = False
        if self.admin_ids and user_id in self.admin_ids:
            is_admin = True

        data['users'][user_id_str] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'registered_at': datetime.now().isoformat(),
            'is_admin': is_admin
        }

        self._write_data_sync(data)
        return is_new

    async def register_for_club(self, user_id: int, club_name: str) -> Tuple[bool, str]:
        """Регистрирует пользователя на кружок"""
        data = self._read_data_sync()
        user_id_str = str(user_id)

        # Инициализируем кружок, если его нет
        if club_name not in data['clubs']:
            from config import MAX_CLUB_SEATS
            data['clubs'][club_name] = {
                'members': [],
                'max_seats': MAX_CLUB_SEATS.get(club_name, 10)
            }

        # Проверяем, не зарегистрирован ли уже пользователь
        if user_id_str in data['clubs'][club_name]['members']:
            return False, f"Вы уже записаны на кружок '{club_name}'"

        # Проверяем количество мест
        current_members = len(data['clubs'][club_name]['members'])
        max_seats = data['clubs'][club_name]['max_seats']

        if current_members >= max_seats:
            return False, f"❌ Извините, на кружок '{club_name}' больше нет мест (максимум {max_seats})"

        # Регистрируем пользователя
        data['clubs'][club_name]['members'].append(user_id_str)
        self._write_data_sync(data)

        remaining = max_seats - (current_members + 1)
        return True, f"✅ Вы успешно записаны на кружок '{club_name}'. Осталось мест: {remaining}"

    async def get_user_clubs(self, user_id: int) -> List[str]:
        """Возвращает список кружков пользователя"""
        data = self._read_data_sync()
        user_id_str = str(user_id)
        user_clubs = []

        for club_name, club_data in data['clubs'].items():
            if user_id_str in club_data.get('members', []):
                user_clubs.append(club_name)

        return user_clubs

    async def get_club_members(self, club_name: str) -> List[str]:
        """Возвращает список участников кружка"""
        data = self._read_data_sync()
        return data['clubs'].get(club_name, {}).get('members', [])

    async def get_club_stats(self, club_name: str) -> Dict:
        """Возвращает статистику по кружку"""
        data = self._read_data_sync()
        from config import MAX_CLUB_SEATS
        club_data = data['clubs'].get(club_name, {'members': [], 'max_seats': MAX_CLUB_SEATS.get(club_name, 10)})
        members = club_data.get('members', [])

        # Считаем пропуски
        absences = {}
        if 'attendance' in data and club_name in data['attendance']:
            for date, records in data['attendance'][club_name].items():
                for absent_id in records.get('absent', []):
                    absences[absent_id] = absences.get(absent_id, 0) + 1

        return {
            'total_members': len(members),
            'max_seats': club_data.get('max_seats', MAX_CLUB_SEATS.get(club_name, 10)),
            'members': members,
            'absences': absences
        }

    async def cancel_registration(self, user_id: int, club_name: str) -> bool:
        """Отменяет регистрацию пользователя"""
        data = self._read_data_sync()
        user_id_str = str(user_id)

        if club_name in data['clubs'] and user_id_str in data['clubs'][club_name]['members']:
            data['clubs'][club_name]['members'].remove(user_id_str)
            self._write_data_sync(data)
            return True

        return False

    async def mark_attendance(self, club_name: str, date: str, present_users: List[int], absent_users: List[int]):
        """Отмечает посещаемость"""
        data = self._read_data_sync()

        if 'attendance' not in data:
            data['attendance'] = {}

        if club_name not in data['attendance']:
            data['attendance'][club_name] = {}

        data['attendance'][club_name][date] = {
            'present': present_users,
            'absent': absent_users
        }

        self._write_data_sync(data)

    async def get_all_users(self) -> Dict:
        """Возвращает всех пользователей"""
        data = self._read_data_sync()
        return data.get('users', {})


# Создаем глобальный экземпляр БД без admin_ids
db = Database()