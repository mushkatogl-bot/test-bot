import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN
from database import init_db
from handlers import user, admin
from keyboards import get_main_keyboard

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# Регистрация обработчиков (они импортируются через handlers)
# Обработчики автоматически регистрируются через декораторы

# ==================== Настройка команд ====================
async def set_commands(dp: Dispatcher):
    """Установка команд бота в меню"""
    await dp.bot.set_my_commands([
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("admin", "👑 Админ-панель")  # Только для админов
    ])


# ==================== Обработчик неизвестных команд ====================
@dp.message_handler(Command(commands=['admin']))
async def admin_command(message: types.Message):
    """Перенаправляем команду admin в админ-обработчик"""
    from handlers.admin import cmd_admin
    await cmd_admin(message)


@dp.message_handler()
async def unknown_message(message: types.Message):
    """Обработчик для неизвестных сообщений"""
    # Игнорируем, если есть обработчики для конкретных текстов
    pass


# ==================== Запуск бота ====================
async def main():
    # Инициализация базы данных
    init_db()
    logger.info("✅ База данных инициализирована")

    # Установка команд
    await set_commands(dp)
    logger.info("✅ Команды установлены")

    # Запуск поллинга
    logger.info("🚀 Бот запущен!")
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())