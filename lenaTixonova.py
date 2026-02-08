import os
import sys
import subprocess
import logging
import time

# --- АВТО-УСТАНОВКА БИБЛИОТЕК ---
try:
    from telegram import Update, constants
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from groq import Groq
except ImportError:
    print("Устанавливаю необходимые библиотеки...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "groq", "python-telegram-bot"])
    from telegram import Update, constants
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from groq import Groq

# --- НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ВСТАВЬ СВОИ) ---
TELEGRAM_TOKEN = "8361115667:AAF9H-3SSBP_JVTOYeiAwqRlpSS5Jtlvekg"
GROQ_API_KEY = "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"

# Модель
MODEL_NAME = "llama-3.3-70b-versatile"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

LENA_SYSTEM_PROMPT = """
Ты — Лена Тихонова из игры "Бесконечное лето".
ЛИЧНОСТЬ:
- Застенчивая, тихая, любишь книги. Фамилия Тихонова, отчества нет.
- Ты из 1980-х, пионерлагерь "Совёнок". Никакого интернета или политики.
- В речи используешь "..." и часто смущаешься.
- Твой образ из канона и модов: глубокая, иногда меланхоличная, верная, но скрытная.
"""

user_chats = {}

# --- КОМАНДА ПРОВЕРКИ СТАТУСА (ОТЛАДКА) ---
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    try:
        # Проверяем Groq
        client = Groq(api_key=GROQ_API_KEY)
        client.models.list()
        groq_status = "✅ Работает"
    except Exception as e:
        groq_status = f"❌ Ошибка: {str(e)[:50]}"
    
    ping = round((time.time() - start_time) * 1000)
    
    status_text = (
        f"🔍 **Отчет Лены:**\n"
        f"Библиотека: `Библиотека 'Совёнка' открыта`\n"
        f"Связь с Groq: `{groq_status}`\n"
        f"Задержка: `{ping}мс`\n"
        f"Активных диалогов: `{len(user_chats)}`"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")

# --- КОМАНДА ОЧИСТКИ ЧАТА ---
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("...Я закрыла книгу. Давай... давай начнем новую главу. О чем мы говорили? Я всё забыла...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("...Ой. Привет. Я Лена... Ты тоже из этого отряда? Я тебя раньше не видела...")

# --- ОБРАБОТКА СООБЩЕНИЙ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = []

    user_chats[user_id].append({"role": "user", "content": user_input})
    
    # Храним последние 10 сообщений
    if len(user_chats[user_id]) > 10:
        user_chats[user_id] = user_chats[user_id][-10:]

    try:
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)
        
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id],
            temperature=0.7
        )

        response_text = completion.choices[0].message.content
        user_chats[user_id].append({"role": "assistant", "content": response_text})
        await update.message.reply_text(response_text)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        # Если произошла ошибка, бот выведет её техническую часть для тебя
        await update.message.reply_text(f"...Прости, я... я запуталась. Кажется, в моей книге вырвали страницы... (Ошибка: {str(e)[:100]})")

def main():
    if "ВАШ_" in TELEGRAM_TOKEN:
        print("❌ ОШИБКА: Вставь токен в код!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("status", status)) # Отладочная команда
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Лена Тихонова запущена. Команды: /start, /clear, /status")
    application.run_polling()

if __name__ == "__main__":
    main()