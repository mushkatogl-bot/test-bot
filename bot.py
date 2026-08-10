import telebot
import os
import time
import threading
from flask import Flask, request

# --- КОНФИГ ---
TOKEN = os.environ.get("BOT_TOKEN", "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- КОМАНДЫ БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Бот работает на Render через polling + Flask!")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Вы написали: {message.text}")

# --- ФУНКЦИЯ ДЛЯ ЗАПУСКА ПОЛЛИНГА В ОТДЕЛЬНОМ ПОТОКЕ ---
def run_polling():
    print("🚀 Запускаем polling в фоновом потоке...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Ошибка в polling: {e}")
            time.sleep(5)

# --- ВЕБ-ЭНДПОИНТЫ (нужны для Render) ---
@app.route('/')
def index():
    return "✅ Бот работает на Render!"

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Запускаем polling в отдельном потоке
    polling_thread = threading.Thread(target=run_polling)
    polling_thread.daemon = True  # Поток завершится, когда завершится основной
    polling_thread.start()
    
    # Запускаем Flask (основной поток)
    port = int(os.environ.get("PORT", 10000))
    print(f"🔥 Запускаем Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)