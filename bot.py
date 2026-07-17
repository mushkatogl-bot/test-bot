import telebot
import time

TOKEN = "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc"
bot = telebot.TeleBot(TOKEN)

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
        except:
            time.sleep(5)