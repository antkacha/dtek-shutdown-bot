import os
import asyncio
import aiohttp
from telegram import Bot

# ====== НАСТРОЙКИ ======
TOKEN = os.getenv("BOT_TOKEN")      # токен бота
CHAT_ID = int(os.getenv("CHAT_ID")) # ваш Chat ID
ADDRESS = "с-ще Коцюбинське, вулиця Паризька, будинок 3"
DTEK_URL = "https://www.dtek-krem.com.ua/ua/ajax"
CHECK_INTERVAL = 60  # проверка каждые 60 секунд

bot = Bot(token=TOKEN)
last_schedule = ""  # хранение предыдущего графика

# ====== Функция получения CSRF и куки ======
async def get_csrf_and_cookies():
    url = "https://www.dtek-krem.com.ua/ua/shutdowns"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            cookies = resp.cookies
            # CSRF обычно хранится в cookie "_csrf-dtek-krem"
            csrf = cookies.get("_csrf-dtek-krem").value if "_csrf-dtek-krem" in cookies else None
            return csrf, cookies

# ====== Функция запроса графика через AJAX ======
async def fetch_schedule(session, csrf, cookies):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.dtek-krem.com.ua",
        "Referer": "https://www.dtek-krem.com.ua/ua/shutdowns",
        "X-CSRF-Token": csrf
    }
    data = {
        "_csrf": csrf,
        "address": ADDRESS
    }

    async with session.post(DTEK_URL, headers=headers, data=data, cookies=cookies) as resp:
        json_data = await resp.json()
        # В json_data ищем график
        schedule_list = json_data.get("schedule", [])
        if not schedule_list:
            return "График пустой или не найден."
        result = ""
        for item in schedule_list:
            date = item.get("date", "")
            time_range = item.get("time", "")
            result += f"{date} — {time_range}\n"
        return result

# ====== Функция проверки и уведомления ======
async def check_schedule():
    global last_schedule
    csrf, cookies = await get_csrf_and_cookies()
    async with aiohttp.ClientSession() as session:
        try:
            schedule = await fetch_schedule(session, csrf, cookies)
            if schedule != last_schedule:
                await bot.send_message(chat_id=CHAT_ID, text="🔔 График отключений обновился:\n" + schedule)
                last_schedule = schedule
        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка при проверке графика: {e}")
    # планируем следующую проверку
    await asyncio.sleep(CHECK_INTERVAL)
    asyncio.create_task(check_schedule())

# ====== Старт бота ======
async def main():
    await bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен. Следим за графиком отключений...")
    asyncio.create_task(check_schedule())
    while True:
        await asyncio.sleep(10)  # держим цикл живым

if __name__ == "__main__":
    asyncio.run(main())
