from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from apscheduler.triggers.cron import CronTrigger

import os
import asyncio
import logging

from router import router
from db.models import async_main
from scheduler import schedule
from workers import worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s"
)

async def main():

    await async_main()
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_TOKEN = os.getenv("API_TOKEN")

    logging.info("The environment variables have been received")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

    dp = Dispatcher()
    dp.include_router(router)

    logging.info("The bot was initialized and the router was added to the bot")

    worker.set_bot(bot)
    worker.set_api(API_TOKEN)

    logging.info("The worker was set up")

    await worker.restart_bot()
    schedule.add_job(worker.set_task, CronTrigger(minute="0,30"))

    logging.info("The task was added to the scheduler")

    schedule.start()
    await dp.start_polling(bot)

    logging.info("The bot is running")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')