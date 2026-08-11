import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

print(f"🔑 Токен: {BOT_TOKEN[:10]}...")  # Покажет первые 10 символов

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())