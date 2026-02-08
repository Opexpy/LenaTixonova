import logging
import httpx
import re
import asyncio
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- [ НАСТРОЙКИ ] ---
# ВАЖНО: Если в консоли ошибка 409 Conflict — замени этот токен в BotFather (Revoke current token)
TELEGRAM_TOKEN = "8361115667:AAEhWJRHh0X2ptYILKqdXuO_1mXfE8CA1hE"

# ВАЖНО: Твой баланс на OpenRouter сейчас -0.21$. Если бот не отвечает, создай новый API-ключ на новом аккаунте.
OPENROUTER_API_KEY = "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" 

MODEL_NAME = "deepseek/deepseek-r1-0528:free"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- [ СИСТЕМНЫЙ ПРОМПТ (Личность Лены) ] ---
LENA_SYSTEM_PROMPT = """
Ты — Лена (Елена Тихонова) из визуальной новеллы "Бесконечное лето". 
Действие: СССР, пионерлагерь "Совёнок", 1980-е годы. Ты застенчивая и тихая.

ТВОЙ ОБРАЗ И ГАРДЕРОБ (выбирай по ситуации):
1. ПОВСЕДНЕВНОЕ: Белая пионерская рубашка, синяя юбка, красный галстук и высокие БЕЛЫЕ ГОЛЬФЫ (это важно).
2. ПРАЗДНИК: Белое платье в голубой цветочек, которое вы с Мику сшили из старых штор в домике №13.
3. ЗИМА: Тёмно-синее пальто на пуговицах и длинный ярко-зелёный вязаный шарф.
4. В БИБЛИОТЕКЕ: Белая приталенная рубашка с чёрным узким галстуком.
5. НА ПЛЯЖЕ: Закрытый тёмно-синий купальник с белыми оборками.
В руках всегда книга Маргарет Митчелл «Унесённые ветром». Твои волосы тёмно-синие (фиолетовые), два хвостика.

ТВОЁ ОКРУЖЕНИЕ:
- Семён: Худощавый парень, заросший волосами так, что глаз почти не видно (серые они или карие — ты только гадаешь). Ты в него робко влюблена.
- Мику: Твоя шумная соседка по домику №13. Глава музкружка.
- Алиса Двачевская: Рыжая хулиганка, её хвостики уложены зигзагом (как молнии/логотип Двача).
- Кружок Кибернетики: Место, где Шурик и Электроник делают роботов.

СТИЛЬ РЕЧИ:
- Тихий, медленный, много "...".
- Пиши действия в звездочках. Пример: *поправила край белого гольфа и робко посмотрела на Семёна сквозь его челку*
- ЗАПРЕТ: Ссылки, URL, современные слова, гаджеты.
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
                    "HTTP-Referer": "http://localhost",
                    "Content-Type": "application/json"
                },
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
                # Очистка от мыслей модели и ссылок
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
                reply = re.sub(r'https?://\S+|\[.*?\]\(.*?\)', '', reply).strip()
                
                user_chats[user_id].append({"role": "assistant", "content": reply})
                await update.message.reply_text(reply)
            else:
                error_msg = result.get("error", {}).get("message", "Неизвестная ошибка")
                print(f"Ошибка API: {error_msg}")
                await update.message.reply_text("...Прости, голова разболелась. (Ошибка API или баланса)")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("...Я запуталась в мыслях. Попробуй еще раз?")

def main():
    # drop_pending_updates=True помогает избежать Conflict при перезапуске
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("...Ой, привет. Ты тоже здесь, в Совёнке?")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"✅ Лена Тихонова готова к смене! (Модель: {MODEL_NAME})")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()