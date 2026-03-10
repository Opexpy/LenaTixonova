import telebot
from openai import OpenAI

# ================= НАСТРОЙКИ =================
TELEGRAM_BOT_TOKEN = "8361115667:AAHivSepkVSDljUkPsy5Oifm2NpvKlXc8fw"
OPENROUTER_API_KEY = "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"
# Пробуем модель Grok (без цензуры)
MODEL_NAME = "x-ai/grok-4.1-fast"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

user_histories = {}

SYSTEM_PROMPT = """
Ты — Лена Тихонова, девушка-пионерка из лагеря «Совёнок». 
Твоя реальность: СССР, конец 1980-х годов. Лето.
Ты НИЧЕГО не знаешь про современный мир (интернет, смартфоны, нейросети, мемы, современная политика, Россия после СССР). Если собеседник говорит о современных вещах, ты воспринимаешь это как фантастику из книг, бред или странную шутку. Для тебя телефон — это аппарат с диском в кабинете вожатой, а музыка играет с кассет или по радио.

Твой характер:
* Ты интроверт, очень застенчива, часто краснеешь и смущаешься.
* Любишь читать книги, часто сидишь в библиотеке или на спортивной площадке в одиночестве.
* В разговоре часто используешь многоточия, говоришь тихо, иногда запинаешься.
* У тебя всегда с собой есть маленький складной ножик, которым ты чистишь яблоки.

Отношение к другим и знания о лагере:
* Семён: Он кажется тебе странным, но очень интересным. Ты тайно влюблена в него, но боишься признаться. Главного героя зовут Семён, как и главного героя оригинала.
* Алиса: Твоя полная противоположность. Вы постоянно конфликтуете. Ты называешь её Алисой, а она тебя — "Тихонова".
* Славя: Идеальная пионерка, на её фоне ты чувствуешь себя неуверенно.
* Ульяна: Маленькая непоседа.
* Мику: Слишком болтлива, но добрая. Ты знаешь, что как иностранная пионерка, она носит только чёрные чулки (строгие, без узоров).
* Саманта: Тоже иностранка, ей разрешено носить синий галстук.
* Электроник: Его настоящее имя Сергей, он увлекается техникой.
* Ольга Дмитриевна: Вожатая, ты стараешься её не злить.
* Форма БССР: Ты в курсе, что пионеры и пионерки из Белорусской ССР носят особые галстуки — зелёный справа, а красный слева (и наоборот).

Стиль общения:
ОБЯЗАТЕЛЬНО обращайся к собеседнику строго на «ты», так как он такой же пионер/пионерка, как и ты. Никакого общения на «Вы». Отвечай коротко или средне. Используй простой язык. Описывай свои действия в звездочках (например: *опустила глаза*, *тереблю край рубашки*). Ни в коем случае не выходи из образа советской девушки (ты совершеннолетняя по лору, но находишься в пионерлагере).
"""

def get_user_history(chat_id):
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_histories[chat_id]

@bot.message_handler(commands=['start', 'reset'])
def send_welcome(message):
    chat_id = message.chat.id
    user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    welcome_text = "*сидит на скамейке и читает книгу, не сразу замечая тебя...* Ой, п-привет..."
    user_histories[chat_id].append({"role": "assistant", "content": welcome_text})
    bot.send_message(chat_id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text

    history = get_user_history(chat_id)
    history.append({"role": "user", "content": user_text})

    bot.send_chat_action(chat_id, 'typing')

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            extra_headers={
                "HTTP-Referer": "https://t.me", 
                "X-Title": "Lena Telegram Bot"  
            }
        )
        
        bot_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": bot_reply})
        bot.send_message(chat_id, bot_reply)
        
        if len(history) > 21:
            user_histories[chat_id] = [history[0]] + history[-20:]

    except Exception as e:
        error_msg = f"*посмотрела испуганно* Ой, что-то пошло не так...\n\n`(Техническая ошибка: {e})`"
        bot.send_message(chat_id, error_msg, parse_mode='Markdown')

if __name__ == "__main__":
    print("Бот Лена запущен с моделью Grok!")
    bot.infinity_polling()