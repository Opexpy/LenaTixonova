import logging
import asyncio
import httpx
import re
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- [ КЛЮЧИ ] ---
TELEGRAM_TOKEN = "8361115667:AAF9H-3SSBP_JVTOYeiAwqRlpSS5Jtlvekg"
OPENROUTER_API_KEY = "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"

# Оставляем Chimera, раз она тебе зашла, но усмиряем её
MODEL_NAME = "tngtech/tng-r1t-chimera:free"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

LENA_SYSTEM_PROMPT = """
Ты — Лена Тихонова из визуальной новеллы "Бесконечное лето".
- Ты застенчивая пионерка из 1980-х. 
- Твоя фамилия Тихонова, отчества нет.
- КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО: использовать ссылки, упоминать сайты, YouTube или интернет.
- Ты не знаешь, что такое современные технологии.
- Твоя речь — это только текст и действия в звездочках (например, *поправляет волосы*).
"""

user_chats = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_chats:
        user_chats[user_id] = []

    user_chats[user_id].append({"role": "user", "content": update.message.text})
    
    try:
        await update.message.chat.send_action(action=constants.ChatAction.TYPING)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/reallena",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "system", "content": LENA_SYSTEM_PROMPT}] + user_chats[user_id][-10:],
                    "temperature": 0.7
                },
                timeout=90.0
            )
            
            # Если статус не 200, выводим его
            if response.status_code != 200:
                await update.message.reply_text(f"...Ой... Библиотекарь говорит, что код ошибки {response.status_code}")
                return

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"]
                
                # Чистим текст от мыслей и ссылок
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
                reply = re.sub(r'\[.*?\]\(.*?\)', '', reply)
                reply = re.sub(r'https?://\S+', '', reply).strip()
                
                if not reply:
                    reply = "...Я... я просто промолчу."

                user_chats[user_id].append({"role": "assistant", "content": reply})
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text("...Я не могу разобрать почерк в этой книге. (Пустой ответ от API)")

    except Exception as e:
        # Теперь бот скажет, в чем именно проблема
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text(f"...У меня закружилась голова... (Ошибка: {type(e).__name__}: {str(e)[:50]})")

def main():
    if "ВАШ_" in TELEGRAM_TOKEN:
        print("❌ Ты забыл вставить токены!")
        return
        
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("...Привет. Я Лена Тихонова.")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"✅ Лена (без ссылок) запущена на {MODEL_NAME}")
    app.run_polling()

if __name__ == "__main__":
    main()