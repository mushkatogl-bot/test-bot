import telebot
import sqlite3
import os
import time
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# ===== КОНФИГ =====
TOKEN = os.environ.get("BOT_TOKEN", "8922624818:AAEjmrOs1Tr5oQJJYot49wCClVf8rel1FIc")
ADMIN_ID = 6668127953
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
    print("✅ База данных готова")

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
    """Отправляет главное меню с картинкой"""
    image_url = "https://your-image-url.com/welcome.jpg"  # ЗАМЕНИТЕ НА ВАШУ КАРТИНКУ
    try:
        bot.send_photo(
            chat_id,
            image_url,
            caption="🏪 *Добро пожаловать в магазин!*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_buttons()
        )
    except:
        bot.send_message(
            chat_id,
            "🏪 *Добро пожаловать в магазин!*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_buttons()
        )

# ===== КОМАНДЫ ИЗ МЕНЮ TELEGRAM =====
@bot.message_handler(commands=['start'])
def start(message):
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['catalog'])
def catalog_command(message):
    """Обработчик команды /catalog из меню"""
    show_catalog_as_message(message.chat.id)

@bot.message_handler(commands=['profile'])
def profile_command(message):
    """Обработчик команды /profile из меню"""
    show_profile_as_message(message.chat.id, message.from_user.id)

@bot.message_handler(commands=['support'])
def support_command(message):
    """Обработчик команды /support из меню"""
    show_support_as_message(message.chat.id)

