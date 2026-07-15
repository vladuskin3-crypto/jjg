import telebot
from telebot import types
from datetime import datetime
import re

# ================= НАСТРОЙКИ =================
TOKEN = '8919583440:AAHKm28DtvwRMwkEyet6sZ5cFTWQR_lXNSw'  # <-- ВСТАВЬ СЮДА ТОКЕН ОТ @BotFather
ADMIN_ID = 7885156097      # <-- ВСТАВЬ СЮДА СВОЙ TELEGRAM ID (цифры)
CHANNEL_USERNAME = '@WhiHosting' # <-- ВСТАВЬ ЮЗЕРНЕЙМ КАНАЛА БЕЗ @ (или с @, код обработает)
SUPPORT_BOT_USERNAME = "suportWhiteHosting_bot" # <-- Имя пользователя бота поддержки

bot = telebot.TeleBot(TOKEN)

# Имитация базы данных (в памяти). При перезапуске данные сбросятся.
# Формат: {user_id: {'username': str, 'balance': float, 'joined_at': str, 'subscribed': bool}}
users_db = {}

def get_user(user):
    """
    Получает информацию о пользователе из базы данных или создает новую запись, если пользователь не найден.
    """
    uid = user.id
    if uid not in users_db:
        users_db[uid] = {
            'username': user.username or "Без юзернейма",
            'balance': 0.0,
            'joined_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'subscribed': False
        }
    return users_db[uid]

# ================= ГЛАВНОЕ МЕНЮ И ПОДПИСКА =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обрабатывает команду /start. Проверяет подписку на канал и показывает главное меню.
    """
    user = message.from_user
    info = get_user(user)

    # Если пользователь еще не подтвердил подписку
    if not info['subscribed']:
        markup = types.InlineKeyboardMarkup()
        channel_link = CHANNEL_USERNAME if CHANNEL_USERNAME.startswith('@') else f"@{CHANNEL_USERNAME}"
        url_btn = types.InlineKeyboardButton("🔗 Перейти в канал", url=f"https://t.me/{channel_link.replace('@', '')}")
        done_btn = types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")

        markup.add(url_btn)
        markup.add(done_btn)

        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Чтобы пользоваться магазином, нужно быть подписанным на наш канал:\n"
            f"{channel_link}\n\n"
            f"Нажми кнопку ниже после подписки."
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return

    # Если уже подписан - показываем главное меню
    show_main_menu(message)

def show_main_menu(message):
    """
    Отображает главное меню бота с кнопками "Купить", "Профиль", "Поддержка".
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_buy = types.KeyboardButton("🛍 Купить")
    btn_profile = types.KeyboardButton("👤 Профиль")
    btn_support = types.KeyboardButton("💬 Поддержка")

    markup.add(btn_buy, btn_profile)
    markup.add(btn_support)

    text = (
        f"🎉 Добро пожаловать в магазин!\n"
        f"Выбирай интересующий раздел в меню."
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
    """
    Обрабатывает нажатие кнопки "Я подписался". Помечает пользователя как подписанного.
    """
    # В этом примере мы доверяем нажатию кнопки. В реальном проекте нужна API-проверка.
    users_db[call.from_user.id]['subscribed'] = True
    bot.answer_callback_query(call.id, "Спасибо за подписку! Теперь доступ открыт.")
    show_main_menu(call.message) # Показываем главное меню после успешной подписки

# ================= МАГАЗИН (КУПИТЬ) =================

@bot.message_handler(func=lambda message: message.text == "🛍 Купить")
def show_products(message):
    """
    Отображает список товаров для покупки с их ценами.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    products = [
        ("prod_1week", "📅 1 неделя — 120 ₽"),
        ("prod_2week", "🗓 2 недели — 200 ₽"),
        ("prod_3week", "📆 3 недели — 270 ₽"),
        ("prod_1month", "🗓 1 месяц — 350 ₽") # Добавлена опция на месяц
    ]

    for data, text in products:
        markup.add(types.InlineKeyboardButton(text, callback_data=data))

    bot.send_message(message.chat.id, "🛒 Выбери срок доступа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("prod_"))
def process_product(call):
    """
    Обрабатывает выбор товара. Списывает баланс пользователя и уведомляет о покупке.
    """
    prod_map = {
        "prod_1week": "1 неделя",
        "prod_2week": "2 недели",
        "prod_3week": "3 недели",
        "prod_1month": "1 месяц" # Соответствие ключа для месяца
    }
    name = prod_map.get(call.data, "Товар")
    price_map = {"prod_1week": 120, "prod_2week": 200, "prod_3week": 270, "prod_1month": 350} # Цена за месяц
    price = price_map.get(call.data)

    user_info = get_user(call.from_user)

    # Проверка достаточности средств на балансе
    if user_info['balance'] < price:
        bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {price} ₽", show_alert=True)
        return

    # Списываем баланс и уведомляем пользователя
    user_info['balance'] -= price
    bot.answer_callback_query(call.id, f"✅ Покупка: {name}")
    bot.send_message(
        call.message.chat.id,
        f"✅ Успешная покупка!\nТы приобрел доступ на **{name}**.\nБаланс обновлен.",
        parse_mode="Markdown"
    )

# ================= ПРОФИЛЬ =================

@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def show_profile(message):
    """
    Отображает профиль пользователя, включая баланс, ID, дату регистрации.
    """
    user = message.from_user
    info = get_user(user)

    # Создаем кнопку для пополнения баланса, ведущую на сообщение владельцу
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Пополнить баланс", url=f"https://t.me/{SUPPORT_BOT_USERNAME}?start=topup_{user.id}"))

    text = (
        f"👤 **Твой профиль**\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"🧑‍💻 Юзернейм: @{info['username']}\n"
        f"💰 Баланс: **{info['balance']} ₽**\n"
        f"📅 Дата регистрации: {info['joined_at']}"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ================= ПОДДЕРЖКА (ПЕРЕВОД НА ДРУГОГО БОТА) =================

@bot.message_handler(func=lambda message: message.text == "💬 Поддержка")
def support_redirect(message):
    """
    Перенаправляет пользователя к боту поддержки.
    """
    markup = types.InlineKeyboardMarkup()
    # Создаем кнопку, которая открывает чат с ботом поддержки
    markup.add(types.InlineKeyboardButton("🚀 Перейти к поддержке", url=f"https://t.me/{SUPPORT_BOT_USERNAME}"))

    bot.send_message(
        message.chat.id,
        "👨‍💻 Для связи с поддержкой, пожалуйста, перейди в чат с нашим ботом поддержки:",
        reply_markup=markup
    )

# === Админские команды (для информации, если нужно) ===
@bot.message_handler(commands=['users'])
def show_users_list(message):
    """
    Показывает список всех пользователей (только для админа).
    """
    if message.from_user.id != 7885156097:
        return

    if not users_db:
        bot.reply_to(message, "База данных пользователей пуста.")
        return

    user_list_text = "Список пользователей:\n\n"
    for uid, info in users_db.items():
        user_list_text += f"- ID: {uid}, Username: @{info['username']}, Balance: {info['balance']} ₽\n"

    bot.reply_to(message, user_list_text)

# ================= ЗАПУСК БОТА =================
if __name__ == '__main__':
    # Бот запускается в режиме опроса (polling).
    bot.polling(none_stop=True)
