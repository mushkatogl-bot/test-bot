import asyncio
import random
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from sqlalchemy.orm import Session

from loader import dp, bot
from database import User, Account, Order, get_db
from keyboards import (
    get_main_keyboard, get_payment_keyboard,
    get_order_history_keyboard, get_back_to_catalog_keyboard
)
from payments import crypto_bot, xrocket
from config import SUPPORT_LINK, GUARANTEE_TEXT
from utils import generate_order_id, format_order_history


# ==================== Команда /start ====================
@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # Регистрация пользователя
    with next(get_db()) as db:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            db.add(user)
            db.commit()

    # Отправка приветствия с картинкой
    # Временно - текст, позже добавим картинку
    await message.answer(
        "👋 Добро пожаловать в магазин аккаунтов!\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_keyboard()
    )


# ==================== Профиль ====================
@dp.message_handler(lambda message: message.text == "📱 Профиль")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id

    with next(get_db()) as db:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        profile_text = f"""
👤 *Ваш профиль*

🆔 ID: `{user.telegram_id}`
👤 Имя: {user.first_name or "Не указано"}
📝 Username: @{user.username or "Не указан"}
📦 Всего заказов: {user.total_orders}
💰 Потрачено: {user.total_spent:.2f} $
📅 Зарегистрирован: {user.registered_at.strftime('%d.%m.%Y')}
        """

        await message.answer(
            profile_text,
            parse_mode="Markdown",
            reply_markup=get_order_history_keyboard()
        )


# ==================== История заказов ====================
@dp.callback_query_handler(lambda c: c.data == "order_history")
async def order_history_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    with next(get_db()) as db:
        orders = db.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

        if not orders:
            await callback.message.edit_text("📭 У вас пока нет заказов.")
            return

        response = f"📋 *История заказов*\n\nВсего заказов: {len(orders)}\n"
        response += "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"

        for order in orders[:10]:  # Показываем последние 10
            response += f"""
💡 Заказ #{order.order_id}
🕐 Время: {order.created_at.strftime('%Y-%m-%d %H:%M')}
🕐 Статус: {order.status}
💰 Сумма: {order.amount:.2f} $
💰 Способ: {order.payment_method}
➖➖➖➖➖➖➖➖➖➖➖➖\n
            """

        await callback.message.edit_text(response, parse_mode="Markdown")


# ==================== Каталог ====================
@dp.message_handler(lambda message: message.text == "📦 Каталог")
async def catalog_handler(message: types.Message):
    with next(get_db()) as db:
        accounts = db.query(Account).filter_by(is_sold=False).all()

        if not accounts:
            await message.answer("😔 К сожалению, аккаунтов в наличии нет.")
            return

        # Создаем инлайн-кнопки для каждого аккаунта
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for account in accounts:
            button_text = f"📅 {account.registration_date} | {account.nickname or 'Без ника'}"
            if account.is_top:
                button_text += " ⭐ ТОП"
            keyboard.add(
                types.InlineKeyboardButton(button_text, callback_data=f"account_{account.id}")
            )

        await message.answer(
            "📦 *Доступные аккаунты:*\n\nВыберите аккаунт для просмотра:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# ==================== Детали аккаунта ====================
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("account_"))
async def account_detail_handler(callback: types.CallbackQuery):
    account_id = int(callback.data.split("_")[1])

    with next(get_db()) as db:
        account = db.query(Account).filter_by(id=account_id, is_sold=False).first()
        if not account:
            await callback.message.edit_text("❌ Аккаунт уже продан или не найден.")
            return

        detail_text = f"""
📱 *Информация об аккаунте*

📅 Дата регистрации: {account.registration_date}
🔢 Тип номера: {account.number_type}
👤 Никнейм: {account.nickname or "Отсутствует"}
🎮 Наличие игры: {"✅ Есть" if account.has_game else "❌ Нет"}
⭐ ТОП: {"✅ Да" if account.is_top else "❌ Нет"}
💰 Цена: {account.price:.2f} $

{GUARANTEE_TEXT}
        """

        keyboard = get_payment_keyboard(account_id, account.price)
        await callback.message.edit_text(
            detail_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# ==================== Обработка платежей ====================
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("pay_"))
async def payment_handler(callback: types.CallbackQuery):
    action, method, account_id = callback.data.split("_")
    account_id = int(account_id)
    user_id = callback.from_user.id

    with next(get_db()) as db:
        account = db.query(Account).filter_by(id=account_id, is_sold=False).first()
        if not account:
            await callback.message.edit_text("❌ Аккаунт уже продан.")
            return

        # Создаем инвойс
        if method == "crypto":
            invoice = await crypto_bot.create_invoice(
                amount=account.price,
                comment=f"Покупка аккаунта #{account_id}"
            )
            payment_method = "CryptoBot"
        elif method == "xrocket":
            invoice = await xrocket.create_invoice(
                amount=account.price,
                comment=f"Покупка аккаунта #{account_id}"
            )
            payment_method = "xRocket"
        else:
            await callback.answer("❌ Неизвестный способ оплаты")
            return

        if not invoice:
            await callback.message.edit_text(
                "❌ Ошибка при создании счета. Попробуйте позже."
            )
            return

        # Сохраняем заказ в БД
        order_id = generate_order_id()
        order = Order(
            order_id=order_id,
            user_id=user_id,
            account_id=account_id,
            status="Ожидает оплаты",
            amount=account.price,
            payment_method=payment_method,
            payment_id=str(invoice["invoice_id"])
        )
        db.add(order)
        db.commit()

        # Отправляем ссылку на оплату
        await callback.message.edit_text(
            f"💳 *Счет на оплату создан!*\n\n"
            f"Заказ #{order_id}\n"
            f"Сумма: {account.price:.2f} $\n"
            f"Способ: {payment_method}\n\n"
            f"🔗 [Перейти к оплате]({invoice['pay_url']})\n\n"
            f"⏳ Счет действителен 1 час.\n"
            f"После оплаты аккаунт будет выдан автоматически.",
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_back_to_catalog_keyboard()
        )


# ==================== Поддержка ====================
@dp.message_handler(lambda message: message.text == "🆘 Поддержка")
async def support_handler(message: types.Message):
    support_text = f"""
🆘 *Поддержка*

Если у вас возникли вопросы или проблемы, вы можете обратиться к нам:

👤 Администратор: {SUPPORT_LINK}

⏰ Время ответа: обычно в течение 15-30 минут

💬 Пожалуйста, описывайте проблему максимально подробно и прикладывайте скриншоты.
    """

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📩 Написать поддержке", url=SUPPORT_LINK))

    await message.answer(support_text, parse_mode="Markdown", reply_markup=keyboard)


# ==================== Возврат в каталог ====================
@dp.callback_query_handler(lambda c: c.data == "back_to_catalog")
async def back_to_catalog_handler(callback: types.CallbackQuery):
    await catalog_handler(callback.message)