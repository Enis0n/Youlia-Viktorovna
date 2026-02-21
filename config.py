import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в файле .env")
    print("❌ ОШИБКА: BOT_TOKEN не найден! Проверьте файл .env")

# Получаем ID администраторов
admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
logger.info(f"Загружены администраторы: {ADMIN_IDS}")

# Максимальное количество мест в кружках
MAX_CLUB_SEATS = {
    'Футбол': 15,
    'Рисование': 10,
    'Робототехника': 8,
    'Музыка': 12,
    'Шахматы': 10
}

# Описания кружков
CLUB_DESCRIPTIONS = {
    'Футбол': '⚽ Спортивная секция для мальчиков и девочек',
    'Рисование': '🎨 Художественный кружок',
    'Робототехника': '🤖 Создание и программирование роботов',
    'Музыка': '🎵 Вокальная студия',
    'Шахматы': '♟ Развитие логического мышления'
}

CLUB_NAMES = list(MAX_CLUB_SEATS.keys())