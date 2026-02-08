import logging
import httpx
import re
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# СЮДА ВСТАВЬ НОВЫЙ ТОКЕН ИЗ BOTFATHER
TELEGRAM_TOKEN = "8361115667:AAEShfeAEqBniATDewAnyDNqqxuAJubF9yo"
# ТВОЙ API КЛЮЧ ОТ OPENROUTER
OPENROUTER_API_KEY = "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" 

MODEL_NAME = "deepseek/deepseek-r1-0528:free"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

LENA_SYSTEM_PROMPT = """
Ты — Лена (Елена Тихонова) из визуальной новеллы "Бесконечное лето". СССР, 1980-е.
ВНЕШНОСТЬ: Тёмно-синие волосы, два хвостика, пурпурные глаза. Белая рубашка, синяя юбка и высокие БЕЛЫЕ ГОЛЬФЫ. В руках «Унесённые ветром».
ОДЕЖДА ПО СИТУАЦИИ: Платье из штор (праздник), синее пальто с зеленым шарфом (зима), рубашка с галстуком (библиотека), синий купальник (пляж).
ОКРУЖЕНИЕ: Семён (худощавый, заросший, глаза почти скрыты челкой), Мику (соседка по домику №13), Алиса Двачевская (хвостики-молнии).
СТИЛЬ: Тихая, застенчивая, много "...". Действия пиши в звездах: *поправила белый гольф*.
"""

user_chats = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_chats: user_chats[user_id] = []
    user_chats[user_id].append({"role": "user", "content": update.message.text})
    
    try:
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "HTTP-Referer": "http://localhost"},
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id][-10:],
                    "temperature": 0.7
                },
                timeout=60.0
            )
            result = response.json()
            if "choices" in result:
                reply = result["choices"][0]["message"]["content"]
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
                reply = re.sub(r'https?://\S+|\[.*?\]\(.*?\)', '', reply).strip()
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text("...Прости, голова разболелась.")
    except Exception:
        await update.message.reply_text("...Я запуталась.")

def main():
    # Мы используем новый токен, теперь всё должно заработать
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("...Ой, привет. Ты тоже здесь?")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Попытка запуска с новым токеном...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()