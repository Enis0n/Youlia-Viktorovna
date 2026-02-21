import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from handlers import router
from admin_handlers import admin_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота...")

    # Проверка наличия токена
    if not BOT_TOKEN:
        logger.error("Не указан BOT_TOKEN в файле .env")
        return

    # Передаем ADMIN_IDS в базу данных
    db.admin_ids = ADMIN_IDS
    logger.info(f"Загружены администраторы: {ADMIN_IDS}")

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем роутеры
    dp.include_router(router)
    dp.include_router(admin_router)

    try:
        # Пропускаем накопившиеся обновления и запускаем бота
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот успешно запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")