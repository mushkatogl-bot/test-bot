from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime

from config import CRYPTOBOT_TOKEN, XROCKET_TOKEN
from database import get_db, Order, Account, User
from payments import xrocket
from bot import bot

app = Flask(__name__)
logger = logging.getLogger(__name__)


# ==================== Webhook для CryptoBot ====================
@app.route('/cryptobot-webhook', methods=['POST'])
def cryptobot_webhook():
    """Обработка вебхуков от CryptoBot"""
    try:
        data = request.json
        logger.info(f"CryptoBot webhook: {data}")

        # Проверка, что это оплата
        if data.get('update_type') == 'invoice_paid':
            invoice_id = data['payload']['invoice_id']
            order_id = data['payload']['order_id']  # Мы передаем наш order_id

            # Обновляем заказ в БД
            with next(get_db()) as db:
                order = db.query(Order).filter_by(order_id=order_id).first()
                if order and order.status == 'Ожидает оплаты':
                    order.status = 'Оплачен'
                    order.payment_id = str(invoice_id)

                    # Обновляем пользователя
                    user = db.query(User).filter_by(telegram_id=order.user_id).first()
                    if user:
                        user.total_orders += 1
                        user.total_spent += order.amount

                    # Помечаем аккаунт как проданный
                    account = db.query(Account).filter_by(id=order.account_id).first()
                    if account:
                        account.is_sold = True
                        account.sold_to = order.user_id
                        account.sold_at = datetime.utcnow()

                    db.commit()

                    # Отправляем аккаунт пользователю
                    await send_account_to_user(order.user_id, account)

        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"CryptoBot webhook error: {e}")
        return jsonify({"ok": False}), 500


# ==================== Webhook для xRocket ====================
@app.route('/xrocket-webhook', methods=['POST'])
def xrocket_webhook():
    """Обработка вебхуков от xRocket"""
    try:
        # Проверка подписи
        signature = request.headers.get('Rocket-Pay-Signature')
        if not signature:
            return jsonify({"error": "Missing signature"}), 400

        body = request.get_data()
        if not xrocket.verify_webhook_signature(body, signature, XROCKET_TOKEN):
            return jsonify({"error": "Invalid signature"}), 401

        data = request.json
        logger.info(f"xRocket webhook: {data}")

        # Обработка оплаты
        if data.get('event') == 'invoice_paid':
            invoice_id = data['data']['id']

            # Обновляем заказ в БД
            with next(get_db()) as db:
                order = db.query(Order).filter_by(payment_id=str(invoice_id)).first()
                if order and order.status == 'Ожидает оплаты':
                    order.status = 'Оплачен'

                    # Обновляем пользователя
                    user = db.query(User).filter_by(telegram_id=order.user_id).first()
                    if user:
                        user.total_orders += 1
                        user.total_spent += order.amount

                    # Помечаем аккаунт как проданный
                    account = db.query(Account).filter_by(id=order.account_id).first()
                    if account:
                        account.is_sold = True
                        account.sold_to = order.user_id
                        account.sold_at = datetime.utcnow()

                    db.commit()

                    # Отправляем аккаунт пользователю
                    await send_account_to_user(order.user_id, account)

        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"xRocket webhook error: {e}")
        return jsonify({"ok": False}), 500


# ==================== Отправка аккаунта пользователю ====================
async def send_account_to_user(user_id: int, account):
    """Отправка файла с куками пользователю"""
    try:
        cookies_path = f"cookies/{account.cookies_filename}"

        # Проверяем, существует ли файл
        import os
        if os.path.exists(cookies_path):
            # Отправляем файл
            with open(cookies_path, 'rb') as f:
                await bot.send_document(
                    user_id,
                    document=f,
                    caption=f"""
✅ *Аккаунт успешно оплачен!*

📱 Аккаунт: {account.nickname or 'без ника'}
📅 Дата регистрации: {account.registration_date}
💰 Цена: {account.price:.2f} $

*Скачайте файл с куками для входа.*
                    """,
                    parse_mode="Markdown"
                )
        else:
            await bot.send_message(
                user_id,
                f"❌ Ошибка: файл с куками для аккаунта {account.id} не найден.\n"
                f"Свяжитесь с поддержкой: @HeisenbergBr35"
            )
    except Exception as e:
        logger.error(f"Error sending account to user {user_id}: {e}")


# ==================== Запуск Flask ====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)