# ===== ФУНКЦИИ ДЛЯ ОТПРАВКИ НОВЫХ СООБЩЕНИЙ =====
def show_catalog_as_message(chat_id):
    """Отправляет каталог как НОВОЕ сообщение"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE status = 'available'")
    accounts = cursor.fetchall()
    conn.close()

    if not accounts:
        bot.send_message(
            chat_id,
            "😕 Аккаунтов в наличии нет. Зайдите позже!"
        )
        return

    text = "📋 *Доступные аккаунты:*\n\n"
    markup = InlineKeyboardMarkup(row_width=1)
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
        markup.add(InlineKeyboardButton(
            f"🛒 {acc[1]} - {acc[5]} USD",
            callback_data=f"buy_{acc[0]}"
        ))
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

def show_profile_as_message(chat_id, user_id):
    """Отправляет профиль как НОВОЕ сообщение"""
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

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

def show_support_as_message(chat_id):
    """Отправляет поддержку как НОВОЕ сообщение"""
    text = "🆘 *Поддержка*\n\n"
    text += "Если у вас возникли вопросы, напишите нам:\n"
    text += "✉️ @your_support_username\n"
    text += "\nМы ответим в течение 24 часов."

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== КНОПКИ (CALLBACK) =====
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
    markup = InlineKeyboardMarkup(row_width=1)
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

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    text = "🆘 *Поддержка*\n\n"
    text += "Если у вас возникли вопросы, напишите нам:\n"
    text += "✉️ @your_support_username\n"
    text += "\nМы ответим в течение 24 часов."

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

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

    reserved_until = datetime.now() + timedelta(minutes=10)
    cursor.execute("UPDATE accounts SET status = 'reserved', reserved_by = ?, reserved_until = ? WHERE id = ?",
                   (user_id, reserved_until, account_id))
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

# ===== ОПЛАТА (ЗАГЛУШКА) =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_xrocket_"))
def pay_xrocket(call):
    account_id = int(call.data.split("_")[2])

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

# ===== АДМИН-ПАНЕЛЬ =====
admin_temp = {}

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет доступа!")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Добавить аккаунт", callback_data="admin_add"),
        InlineKeyboardButton("📋 Список аккаунтов", callback_data="admin_list"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )
    bot.send_message(
        message.chat.id,
        "🔐 *Админ-панель*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add")
def admin_add_start(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа!", show_alert=True)
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel"))

    msg = bot.send_message(
        call.message.chat.id,
        "📝 *Добавление нового аккаунта*\n\n"
        "Отправьте данные в формате:\n\n"
        "```\n"
        "Название: Аккаунт #1\n"
        "Дата регистрации: 2024-01-15\n"
        "Топ: да\n"
        "Прогрев: нет\n"
        "Цена: 10\n"
        "Количество: 1\n"
        "```\n\n"
        "После этого отправьте файл с куки.",
        parse_mode="Markdown",
        reply_markup=markup
    )

    admin_temp[call.from_user.id] = {'step': 'waiting_data', 'data': {}}
    bot.register_next_step_handler(msg, admin_process_data)

def admin_process_data(message):
    user_id = message.from_user.id

    if user_id not in admin_temp:
        return

    if message.text == "❌ Отмена":
        admin_temp.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Добавление отменено.")
        return

    try:
        lines = message.text.strip().split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'название':
                    data['name'] = value
                elif key == 'дата регистрации':
                    data['register_date'] = value
                elif key == 'топ':
                    data['is_top'] = 1 if value.lower() in ['да', 'yes', 'true', '1'] else 0
                elif key == 'прогрев':
                    data['has_product'] = 1 if value.lower() in ['да', 'yes', 'true', '1'] else 0
                elif key == 'цена':
                    data['price'] = float(value)
                elif key == 'количество':
                    data['quantity'] = int(value)

        if 'name' not in data or 'price' not in data:
            raise ValueError("Не хватает обязательных полей (Название, Цена)")

        admin_temp[user_id]['data'] = data
        admin_temp[user_id]['step'] = 'waiting_file'

        bot.send_message(
            message.chat.id,
            f"✅ Данные приняты:\n\n"
            f"📌 Название: {data.get('name')}\n"
            f"📅 Дата регистрации: {data.get('register_date', 'не указана')}\n"
            f"⭐ Топ: {'Да' if data.get('is_top') else 'Нет'}\n"
            f"📦 Прогрев: {'Да' if data.get('has_product') else 'Нет'}\n"
            f"💰 Цена: {data.get('price')} USD\n"
            f"📦 Количество: {data.get('quantity', 1)}\n\n"
            "📤 Теперь отправьте файл с куки (TXT, JSON или DAT)."
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка: {e}\n\n"
            "Попробуйте снова. Формат:\n"
            "Название: Аккаунт #1\n"
            "Цена: 10"
        )
        bot.register_next_step_handler(message, admin_process_data)

@bot.message_handler(content_types=['document'])
def admin_process_file(message):
    user_id = message.from_user.id

    if user_id not in admin_temp or admin_temp[user_id].get('step') != 'waiting_file':
        return

    if message.document:
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name

        os.makedirs('storage/accounts', exist_ok=True)
        file_path = f"storage/accounts/{file_name}"

        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        data = admin_temp[user_id]['data']
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (name, register_date, is_top, has_product, price, quantity, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data.get('register_date', ''),
            data.get('is_top', 0),
            data.get('has_product', 0),
            data['price'],
            data.get('quantity', 1),
            file_path
        ))
        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ Аккаунт *{data['name']}* успешно добавлен!\n"
            f"📁 Файл: {file_name}\n"
            f"💰 Цена: {data['price']} USD",
            parse_mode="Markdown"
        )

        admin_temp.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data == "admin_cancel")
def admin_cancel(call):
    admin_temp.pop(call.from_user.id, None)
    bot.edit_message_text(
        "❌ Добавление отменено.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def admin_list(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа!", show_alert=True)
        return

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, status, quantity FROM accounts")
    accounts = cursor.fetchall()
    conn.close()

    if not accounts:
        text = "📋 *Список аккаунтов*\n\nАккаунтов пока нет."
    else:
        text = "📋 *Список аккаунтов*\n\n"
        for acc in accounts:
            status_emoji = {
                'available': '✅',
                'reserved': '⏳',
                'sold': '❌'
            }.get(acc[3], '❓')
            text += f"{status_emoji} ID: {acc[0]} | {acc[1]} | {acc[4]} шт. | {acc[2]} USD\n"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 В админ-панель", callback_data="admin_back"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа!", show_alert=True)
        return

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'")
    available = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'sold'")
    sold = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
    orders = cursor.fetchone()[0]
    conn.close()

    text = f"📊 *Статистика*\n\n"
    text += f"📦 Доступно: {available}\n"
    text += f"✅ Продано: {sold}\n"
    text += f"📋 Всего заказов: {orders}"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 В админ-панель", callback_data="admin_back"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if call.from_user.id != ADMIN_ID:
        return
    admin_panel(call.message)

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
    init_db()
    print("✅ База данных готова")

    polling_thread = threading.Thread(target=run_polling)
    polling_thread.daemon = True
    polling_thread.start()

    port = int(os.environ.get("PORT", 10000))
    print(f"🔥 Запускаем Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)