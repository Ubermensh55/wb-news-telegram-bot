from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue, CallbackQueryHandler
import requests
import logging

# === НАСТРОЙКИ ===
TOKEN = "7742580858:AAHWJYFLcIRGy01oEBhnKjjEy213ugcPtl0"
TGSTAT_API_TOKEN = "57399d94051368c10a651fad5f050843"

CATEGORIES = {
    "Внутренняя реклама": [
        ("FULLSTATS", "@fullstats"),
        ("Хогвартс маркетплейсов", "@mp_hogwarts"),
        ("Реклама и внешние каналы", "@ads_wb")
    ],
    "Операционные таблицы и файлы": [
        ("Семья на Маркетплейсах", "@familymp"),
        ("Market Guru WB", "@marketguru_wb"),
        ("никакой магии", "@homichwb"),
        ("WildCRM", "@wildcrm")
    ],
    "Личный опыт и блогинг": [
        ("Рыжий М", "@ryzhiy_market"),
        ("Маркетплейс Босс", "@mp_boss"),
        ("Ритейл Мама", "@retailmama")
    ]
}

KEYWORDS = ["таблица", "гайд", "лайфхак", "инструкция", "аналитика", "ошибка", "новое", "важно"]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === КОМАНДЫ ===
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Внутренняя реклама", callback_data='ads')],
        [InlineKeyboardButton("Операционные таблицы и файлы", callback_data='files')],
        [InlineKeyboardButton("Личный опыт и блогинг", callback_data='blog')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите категорию новостей:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    category_map = {
        'ads': "Внутренняя реклама",
        'files': "Операционные таблицы и файлы",
        'blog': "Личный опыт и блогинг"
    }
    category = category_map.get(query.data)
    messages = fetch_category_posts(category) if category else ["Неверный выбор."]

    for msg in messages:
        query.message.reply_text(msg)

def fetch_category_posts(category):
    messages = []
    for name, channel in CATEGORIES.get(category, []):
        try:
            url = f"https://api.tgstat.ru/channels/posts?token={TGSTAT_API_TOKEN}&channel={channel}&limit=3"
            res = requests.get(url)
            data = res.json()
            for post in data.get("items", []):
                text = post.get("text", "")
                link = post.get("url", "")
                if any(k in text.lower() for k in KEYWORDS):
                    messages.append(f"🔹 {name}:
{text[:300]}...
{link}")
        except Exception as e:
            logging.error(f"Ошибка при получении постов из {name}: {e}")
    return messages if messages else ["Нет свежих новостей."]

def news(update: Update, context: CallbackContext):
    start(update, context)

def scheduled_job(context: CallbackContext):
    chat_id = context.job.context
    for category in CATEGORIES:
        messages = fetch_category_posts(category)
        for msg in messages:
            context.bot.send_message(chat_id=chat_id, text=msg)

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(scheduled_job, interval=3600, first=0, context=chat_id)
    update.message.reply_text("Вы подписались на автоматическую рассылку новостей каждый час.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "/start — Приветствие и выбор категории
"
        "/news — Последние новости
"
        "/subscribe — Авторассылка каждый час
"
        "/help — Список команд"
    )

# === ЗАПУСК ===
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("news", news))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()