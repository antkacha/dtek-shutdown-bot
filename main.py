import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ====== НАСТРОЙКИ ======
TOKEN = "ВАШ_API_ТОКЕН"  # токен бота от BotFather
ADDRESS = "с-ще Коцюбинське, вулиця Паризька, будинок 3"
DTEK_URL = "https://www.dtek-krem.com.ua/ua/shutdowns"

# ====== ФУНКЦИЯ ПАРСИНГА ======
def get_shutdown_schedule(address):
    session = requests.Session()
    
    # Заголовки для имитации браузера
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # GET страница, чтобы получить cookies и csrf
    r = session.get(DTEK_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Можно добавить поиск CSRF-токена, если требуется форма
    csrf = soup.find("input", {"name": "_csrf"})
    csrf_token = csrf["value"] if csrf else ""

    # Отправка формы для поиска по адресу (примерный POST, структура может меняться)
    data = {
        "_csrf": csrf_token,
        "address": address
    }

    r2 = session.post(DTEK_URL, headers=headers, data=data)
    soup2 = BeautifulSoup(r2.text, "html.parser")

    # Пример парсинга таблицы графиков
    table = soup2.find("table")
    if not table:
        return "График не найден. Попробуйте проверить адрес."

    result = ""
    for row in table.find_all("tr")[1:]:  # пропускаем заголовок
        cols = row.find_all("td")
        date = cols[0].text.strip()
        time = cols[1].text.strip()
        result += f"{date} — {time}\n"
    
    return result or "График пустой."

# ====== ФУНКЦИИ БОТА ======
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот для отслеживания отключений света 💡\nИспользуй команду /status")

def status(update: Update, context: CallbackContext):
    update.message.reply_text("Ищу график отключений...")
    schedule = get_shutdown_schedule(ADDRESS)
    update.message.reply_text(schedule)

# ====== ЗАПУСК БОТА ======
updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("status", status))

updater.start_polling()
updater.idle()

