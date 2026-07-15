import telebot
from telebot import types
from datetime import datetime

# ================= НАСТРОЙКИ =================
# ⚠️ ВСТАВЬ СЮДА НОВЫЙ ТОКЕН ПОСЛЕ ОТЗЫВА СТАРОГО В @BOTFATHER
TOKEN = '8919583440:AAHKm28DtvwRMwkEyet6sZ5cFTWQR_lXNSw' 
ADMIN_ID = 7885156097      
CHANNEL_USERNAME = '@WhiHosting'
SUPPORT_BOT_USERNAME = "suportWhiteHosting_bot"

bot = telebot.TeleBot(TOKEN)

# Имитация базы данных (в памяти)
users_db = {}

def get_user(user):
    """
    Получает информацию о пользователе. Если нет - создает.
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

def is_admin(user_id):
    """Проверка, является ли пользователь админом."""
    return user_id == 7885156097

# ================= ГЛАВНОЕ МЕНЮ И ПОДПИСКА =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    info = get_user(user)

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

    show_main_menu(message)

def show_main_menu(message):
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
    users_db[call.from_user.id]['subscribed'] = True
    bot.answer_callback_query(call.id, "Спасибо за подписку! Теперь доступ открыт.")
    show_main_menu(call.message)

# ================= МАГАЗИН (КУПИТЬ) =================

@bot.message_handler(func=lambda message: message.text == "🛍 Купить")
def show_products(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    products = [
        ("prod_1week", "📅 1 неделя — 120 ₽"),
        ("prod_2week", "🗓 2 недели — 200 ₽"),
        ("prod_3week", "📆 3 недели — 270 ₽"),
        ("prod_1month", "🗓 1 месяц — 350 ₽")
    ]

    for data, text in products:
        markup.add(types.InlineKeyboardButton(text, callback_data=data))

    bot.send_message(message.chat.id, "🛒 Выбери срок доступа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("prod_"))
def process_product(call):
    prod_map = {
        "prod_1week": "1 неделя",
        "prod_2week": "2 недели",
        "prod_3week": "3 недели",
        "prod_1month": "1 месяц"
    }
    name = prod_map.get(call.data, "Товар")
    price_map = {"prod_1week": 120, "prod_2week": 200, "prod_3week": 270, "prod_1month": 350}
    price = price_map.get(call.data)

    user_info = get_user(call.from_user)

    if user_info['balance'] < price:
        bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {price} ₽", show_alert=True)
        return

    # Списываем баланс
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
    user = message.from_user
    info = get_user(user)

    markup = types.InlineKeyboardMarkup()
    # Кнопка ведет к боту поддержки (как было у тебя)
    markup.add(types.InlineKeyboardButton("➕ Пополнить баланс", url=f"https://t.me/{SUPPORT_BOT_USERNAME}?start=topup_{user.id}"))

    text = (
        f"👤 **Твой профиль**\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"🧑‍💻 Юзернейм: @{info['username']}\n"
        f"💰 Баланс: **{info['balance']} ₽**\n"
        f"📅 Дата регистрации: {info['joined_at']}"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ================= ПОДДЕРЖКА =================

@bot.message_handler(func=lambda message: message.text == "💬 Поддержка")
def support_redirect(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Перейти к поддержке", url=f"https://t.me/{SUPPORT_BOT_USERNAME}"))

    bot.send_message(
        message.chat.id,
        "👨‍💻 Для связи с поддержкой, пожалуйста, перейди в чат с нашим ботом поддержки:",
        reply_markup=markup
    )

# ================= АДМИН ПАНЕЛЬ (НОВЫЕ КОМАНДЫ) =================

@bot.message_handler(commands=['give'])
def admin_give_balance(message):
    """Команда /give <USER_ID> <AMOUNT> - начислить баланс"""
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Использование: `/give <USER_ID> <СУММА>`\nПример: `/give 123456789 500`", parse_mode="Markdown")
        return
    
    try:
        target_id = int(args[1])
        amount = float(args[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0.")
            return

        # Если пользователя нет в базе, создаем его (чтобы можно было начислить даже новым людям)
        if target_id not in users_db:
            # Нам нужно имя пользователя, но мы не можем его получить без запроса к API.
            # Создаем заглушку. При первом заходе в бота имя обновится.
            users_db[target_id] = {
                'username': "Неизвестный пользователь",
                'balance': 0.0,
                'joined_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
                'subscribed': False
            }
            bot.reply_to(message, f"⚠️ Пользователь {target_id} не был в базе. Создана запись.")

        users_db[target_id]['balance'] += amount
        
        bot.reply_to(
            message, 
            f"✅ Баланс пользователя `{target_id}` успешно пополнен на `{amount} ₽`!", 
            parse_mode="Markdown"
        )

        # Уведомляем самого пользователя
        try:
            bot.send_message(
                target_id, 
                f"💰 Админ пополнил твой баланс на **{amount} ₽**!\nТекущий баланс: **{users_db[target_id]['balance']} ₽**",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Не удалось отправить уведомление пользователю (возможно, он заблокировал бота). Ошибка: {e}")

    except ValueError:
        bot.reply_to(message, "❌ Ошибка формата. ID и сумма должны быть числами.")

@bot.message_handler(commands=['take'])
def admin_take_balance(message):
    """Команда /take <USER_ID> <AMOUNT> - списать баланс"""
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Использование: `/take <USER_ID> <СУММА>`\nПример: `/take 123456789 100`", parse_mode="Markdown")
        return
    
    try:
        target_id = int(args[1])
        amount = float(args[2])

        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0.")
            return

        if target_id not in users_db:
            bot.reply_to(message, "❌ Пользователь не найден в базе данных.")
            return

        current_balance = users_db[target_id]['balance']
        
        if current_balance < amount:
            bot.reply_to(message, f"❌ У пользователя недостаточно средств! Баланс: {current_balance} ₽, запрашивают: {amount} ₽")
            return

        users_db[target_id]['balance'] -= amount
        
        bot.reply_to(
            message, 
            f"✅ С баланса пользователя `{target_id}` списано `{amount} ₽`.\nОстаток: `{users_db[target_id]['balance']} ₽`", 
            parse_mode="Markdown"
        )

        # Уведомляем пользователя
        try:
            bot.send_message(
                target_id,
                f"⚠️ С твоего баланса списано **{amount} ₽** администратором.\nТекущий баланс: **{users_db[target_id]['balance']} ₽**",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Не удалось уведомить пользователя (заблокировал бота).")

    except ValueError:
        bot.reply_to(message, "❌ Ошибка формата.")

# Команда для просмотра списка пользователей (оставил твою)
@bot.message_handler(commands=['users'])
def show_users_list(message):
    if not is_admin(message.from_user.id):
        return

    if not users_db:
        bot.reply_to(message, "База данных пользователей пуста.")
        return

    user_list_text = "📋 Список пользователей:\n\n"
    count = 0
    for uid, info in users_db.items():
        user_list_text += f"ID: `{uid}` | @{info['username']} | Баланс: `{info['balance']} ₽`\n"
        count += 1
        if count >= 20: # Чтобы не спамить слишком длинными сообщениями, можно разбить на части
            break
            
    user_list_text += f"\n... и еще {len(users_db) - count} пользователей."
    
    bot.reply_to(message, user_list_text, parse_mode="Markdown")

# ================= ЗАПУСК БОТА =================
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
       
