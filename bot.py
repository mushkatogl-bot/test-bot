import telebot
import time

TOKEN = "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc"
bot = telebot.TeleBot(TOKEN)

# === УДАЛЯЕМ ВЕБХУК ===
print("Удаляю старый вебхук...")
bot.remove_webhook()
time.sleep(2)
print("Вебхук удалён!")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Бот работает!"
    )

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Вы написали: {message.text}")

if __name__ == '__main__':
    print("Бот запущен!")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)