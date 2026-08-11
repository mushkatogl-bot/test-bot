import random
import re
from datetime import datetime


def generate_order_id() -> str:
    """Генерация номера заказа (8 цифр)"""
    return str(random.randint(10000000, 99999999))


def parse_account_data(line: str) -> dict:
    """
    Парсинг строки с данными аккаунта.
    Формат: дата|тип_номера|никнейм|игра|топ|цена|файл_кук
    Пример: 2024-01-15|DE|@user1|есть|нет|5.50|cookies_user1.txt
    """
    parts = [p.strip() for p in line.split('|')]

    if len(parts) < 7:
        raise ValueError(f"Недостаточно данных. Ожидается 7 полей, получено {len(parts)}")

    return {
        'registration_date': parts[0],
        'number_type': parts[1],
        'nickname': parts[2] if parts[2] != '-' else None,
        'has_game': parts[3].lower() in ['есть', 'да', '+', 'true'],
        'is_top': parts[4].lower() in ['есть', 'да', '+', 'true'],
        'price': float(parts[5].replace(',', '.')),
        'cookies_file': parts[6]
    }


def format_order_history(orders) -> str:
    """Форматирование истории заказов"""
    if not orders:
        return "📭 У вас пока нет заказов."

    text = f"📋 *История заказов*\n\nВсего заказов: {len(orders)}\n"
    text += "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"

    for order in orders[:10]:
        text += f"""
💡 Заказ #{order.order_id}
🕐 Время: {order.created_at.strftime('%Y-%m-%d %H:%M')}
🕐 Статус: {order.status}
💰 Сумма: {order.amount:.2f} $
💰 Способ: {order.payment_method}
➖➖➖➖➖➖➖➖➖➖➖➖\n
        """

    return text


def validate_telegram_id(telegram_id: int) -> bool:
    """Валидация Telegram ID"""
    return isinstance(telegram_id, int) and telegram_id > 0


def get_current_time() -> str:
    """Текущее время в формате для отображения"""
    return datetime.now().strftime('%Y-%m-%d %H:%M')