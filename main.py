from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction
import sqlite3
import datetime

# === Настройки ===
BOT_TOKEN = '7624710888:AAHAIYsOjoWTCvtUVlx6XwnEWI-eyLuPok8'
ADMIN_IDS = [992028570207, 992928570207]  # ID администраторов

# === Работа с базой данных ===
conn = sqlite3.connect('cargo.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS cargo (
        tracking_number TEXT PRIMARY KEY,
        status TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_number TEXT,
        action TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()

# === Вспомогательные функции ===
async def send_typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

def log_action(tracking_number, action, status):
    cursor.execute('INSERT INTO log (tracking_number, action, status) VALUES (?, ?, ?)',
                   (tracking_number, action, status))
    conn.commit()

def get_today_logs():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT tracking_number, action, status, strftime('%H:%M', timestamp)
        FROM log
        WHERE date(timestamp) = ?
    ''', (today,))
    return cursor.fetchall()

# === Команды бота ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing_action(update, context)

    keyboard = [
        ["🛠 Я админ", "👤 Я пользователь"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Здравствуйте! ✋\n"
        "Салом! ✋\n\n"
        "Выберите, кто вы: 👇\n"
        "Лутфан интихоб кунед:",
        reply_markup=reply_markup
    )

async def role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛠 Я админ":
        await update.message.reply_text(
            "🔑 Вы выбрали режим администратора!\n\n"
            "Доступные команды:\n"
            "/add <номер> — добавить товар ➕\n"
            "/arrived <номер> — отметить прибытие ✈\n"
            "/today — отчёт за сегодня 📋",
            reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру
        )
    elif text == "👤 Я пользователь":
        await update.message.reply_text(
            "👤 Вы выбрали режим пользователя!\n\n"
            "Доступные команды:\n"
            "/status <номер> — узнать статус товара 📦",
            reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите одну из кнопок! 👇"
        )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing_action(update, context)
    if len(context.args) != 1:
        await update.message.reply_text(
            "Пожалуйста, отправьте так: /status <номер товара> ❗\n"
            "Лутфан чунин фиристед: /status <рақами бор>",
        )
        return

    tracking_number = context.args[0]
    cursor.execute('SELECT status FROM cargo WHERE tracking_number = ?', (tracking_number,))
    result = cursor.fetchone()

    if result:
        await update.message.reply_text(
            f"Статус товара 📦 {tracking_number}:\n"
            f"{result[0]} ✅\n\n"
            f"Вазъи бор 📦 {tracking_number}:\n"
            f"{result[0]} ✅",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"Товар с номером {tracking_number} не найден ❌\n"
            f"Бори рақами {tracking_number} ёфт нашуд ❌",
            parse_mode="Markdown"
        )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing_action(update, context)
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде. ❗\nШумо иҷозат надоред.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Пожалуйста, отправьте так: /add <номер> 📦\nЛутфан чунин фиристед: /add <рақам>")
        return

    tracking_number = context.args[0]

    cursor.execute('INSERT OR REPLACE INTO cargo (tracking_number, status) VALUES (?, ?)',
                   (tracking_number, 'Товар принят на складе в Китае'))
    conn.commit()
    log_action(tracking_number, 'Добавлен', 'Товар принят на складе в Китае')

    await update.message.reply_text(
        f"Товар {tracking_number} успешно добавлен! ✅\n"
        f"Бори рақами {tracking_number} бо муваффақият илова шуд! ✅",
        parse_mode="Markdown"
    )

async def arrived(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing_action(update, context)
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде. ❗\nШумо иҷозат надоред.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Пожалуйста, отправьте так: /arrived <номер> ✈\nЛутфан чунин фиристед: /arrived <рақам>")
        return

    tracking_number = context.args[0]

    cursor.execute('UPDATE cargo SET status = ? WHERE tracking_number = ?',
                   ('Товар прибыл в Таджикистан', tracking_number))
    conn.commit()
    log_action(tracking_number, 'Обновлен', 'Товар прибыл в Таджикистан')

    await update.message.reply_text(
        f"Статус товара {tracking_number} обновлён на 'Товар прибыл в Таджикистан' ✈✅\n"
        f"Вазъи бори {tracking_number} ба 'Ба Тоҷикистон расид' навсозӣ шуд ✈✅",
        parse_mode="Markdown"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing_action(update, context)
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде. ❗\nШумо иҷозат надоред.")
        return

    logs = get_today_logs()

    if not logs:
        await update.message.reply_text(
            "Сегодня пока не было операций. 📋\nИмрӯз ягон амалиёт анҷом дода нашудааст. 📋"
        )
        return

    added = sum(1 for log in logs if log[1] == 'Добавлен')
    updated = sum(1 for log in logs if log[1] == 'Обновлен')

    message = f"📋 *Отчёт за сегодня:*\n"
    message += f"➔ Добавлено товаров: {added} 📦\n"
    message += f"➔ Обновлено статусов: {updated} ✏\n\n"

    message += "📋 *Имрӯз:*\n"
    message += f"➔ Борҳо илова шуд: {added} 📦\n"
    message += f"➔ Вазъи борҳо навсозӣ шуд: {updated} ✏\n\n"

    for num, (tracking_number, action, status, time) in enumerate(logs, 1):
        icon = "➕" if action == 'Добавлен' else "✏"
        message += f"{num}. {tracking_number} {icon} {status} ({time})\n"

    await update.message.reply_text(message, parse_mode="Markdown")

# === Запуск приложения ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("arrived", arrived))
app.add_handler(CommandHandler("today", today))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, role_selection))

print("Бот успешно запущен...")
app.run_polling()
