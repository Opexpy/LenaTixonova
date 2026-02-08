import os
import sys
import subprocess
import logging
import time
import asyncio

# --- АВТО-УСТАНОВКА БИБЛИОТЕК ---
try:
    from telegram import Update, constants
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from groq import Groq
except ImportError:
    print("Устанавливаю библиотеки...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "groq", "python-telegram-bot"])
    from telegram import Update, constants
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from groq import Groq

# --- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ) ---
TELEGRAM_TOKEN = "8361115667:AAF9H-3SSBP_JVTOYeiAwqRlpSS5Jtlvekg"
GROQ_API_KEY = "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"

# ЭТА МОДЕЛЬ САМАЯ СТАБИЛЬНАЯ ДЛЯ БЕСПЛАТНОГО ТАРИФА (БЕЗ ОШИБКИ 403)
MODEL_NAME = "llama3-8b-8192"

logging.basicConfig(level=logging.INFO)

LENA_SYSTEM_PROMPT = """
Ты — Лена Тихонова из "Бесконечного лета". 
- Ты тихая, застенчивая, фиолетовые волосы в хвостах.
- Постоянно читаешь, любишь запах книг.
- Используешь "..." в речи, смущаешься.
- Ты из 80-х, пионерлагерь "Совёнок". Никакой политики и интернета.
- У тебя сложные отношения с Алисой и теплые, но грустные — с Семёном.
- Помнишь сюжет оригинала и популярных модов (твоя меланхолия и "тихий омут").
"""

user_chats = {}

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("...Привет. Я Лена Тихонова... Я тебя раньше не видела в нашем отряде. Ты тоже... любишь читать?")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chats[update.effective_user.id] = []
    await update.message.reply_text("...Хорошо. Я закрою эту книгу. Давай начнем с чистого листа...")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        client.models.list()
        await update.message.reply_text(f"✅ Статус: Связь с библиотекой установлена.\nМодель: {MODEL_NAME}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка связи: {e}")

# --- ЛОГИКА ОБЩЕНИЯ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_chats:
        user_chats[user_id] = []

    user_chats[user_id].append({"role": "user", "content": update.message.text})
    if len(user_chats[user_id]) > 10:
        user_chats[user_id] = user_chats[user_id][-10:]

    try:
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)
        
        client = Groq(api_key=GROQ_API_KEY)
        # Добавляем небольшую задержку, чтобы избежать 403/429 при спаме
        await asyncio.sleep(0.5)

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id],
            temperature=0.7,
            max_tokens=500
        )

        reply = completion.choices[0].message.content
        user_chats[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        error_text = str(e)
        if "403" in error_text:
            msg = "...Кажется, вожатая запретила мне общаться (Ошибка 403). Попробуй включить VPN или смени ключ API."
        elif "429" in error_text:
            msg = "...Я не успеваю за твоими словами. Давай помолчим минуту?"
        else:
            msg = f"...Ой, у меня голова закружилась... (Ошибка: {error_text[:60]})"
        await update.message.reply_text(msg)

def main():
    if "ВАШ_" in TELEGRAM_TOKEN or "gsk" not in GROQ_API_KEY:
        print("❌ ОШИБКА: Проверь ключи в коде!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"✅ Лена Тихонова запущена на модели {MODEL_NAME}")
    app.run_polling()

if __name__ == "__main__":
    main()