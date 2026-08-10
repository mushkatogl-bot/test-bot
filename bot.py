import telebot
import sqlite3
import os
import time
import threading
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# ===== КОНФИГ =====
TOKEN = os.environ.get("BOT_TOKEN", "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc")
bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            register_date TEXT,
            is_top BOOLEAN DEFAULT 0,
            has_product BOOLEAN DEFAULT 0,
            price REAL NOT NULL,
            quantity INTEGER DEFAULT 1,
            file_path TEXT,
            status TEXT DEFAULT 'available',
            reserved_by INTEGER,
            reserved_until TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ===== МЕНЮ В СТРОКЕ ВВОДА =====
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("🚀 Старт"))
    return markup

# ===== ГЛАВНОЕ МЕНЮ (КАРТИНКА + 3 КНОПКИ) =====
def get_main_buttons():
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("📋 Каталог", callback_data="catalog"),
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("🆘 Поддержка", callback_data="support")
    )
    return markup

def show_main_menu(chat_id):
    image_url = "https://your-image-url.com/welcome.jpg"  # Замените на свою картинку
    try:
        bot.send_photo(
            chat_id,
            image_url,
            caption="🏪 *Добро пожаловать в магазин!*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_buttons()
        )
    except:
        # Если картинка не загружается, отправляем текст
        bot.send_message(
            chat_id,
            "🏪 *Добро пожаловать в магазин!*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_buttons()
        )

# ===== КОМАНДЫ ИЗ МЕНЮ TELEGRAM =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в магазин аккаунтов!",
        reply_markup=get_main_menu()
    )
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['catalog'])
def catalog_command(message):
    """Обработчик команды /catalog из меню"""
    # Создаём имитацию callback для переиспользования кода
    class FakeCall:
        def __init__(self, msg):
            self.message = msg
            self.data = "catalog"
            self.from_user = msg.from_user
            self.id = None
    fake_call = FakeCall(message)
    show_catalog(fake_call)

@bot.message_handler(commands=['profile'])
def profile_command(message):
    """Обработчик команды /profile из меню"""
    class FakeCall:
        def __init__(self, msg):
            self.message = msg
            self.data = "profile"
            self.from_user = msg.from_user
            self.id = None
    fake_call = FakeCall(message)
    profile(fake_call)

@bot.message_handler(commands=['support'])
def support_command(message):
    """Обработчик команды /support из меню"""
    class FakeCall:
        def __init__(self, msg):
            self.message = msg
            self.data = "support"
            self.from_user = msg.from_user
            self.id = None
    fake_call = FakeCall(message)
    support(fake_call)

@bot.message_handler(func=lambda message: message.text == "🚀 Старт")
def start_button(message):
    show_main_menu(message.chat.id)

# ===== КАТАЛОГ =====
@bot.callback_query_handler(func=lambda call: call.data == "catalog")
def show_catalog(call):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE status = 'available'")
    accounts = cursor.fetchall()
    conn.close()

    if not accounts:
        bot.edit_message_text(
            "😕 Аккаунтов в наличии нет. Зайдите позже!",
            call.message.chat.id,
            call.message.message_id
        )
        return

    text = "📋 *Доступные аккаунты:*\n\n"
    for acc in accounts:
        text += f"🔹 *{acc[1]}*\n"
        text += f"   📅 Регистрация: {acc[2]}\n"
        if acc[3]:
            text += f"   ⭐ Топ аккаунт\n"
        if acc[4]:
            text += f"   📦 Прогрев товара\n"
        text += f"   📦 Доступно: {acc[6]}\n"
        text += f"   💰 Цена: {acc[5]} USD\n"
        text += f"   🆔 ID: {acc[0]}\n\n"

    markup = InlineKeyboardMarkup(row_width=1)
    for acc in accounts:
        markup.add(InlineKeyboardButton(
            f"🛒 {acc[1]} - {acc[5]} USD",
            callback_data=f"buy_{acc[0]}"
        ))
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== ПРОФИЛЬ =====
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = 'completed'", (user_id,))
    orders_count = cursor.fetchone()[0]
    conn.close()

    text = f"👤 *Ваш профиль*\n\n"
    text += f"🆔 ID: {user_id}\n"
    text += f"📦 Покупок: {orders_count}\n"
    text += f"\nСпасибо, что выбираете нас!"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

