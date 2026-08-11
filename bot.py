import asyncio
import logging
from aiogram.types import BotCommand

from config import BOT_TOKEN
from loader import dp, bot
from handlers import user, admin  # Импортируем обработчики для их регистрации

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Установка команд бота
async def set_commands(dp: Dispatcher):
    await dp.bot.set_my_commands([
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("admin", "👑 Админ-панель")
    ])

# Запуск бота
async def main():
    await set_commands(dp)
    logger.info("🚀 Бот запущен!")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())