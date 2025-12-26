import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time
import threading

# ====== НАСТРОЙКИ ======
TOKEN = "ВАШ_API_ТОКЕН"  # токен бота
CHAT_ID = "ВАШ_CHAT_ID"   # куда отправлять уведомления
ADDRESS = "с-ще Коцюбинське, вулиця Паризька, будинок 3"
DTEK_URL = "https://www.dtek-krem.com.ua/ua/shutdowns"
CHECK_INTERVAL = 60  # интервал проверки в секундах

bot = Bot(token=TOKEN)
last_schedule = ""  # сюда будем сохранять предыдущий график

# ====== ФУНКЦИЯ ПАРСИНГА ======
def get_shutdown_schedule(address):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # GET страница, чтобы получить cookies и csrf
    r = session.get(DTEK_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    
    csrf = soup.find("input", {"name": "_csrf"})
    csrf_token = csrf["value"] if csrf else ""

    data = {
        "_csrf": csrf_token,
        "address": address
    }

    r2 = session.post(DTEK_URL, headers=headers, data=data)
    soup2 = BeautifulSoup(r2.text, "html.parser")

    table = soup2.find("table")
    if not table:
        return "График не найден."

    result = ""
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        date = cols[0].text.strip()
        time_range = cols[1].text.strip()
        result += f"{date} — {time_range}\n"

    return result or "График пустой."

# ====== ФУНКЦИЯ ПРОВЕРКИ И ОТПРАВКИ ======
def check_schedule():
    global last_schedule
    try:
        schedule = get_shutdown_schedule(ADDRESS)
        if schedule != last_schedule:
            bot.send_message(chat_id=CHAT_ID, text="🔔 График отключений обновился:\n" + schedule)
            last_schedule = schedule
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"Ошибка при проверке графика: {e}")

    # Запланировать следующую проверку
    threading.Timer(CHECK_INTERVAL, check_schedule).start()

# ====== СТАРТ ======
bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен. Следим за графиком отключений...")

# Запуск проверки
check_schedule()

# Чтобы скрипт не завершался
while True:
    time.sleep(1)

