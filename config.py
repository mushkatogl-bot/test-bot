import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# CryptoBot
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")

# xRocket
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
XROCKET_WEBHOOK_URL = os.getenv("XROCKET_WEBHOOK_URL")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# Константы
SUPPORT_LINK = "https://t.me/HeisenbergBr35"
GUARANTEE_TEXT = """
⚠️ *Важно!*

📹 Перед подтверждением покупки обязательно запишите видео процесса получения аккаунта.

⏱️ Гарантия действует 30 минут после покупки *ТОЛЬКО* при наличии видео.
❌ Без видео - замена *НЕ* производится.

✅ Заменим аккаунт только в случае его невалидности.
❗ Баны, блокировки и проблемы с заливом - *НЕ* являются причиной для замены.

🔍 Проверяйте аккаунт сразу после получения!
"""