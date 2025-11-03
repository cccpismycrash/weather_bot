import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv 
import os

from router import router
from db.models import async_main
from scheduler import schedule
from workers import worker

async def main():

    await async_main()
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_TOKEN = os.getenv("API_TOKEN")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    worker.set_bot(bot)
    worker.set_api(API_TOKEN)
    await worker.restart_bot()
    schedule.add_job(worker.set_daily_tasks, trigger='cron', hour=0, minute=0, args=(schedule,))
    schedule.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')