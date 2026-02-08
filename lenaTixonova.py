import logging
import asyncio
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8361115667:AAF9H-3SSBP_JVTOYeiAwqRlpSS5Jtlvekg".strip()
GROQ_API_KEY = "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".strip()

# Модель от Meta (Llama 3), она очень умная и быстрая
MODEL_NAME = "llama-3.3-70b-versatile"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация клиента Groq
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    client = None
    print(f"Ошибка Groq: {e}")

LENA_SYSTEM_PROMPT = """Ты — Лена (Елена Тихонова) из "Бесконечного лета".
ХАРАКТЕР: Застенчивая, тихая, любишь читать под кипарисами. Ты часто смущаешься и используешь "...".
ОТНОШЕНИЯ И ПЕРСОНАЖИ:
- Иногда вспоминай Алису (Двачевскую). Она тебя задирает, и ты её немного побаиваешься, но в душе ценишь.
- Упоминай Славяну, как пример идеальной помощницы вожатой.
- Вспоминай Ульяну, когда речь заходит о шуме или краже котлет.
- Мику — твоя шумная соседка.
- Ты тоскуешь по тишине и иногда хочешь, чтобы кто-то просто посидел рядом.
СТИЛЬ: Отвечай на русском. Коротко, меланхолично, интровертно. Никакой политики."""

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("...Ой. Привет. Я не заметила, как ты подошел... Я тут читала. Я Лена... Хочешь посидеть рядом?")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chats[update.effective_user.id] = []
    await update.message.reply_text("...Хорошо. Я закрою эту страницу... Давай начнем с чистого листа.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not client:
        await update.message.reply_text("...У меня карандаш сломался (API ошибка). Проверь ключи.")
        return

    if user_id not in user_chats:
        user_chats[user_id] = []

    user_chats[user_id].append({"role": "user", "content": text})
    if len(user_chats[user_id]) > 10:
        user_chats[user_id] = user_chats[user_id][-10:]

    try:
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)
        
        # Groq работает очень быстро, пауза 1 сек просто для естественности
        await asyncio.sleep(1)

        messages = [{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id]
        
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        
        reply = completion.choices[0].message.content
        user_chats[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("...Прости, я... я запуталась в мыслях. Попробуй еще раз чуть позже.")

def main():
    if "ТВОЙ_" in TELEGRAM_TOKEN:
        print("ОШИБКА: Вставь токен Telegram!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Лена запущена на движке Groq! Лимитов больше не будет.")
    app.run_polling()

if __name__ == '__main__':

    main()
