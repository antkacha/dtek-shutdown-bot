import requests
import json
import hashlib
import time
import os
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

ADDRESS = {
    "city": "Коцюбинське",
    "street": "Паризька",
    "house": "3"
}

API_URL = "https://www.dtek-krem.com.ua/api/shutdowns"
CHECK_INTERVAL = 60

bot = Bot(BOT_TOKEN)
last_hash = None

def get_data():
    r = requests.post(
        API_URL,
        json=ADDRESS,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15
    )
    r.raise_for_status()
    return r.json()

def make_hash(data):
    return hashlib.md5(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()

def format_message(data):
    if not data.get("shutdowns"):
        return "⚡ Відключень електроенергії не заплановано"

    text = (
        "⚡ *Графік відключень електроенергії*\n\n"
        f"📍 {ADDRESS['city']}, вул. {ADDRESS['street']}, буд. {ADDRESS['house']}\n\n"
    )

    for s in data["shutdowns"]:
        text += (
            f"🕒 *{s['date']}*\n"
            f"Від: {s['time_from']}\n"
            f"До: {s['time_to']}\n"
            f"Причина: {s.get('reason', '—')}\n\n"
        )

    return text

while True:
    try:
        data = get_data()
        h = make_hash(data)

        if h != last_hash:
            bot.send_message(
                chat_id=CHAT_ID,
                text=format_message(data),
                parse_mode="Markdown"
            )
            last_hash = h
            print("🔔 Изменения отправлены")
        else:
            print("⏳ Без изменений")

    except Exception as e:
        print("❌ Ошибка:", e)

    time.sleep(CHECK_INTERVAL)
