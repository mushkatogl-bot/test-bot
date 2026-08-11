import os
import zipfile
import shutil
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import dp, bot
from database import User, Account, Order, get_db
from keyboards import get_admin_keyboard, get_cancel_keyboard
from config import ADMIN_IDS
from utils import parse_account_data


# ==================== Проверка админа ====================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==================== Состояния для загрузки аккаунтов ====================
class AdminStates(StatesGroup):
    waiting_for_zip = State()
    waiting_for_account_data = State()
    waiting_for_account_file = State()


# ==================== Команда /admin ====================
@dp.message_handler(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора.")
        return

    await message.answer(
        "👑 *Панель администратора*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )


# ==================== Загрузка аккаунтов ====================
@dp.message_handler(lambda m: m.text == "➕ Загрузить аккаунты" and is_admin(m.from_user.id))
async def admin_upload_accounts(message: types.Message, state: FSMContext):
    await message.answer(
        "📤 *Загрузка аккаунтов*\n\n"
        "Отправьте ZIP-архив с файлами:\n"
        "1. Файл `accounts.txt` с данными аккаунтов (формат: каждая строка - аккаунт)\n"
        "2. Папка `cookies/` с TXT-файлами кук\n\n"
        "Или используйте пошаговое добавление: /add_account",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_zip)


# ==================== Обработка ZIP-архива ====================
@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=AdminStates.waiting_for_zip)
async def handle_zip_upload(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    document = message.document
    if not document.file_name.endswith('.zip'):
        await message.answer("❌ Пожалуйста, отправьте ZIP-архив.")
        return

    # Скачиваем архив
    file = await bot.get_file(document.file_id)
    file_path = f"temp_{document.file_name}"
    await file.download(file_path)

    # Распаковываем
    extract_path = f"extract_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Ищем файлы
    accounts_file = None
    cookies_dir = None

    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file == 'accounts.txt':
                accounts_file = os.path.join(root, file)
        if 'cookies' in dirs:
            cookies_dir = os.path.join(root, 'cookies')

    if not accounts_file:
        await message.answer("❌ Файл `accounts.txt` не найден в архиве.")
        shutil.rmtree(extract_path)
        os.remove(file_path)
        await state.finish()
        return

    # Парсим аккаунты
    with next(get_db()) as db:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = parse_account_data(line)
                    account = Account(
                        registration_date=data['registration_date'],
                        number_type=data['number_type'],
                        nickname=data.get('nickname'),
                        has_game=data.get('has_game', False),
                        is_top=data.get('is_top', False),
                        cookies_filename=data['cookies_file'],
                        price=data['price'],
                        is_sold=False
                    )
                    db.add(account)
                    db.commit()

                    # Копируем файл с куками
                    if cookies_dir:
                        src_cookie = os.path.join(cookies_dir, data['cookies_file'])
                        if os.path.exists(src_cookie):
                            dst_cookie = os.path.join('cookies', data['cookies_file'])
                            shutil.copy2(src_cookie, dst_cookie)

                except Exception as e:
                    await message.answer(f"⚠️ Ошибка в строке: {line}\n{str(e)}")
                    continue

    # Очистка
    shutil.rmtree(extract_path)
    os.remove(file_path)

    await message.answer("✅ Аккаунты успешно загружены!", reply_markup=get_admin_keyboard())
    await state.finish()


# ==================== Статистика ====================
@dp.message_handler(lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
async def admin_stats(message: types.Message):
    with next(get_db()) as db:
        total_users = db.query(User).count()
        total_orders = db.query(Order).filter_by(status="Оплачен").count()
        total_revenue = db.query(Order).filter_by(status="Оплачен").with_entities(
            db.func.sum(Order.amount)
        ).scalar() or 0

        stats_text = f"""
📊 *Статистика магазина*

👥 Всего пользователей: {total_users}
📦 Всего продаж: {total_orders}
💰 Общая выручка: {total_revenue:.2f} $
📈 Средний чек: {total_revenue / total_orders if total_orders > 0 else 0:.2f} $
        """

        await message.answer(stats_text, parse_mode="Markdown")


# ==================== Список пользователей ====================
@dp.message_handler(lambda m: m.text == "👥 Все пользователи" and is_admin(m.from_user.id))
async def admin_users_list(message: types.Message):
    with next(get_db()) as db:
        users = db.query(User).order_by(User.total_orders.desc()).all()

        if not users:
            await message.answer("📭 Пользователей пока нет.")
            return

        response = "👥 *Список пользователей*\n\n"
        for user in users[:20]:  # Показываем первых 20
            response += f"👤 @{user.username or 'без ника'} | Заказов: {user.total_orders} | 💰 {user.total_spent:.2f}$\n"

        if len(users) > 20:
            response += f"\n... и еще {len(users) - 20} пользователей."

        await message.answer(response, parse_mode="Markdown")


# ==================== Управление аккаунтами ====================
@dp.message_handler(lambda m: m.text == "📦 Управление аккаунтами" and is_admin(m.from_user.id))
async def admin_accounts_manage(message: types.Message):
    with next(get_db()) as db:
        accounts = db.query(Account).all()

        if not accounts:
            await message.answer("📭 Нет аккаунтов.")
            return

        response = "📦 *Список аккаунтов*\n\n"
        for acc in accounts:
            status = "✅ Продан" if acc.is_sold else "🟢 В наличии"
            response += f"ID: {acc.id} | {acc.registration_date} | {acc.nickname or 'без ника'} | {acc.price}$ | {status}\n"

        await message.answer(response, parse_mode="Markdown")


# ==================== Отмена ====================
@dp.message_handler(Text(equals="❌ Отмена"), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())