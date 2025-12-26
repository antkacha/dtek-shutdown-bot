import requests
import json
import hashlib
import time
import os
import re
from telegram import Bot

# --- Переменные окружения ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Не установлены BOT_TOKEN или CHAT_ID")

bot = Bot(BOT_TOKEN)

# --- Настройки DTEK ---
ADDRESS = {
    "address": "с-ще Коцюбинське, вулиця Паризька, будинок 3"
}
MAIN_PAGE_URL = "https://www.dtek-krem.com.ua/ua/shutdowns"
API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"
CHECK_INTERVAL = 60  # проверка каждые 60 секунд
last_hash = None

# --- Получение данных с сайта DTEK с куками и CSRF ---
def get_data():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        # Получаем главную страницу и куки
        r = session.get(MAIN_PAGE_URL, timeout=15)
        if r.status_code != 200:
            print("❌ Не удалось получить страницу, статус:", r.status_code)
            return {}

        # Извлекаем CSRF-токен
        match = re.search(r'name="__RequestVerificationToken" value="(.+?)"', r.text)
        csrf_token = match.group(1) if match else None
        if not csrf_token:
            print("❌ CSRF токен не найден")
            return {}

        # Делаем POST с токеном и куками
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token
        }
        r_post = session.post(API_URL, json=ADDRESS, headers=headers, timeout=15)

        try:
            data = r_post.json()
            return data
        except json.JSONDecodeError:
            print("❌ Сервер вернул невалидный JSON:", r_post.text[:200])
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

# --- Основной цикл ---
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
