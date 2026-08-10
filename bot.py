import telebot
import os
import time
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN", "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== КОМАНДЫ БОТА =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Бот работает на Render через вебхук!")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Вы написали: {message.text}")

# ===== ВЕБХУК =====
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        if update:
            bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Bad Request", 400

@app.route('/')
def index():
    return "Бот работает на Render!"

# ===== ЗАПУСК =====
if __name__ == '__main__':
    # Порт, который ждёт Render (по умолчанию 10000)
    port = int(os.environ.get("PORT", 10000))
    
    # Устанавливаем вебхук
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{TOKEN}"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=webhook_url)
    print(f"✅ Вебхук установлен на {webhook_url}")
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=port)