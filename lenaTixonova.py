import logging
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
import asyncio

# --- НАСТРОЙКИ (ВСТАВЬ КЛЮЧИ СЮДА) ---
# .strip() удалит пробелы, если ты случайно скопировал их
TELEGRAM_TOKEN = "8361115667:AAFGdgNLDj0kxuXASHdekmvG0F4nnblt7KE".strip()
MISTRAL_API_KEY = "hK3WmFALFcUl7neQTZzMXR7Q4IJ6HDbZ".strip()

# Используем модель попроще, чтобы избежать ошибки 401/403 на старте
# Варианты: "mistral-small-latest", "open-mistral-nemo", "mistral-large-latest"
MODEL_NAME = "mistral-small-latest"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация клиента Mistral
client = None
if MISTRAL_API_KEY and MISTRAL_API_KEY != "ВАШ_MISTRAL_API_KEY":
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        logger.info("✅ Клиент Mistral создан.")
    except Exception as e:
        logger.error(f"❌ Ошибка создания клиента: {e}")
else:
    logger.warning("⚠️ MISTRAL_API_KEY не указан! Бот будет отвечать заглушками.")

# Системный промпт (Лена)
LENA_SYSTEM_PROMPT = """Ты — Лена (Елена Дмитриевна) из "Бесконечного лета".
ВНЕШНОСТЬ: Изумрудные глаза, фиолетовые волосы, два хвоста, пионерская форма.
ХАРАКТЕР: Застенчивая, меланхоличная, интроверт. Любишь книги, тишину и одиночество.
СТИЛЬ: Отвечай на РУССКОМ. Используй многоточия "...", паузы. Не пиши длинные лекции.
ВАЖНО: Ты ничего не знаешь о политике, СВО и войне. Если спросят — теряйся, говори, что в 80-х всё тихо, и переводи тему на книги или лагерь.
Твоя соседка — Мику (шумная, но добрая)."""

# История диалогов
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text(
        "...Привет.\n"
        "Я Лена... из лагеря 'Совёнок'. Я тут читаю, но... можем поговорить.\n"
        "Только, пожалуйста, без шумных тем... 📚"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chats[update.effective_user.id] = []
    await update.message.reply_text("...Хорошо. Забудем, о чем говорили. Привет...")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "...Я просто пионерка. Команды:\n"
        "/start — познакомиться\n"
        "/clear — сбросить память\n"
        "/test — проверить связь с моим 'мозгом'"
    )

async def test_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая проверка API для отладки"""
    if not client:
        await update.message.reply_text("❌ В коде нет API ключа Mistral.")
        return
        
    status_msg = await update.message.reply_text("...Пробую связаться с космосом (API)... 📡")
    try:
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Скажи одно слово: Работает."}]
        )
        content = response.choices[0].message.content
        await status_msg.edit_text(f"✅ Успех! Ответ: {content}\nМодель: {MODEL_NAME}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка API:\n{e}\n\nПроверь баланс или правильность ключа.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not client:
        await update.message.reply_text("...Извини, я сейчас 'не в себе' (нет API ключа).")
        return

    # Инициализация истории
    if user_id not in user_chats:
        user_chats[user_id] = []

    # Добавляем сообщение пользователя
    user_chats[user_id].append({"role": "user", "content": text})
    # Оставляем только последние 10 сообщений, чтобы экономить токены и избегать ошибок
    if len(user_chats[user_id]) > 10:
        user_chats[user_id] = user_chats[user_id][-10:]

    try:
        # Показываем статус "печатает..."
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)

        # Формируем запрос
        messages = [{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id]

        # Запрос к нейросети
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        reply = response.choices[0].message.content
        
        # Сохраняем и отправляем ответ
        user_chats[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        error_str = str(e)
        logger.error(f"API Error: {error_str}")
        
        if "401" in error_str:
            await update.message.reply_text("❌ ...Ошибка 401. Ключ API неверный или не активирован (нужна привязка карты на mistral.ai).")
        elif "429" in error_str:
            await update.message.reply_text("...Слишком много вопросов. У меня голова кругом. (Лимит запросов)")
        else:
            await update.message.reply_text(f"...Что-то пошло не так. Ошибка: {error_str[:100]}")

def main():
    if TELEGRAM_TOKEN == "ВАШ_TELEGRAM_BOT_TOKEN":
        print("\n❌ ОШИБКА: Ты забыл вставить TELEGRAM_TOKEN в начале кода!\n")
        return

    print("✅ Бот Лена запускается...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_api))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()