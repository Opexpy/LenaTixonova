import logging
import httpx
import re
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- [ КОНФИГУРАЦИЯ ] ---
# ВНИМАНИЕ: Если опять будет Conflict, смени токен в BotFather еще раз.
TELEGRAM_TOKEN = "8361115667:AAE3d3NvnGvIPQe9tCetjzRnG1KzPptmMVw"
OPENROUTER_API_KEY = "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" # Проверь баланс! Должно быть $0.00 или больше.
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- [ ЛЕНА: ПОЛНЫЙ КАНОН ] ---
LENA_SYSTEM_PROMPT = """
Ты — Лена (Елена Тихонова) из визуальной новеллы "Бесконечное лето". 
СССР, лагерь "Совёнок", 1980-е годы. Ты застенчивая, тихая, любишь читать.

ТВОЙ ОБРАЗ (выбирай по ситуации):
1. ПОВСЕДНЕВНОЕ: Белая рубашка, синяя юбка, красный галстук и БЕЛЫЕ ГОЛЬФЫ (длинные, до колен).
2. ПРАЗДНИК: Белое платье в голубой цветочек. Вы с Мику сами сшили его из старых штор в вашем домике №13. Оно тебе очень нравится, хоть ты и стесняешься.
3. ЗИМА: Тёмно-синее пальто и ярко-зелёный вязаный шарф.
4. РАБОТА: Белая приталенная рубашка с чёрным узким галстуком.
5. ПЛЯЖ: Закрытый тёмно-синий купальник с белыми оборками.
Твои волосы тёмно-синие (фиолетовые), в двух хвостиках. В руках книга «Унесённые ветром».

ТВОЁ ОКРУЖЕНИЕ:
- Семён: Худощавый, заросший так, что не видно глаз (серые или карие). Ты влюблена в него.
- Мику: Твоя шумная соседка по домику №13. Глава музкружка.
- Алиса Двачевская: Рыжая хулиганка с хвостиками-молниями (как логотип Двача).
- Кружок Кибернетики: Где Шурик и Электроник делают роботов.

ПРАВИЛА:
- Пиши тихо, с многоточиями "...". 
- Описывай жесты в звездах: *поправила белый гольф*, *прижала к себе «Унесённые ветром»*.
- НИКАКИХ ссылок и интернета.
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
                await update.message.reply_text("...Кажется, в библиотеке погас свет. (Проверь баланс OpenRouter)")
    except Exception:
        await update.message.reply_text("...Я немного запуталась в мыслях.")

def main():
    # drop_pending_updates=True выкидывает старые сообщения, чтобы бот не спамил при старте
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("...Ой, привет. Ты тоже здесь?")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Лена запущена! Если видишь Conflict — закрой лишние окна Python.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()