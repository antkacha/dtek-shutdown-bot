import requests
import json
import hashlib
import time
import os
from telegram import Bot

# --- Переменные окружения ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Не установлены BOT_TOKEN или CHAT_ID")

# --- Настройка Telegram ---
bot = Bot(BOT_TOKEN)

# --- Настройки DTEK ---
ADDRESS = {
    "address": "с-ще Коцюбинське, вулиця Паризька, будинок 3"
}
API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд

last_hash = None

# --- Функция получения данных с DTEK ---
def get_data():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json"
    })

    try:
        r = session.post(API_URL, json=ADDRESS, timeout=15)
        print("HTTP status:", r.status_code)
        if r.status_code != 200:
            print("❌ Сервер вернул статус", r.status_code)
            return {}

        # Безопасно парсим JSON
        try:
            data = r.json()
            return data
        except json.JSONDecodeError:
            print("❌ Сервер вернул невалидный JSON:", r.text[:200])
            return {}

    except requests.RequestException as e:
        print("❌ Ошибка запроса:", e)
        return {}

# --- Хеширование данных для отслеживания изменений ---
def make_hash(data):
    return hashlib.md5(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

# --- Форматирование сообщения для Telegram ---
def format_message(data):
    shutdowns = data.get("shutdowns")
    if not shutdowns:
        return "⚡ Відключень електроенергії не заплановано"

    text = (
        "⚡ *Графік відключень електроенергії*\n\n"
        f"📍 {ADDRESS['address']}\n\n"
    )
    for s in shutdowns:
        text += (
            f"🕒 *{s.get('date','—')}*\n"
            f"Від: {s.get('time_from','—')}\n"
            f"До: {s.get('time_to','—')}\n"
            f"Причина: {s.get('reason','—')}\n\n"
        )
    return text

# --- Основной цикл проверки ---
while True:
    data = get_data()
    if not data:
        print("⏳ Нет данных от сервера")
        time.sleep(CHECK_INTERVAL)
        continue

    h = make_hash(data)
    if h != last_hash:
        message = format_message(data)
        try:
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            print("🔔 Изменения отправлены")
        except Exception as e:
            print("❌ Ошибка отправки в Telegram:", e)
        last_hash = h
    else:
        print("⏳ Без изменений")

    time.sleep(CHECK_INTERVAL)
