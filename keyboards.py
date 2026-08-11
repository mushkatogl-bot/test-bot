from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Главное меню пользователя"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📱 Профиль"),
        KeyboardButton("📦 Каталог"),
        KeyboardButton("🆘 Поддержка")
    )
    return keyboard

def get_admin_keyboard():
    """Главное меню админа"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("➕ Загрузить аккаунты"),
        KeyboardButton("📊 Статистика"),
        KeyboardButton("👥 Все пользователи"),
        KeyboardButton("📦 Управление аккаунтами"),
        KeyboardButton("🔙 В главное меню")
    )
    return keyboard

def get_cancel_keyboard():
    """Кнопка отмены"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("❌ Отмена"))
    return keyboard

def get_payment_keyboard(account_id: int, amount: float):
    """Кнопки оплаты для аккаунта"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💰 CryptoBot", callback_data=f"pay_crypto_{account_id}"),
        InlineKeyboardButton("💰 xRocket", callback_data=f"pay_xrocket_{account_id}")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад в каталог", callback_data="back_to_catalog"))
    return keyboard

def get_order_history_keyboard():
    """Кнопка для истории заказов"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 История заказов", callback_data="order_history"))
    return keyboard

def get_back_to_catalog_keyboard():
    """Кнопка возврата в каталог"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад в каталог", callback_data="back_to_catalog"))
    return keyboard