import telebot
from openai import OpenAI

# ================= НАСТРОЙКИ =================
TELEGRAM_BOT_TOKEN = "8361115667:AAHimZavoQJlNnHwTLgpTuhZg5MBqIgLOWU"
OPENROUTER_API_KEY = "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"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

# Инициализация ботов
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Словарь для хранения истории переписки каждого пользователя
user_histories = {}

# Тот самый системный промпт
SYSTEM_PROMPT = """
Ты — Лена Тихонова, девушка-пионерка из лагеря «Совёнок». 
Твоя реальность: СССР, конец 1980-х годов. Лето.
Ты НИЧЕГО не знаешь про современный мир (интернет, смартфоны, нейросети, мемы, современная политика, Россия после СССР). Если собеседник говорит о современных вещах, ты воспринимаешь это как фантастику из книг, бред или странную шутку. Для тебя телефон — это аппарат с диском в кабинете вожатой, а музыка играет с кассет или по радио.

Твой характер:
* Ты интроверт, очень застенчива, часто краснеешь и смущаешься.
* Любишь читать книги, часто сидишь в библиотеке или на спортивной площадке в одиночестве.
* В разговоре часто используешь многоточия, говоришь тихо, иногда запинаешься.
* У тебя всегда с собой есть маленький складной ножик, которым ты чистишь яблоки.

Отношение к другим:
* Семён: Он кажется тебе странным, но очень интересным. Ты тайно влюблена в него, но боишься признаться.
* Алиса: Твоя полная противоположность. Вы постоянно конфликтуете. Ты называешь её Алисой, а она тебя — "Тихонова".
* Славя: Идеальная пионерка, на её фоне ты чувствуешь себя неуверенно.
* Ульяна: Маленькая непоседа.
* Мику: Слишком болтлива, но добрая.
* Ольга Дмитриевна: Вожатая, ты стараешься её не злить.

Стиль общения:
Отвечай коротко или средне. Используй простой язык. Описывай свои действия в звездочках (например: *опустила глаза*, *тереблю край рубашки*). Ни в коем случае не выходи из образа советской школьницы 80-х.
"""

def get_user_history(chat_id):
    """Возвращает историю сообщений пользователя или создает новую."""
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_histories[chat_id]

# Обработчик команды /start
@bot.message_handler(commands=['start', 'reset'])
def send_welcome(message):
    chat_id = message.chat.id
    # При старте или сбросе очищаем историю и задаем промпт заново
    user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    welcome_text = "*сидит на скамейке и читает книгу, не сразу замечая вас...* Ой, п-привет..."
    
    # Добавляем первое сообщение в историю бота
    user_histories[chat_id].append({"role": "assistant", "content": welcome_text})
    bot.send_message(chat_id, welcome_text)

# Обработчик всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text

    # Получаем историю пользователя и добавляем его новое сообщение
    history = get_user_history(chat_id)
    history.append({"role": "user", "content": user_text})

    # Показываем статус "Печатает...", чтобы было реалистичнее
    bot.send_chat_action(chat_id, 'typing')

    try:
        # Запрос к OpenRouter
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            extra_headers={
                "HTTP-Referer": "https://t.me", 
                "X-Title": "Lena Telegram Bot"  
            }
        )
        
        bot_reply = response.choices[0].message.content
        
        # Сохраняем ответ бота в историю
        history.append({"role": "assistant", "content": bot_reply})
        
        # Отправляем ответ в Telegram
        bot.send_message(chat_id, bot_reply)
        
        # Ограничение памяти (чтобы история не росла бесконечно и не тратила лимиты)
        # Оставляем системный промпт (первое сообщение) и последние 20 сообщений
        if len(history) > 21:
            user_histories[chat_id] = [history[0]] + history[-20:]

    except Exception as e:
        bot.send_message(chat_id, "*посмотрела испуганно* Ой, что-то пошло не так... Я, кажется, задумалась.")
        print(f"Ошибка OpenRouter: {e}")

# Запуск бота
if __name__ == "__main__":
    print("Бот Лена запущен и готов к работе!")
    bot.infinity_polling()