# ===== ПОДДЕРЖКА =====
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    text = "🆘 *Поддержка*\n\n"
    text += "Если у вас возникли вопросы, напишите нам:\n"
    text += "✉️ @your_support_username\n"
    text += "\nМы ответим в течение 24 часов."

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

# ===== В МЕНЮ =====
@bot.callback_query_handler(func=lambda call: call.data == "menu")
def back_to_menu(call):
    show_main_menu(call.message.chat.id)

# ===== ПОКУПКА =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def start_purchase(call):
    account_id = int(call.data.split("_")[1])
    user_id = call.from_user.id

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ? AND status = 'available'", (account_id,))
    account = cursor.fetchone()

    if not account:
        bot.answer_callback_query(call.id, "❌ Аккаунт уже продан!", show_alert=True)
        conn.close()
        return

    # Бронируем на 10 минут
    reserved_until = datetime.now() + timedelta(minutes=10)
    cursor.execute("UPDATE accounts SET status = 'reserved', reserved_by = ?, reserved_until = ? WHERE id = ?",
                   (user_id, reserved_until, account_id))

    # Создаём заказ
    cursor.execute("INSERT INTO orders (user_id, product_id) VALUES (?, ?)", (user_id, account_id))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    text = f"""📦 *Оформление заказа*

*Аккаунт:* {account[1]}
📅 Регистрация: {account[2]}
{'⭐ Топ аккаунт' if account[3] else ''}
{'📦 Прогрев товара' if account[4] else ''}
💰 *Цена: {account[5]} USD*

⏰ Аккаунт забронирован до *{(datetime.now() + timedelta(minutes=10)).strftime('%H:%M')}*

Выберите способ оплаты:"""

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💳 X-Rocket", callback_data=f"pay_xrocket_{account_id}"),
        InlineKeyboardButton("🤖 Криптобот", callback_data=f"pay_cryptobot_{account_id}")
    )
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="catalog"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== ОПЛАТА (заглушка) =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_xrocket_"))
def pay_xrocket(call):
    account_id = int(call.data.split("_")[2])
    user_id = call.from_user.id

    text = f"""💳 *Оплата через X-Rocket*

Сумма: 10 USD (пример)

🔗 Ссылка на оплату будет здесь.

После оплаты нажмите кнопку ниже:"""

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_{account_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data="menu")
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_cryptobot_"))
def pay_cryptobot(call):
    account_id = int(call.data.split("_")[2])
    user_id = call.from_user.id

    text = f"""🤖 *Оплата через Криптобот*

Сумма: 10 USD (пример)

Инструкция по оплате будет здесь.

После оплаты нажмите кнопку ниже:"""

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_{account_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data="menu")
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== ПРОВЕРКА ОПЛАТЫ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_payment(call):
    account_id = int(call.data.split("_")[1])

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        file_path = result[0]
        try:
            with open(file_path, 'rb') as f:
                bot.send_document(call.message.chat.id, f, caption="✅ Оплата получена! Ваш файл с куки:")
            bot.edit_message_text(
                "✅ Оплата подтверждена! Файл отправлен.",
                call.message.chat.id,
                call.message.message_id
            )
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "❌ Файл не найден. Обратитесь в поддержку.", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "⏳ Оплата ещё не получена. Попробуйте позже.", show_alert=True)

# ===== ЗАПУСК БОТА И FLASK =====
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает на Render!"

def run_polling():
    print("🚀 Запускаем polling в фоновом потоке...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Ошибка в polling: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    print("✅ База данных готова")

    # Запускаем polling в отдельном потоке
    polling_thread = threading.Thread(target=run_polling)
    polling_thread.daemon = True
    polling_thread.start()

    # Запускаем Flask
    port = int(os.environ.get("PORT", 10000))
    print(f"🔥 Запускаем Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)