import logging
import asyncio
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral

# --- КОНФИГУРАЦИЯ ---
# Вставь токены сюда (обязательно!)
TELEGRAM_TOKEN = "8361115667:AAFGdgNLDj0kxuXASHdekmvG0F4nnblt7KE".strip()
MISTRAL_API_KEY = "hK3WmFALFcUl7neQTZzMXR7Q4IJ6HDbZ".strip()

# Легкая модель, которая реже ловит лимиты
MODEL_NAME = "open-mistral-nemo"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация клиента
try:
    client = Mistral(api_key=MISTRAL_API_KEY)
except Exception as e:
    client = None
    print(f"Ошибка Mistral: {e}")

LENA_SYSTEM_PROMPT = """Ты — Лена из "Бесконечного лета". Застенчивая пионерка. 
Используй "..." в речи. Не говори о политике. Ты любишь книги и тишину."""

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("...Привет. Я Лена. Давай просто... пообщаемся? 📚")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chats[update.effective_user.id] = []
    await update.message.reply_text("...Я всё забыла. Начнем сначала?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not client:
        await update.message.reply_text("...У меня пропала связь с миром. Проверь API ключ.")
        return

    if user_id not in user_chats:
        user_chats[user_id] = []

    # Добавляем сообщение пользователя
    user_chats[user_id].append({"role": "user", "content": text})
    if len(user_chats[user_id]) > 8: # Сократил историю, чтобы не превышать лимиты
        user_chats[user_id] = user_chats[user_id][-8:]

    try:
        # 1. Показываем статус "печатает"
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)

        # 2. ПАУЗА 2 СЕКУНДЫ (чтобы соблюдать твой лимит 1 запрос в сек)
        await asyncio.sleep(2.0)

        # 3. Запрос к нейросети
        messages = [{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id]
        
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        user_chats[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Ошибка: {err_msg}")
        
        if "429" in err_msg:
            await update.message.reply_text("...Извини, я немного устала отвечать. Подожди минутку, пожалуйста.")
            # Если словили лимит — очищаем последнее сообщение, чтобы оно не зациклилось
            user_chats[user_id] = user_chats[user_id][:-1] 
        else:
            await update.message.reply_text("...Ой, что-то голова разболелась. Давай попробуем позже?")

def main():
    if "ВАШ_" in TELEGRAM_TOKEN or not TELEGRAM_TOKEN:
        print("ОШИБКА: Вставь токен в код!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен. Лена ждет сообщений.")
    app.run_polling()

if __name__ == '__main__':
    main()