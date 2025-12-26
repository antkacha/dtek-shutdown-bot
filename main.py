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

# ====== Получение CSRF и куки ======
async def get_csrf_and_cookies():
    url = "https://www.dtek-krem.com.ua/ua/shutdowns"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            cookies = resp.cookies
            csrf = cookies.get("_csrf-dtek-krem").value if "_csrf-dtek-krem" in cookies else None
            return csrf, cookies

# ====== Запрос графика через AJAX ======
async def fetch_schedule(session, csrf, cookies_dict):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.dtek-krem.com.ua",
        "Referer": "https://www.dtek-krem.com.ua/ua/shutdowns",
        "X-CSRF-Token": csrf
    }
    data = {"_csrf": csrf, "address": ADDRESS}

    async with session.post(DTEK_URL, headers=headers, data=data, cookies=cookies_dict) as resp:
        json_data = await resp.json()

        # ===== Безопасная обработка графика =====
        schedule_list = json_data.get("schedule") or json_data.get("data") or []

        if not isinstance(schedule_list, list):
            temp_list = []
            if isinstance(schedule_list, dict):
                for k, v in schedule_list.items():
                    if isinstance(v, dict):
                        date = str(k)
                        time_range = str(v.get("time", ""))
                        temp_list.append({"date": date, "time": time_range})
            schedule_list = temp_list

        result = ""
        for item in schedule_list:
            date = str(item.get("date", ""))
            time_range = str(item.get("time", ""))
            result += f"{date} — {time_range}\n"

        return result or "График пустой или не найден."

# ====== Проверка графика и уведомление ======
async def check_schedule():
    global last_schedule
    csrf, cookies = await get_csrf_and_cookies()
    
    # преобразуем куки в простой словарь
    cookies_dict = {k: v.value for k, v in cookies.items()}

    async with aiohttp.ClientSession() as session:
        try:
            schedule = await fetch_schedule(session, csrf, cookies_dict)
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
