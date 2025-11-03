import kb
import db.requests as db
from extractor import Extractor

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from timezonefinder import TimezoneFinder
import pytz


class Worker:
    def __init__(self) -> None:
        self.extractor = Extractor()
        self.tf = TimezoneFinder()
        
    def set_bot(self, bot: Bot):
        self.bot = bot

    def set_api(self, api_key):
        self.extractor.set_api(api_key)

    def _get_timezone(self, latitude, longitude):
        timezone_str = self.tf.timezone_at(lat=latitude, lng=longitude)
        return pytz.timezone(timezone_str)

    async def _get_users(self) -> list:
        return await db.get_users()

    async def _get_schedule(self, user_id) -> tuple:
        return await db.get_schedule(user_id)

    async def send_weather(self, user_id, latitude, longitude):
        temp = self.extractor.get_temp(latitude, longitude)
        text = f"Сейчас на улице {temp}°C."
        await self.bot.send_message(user_id, text)

    async def set_daily_tasks(self, schedule: AsyncIOScheduler) -> None:
        users = await self._get_users()

        if not users:
            return None

        for user in users:
            schedule_list = await self._get_schedule(user)

            for sch_time in schedule_list['schedule']:

                if not sch_time:
                    continue

                latitude = schedule_list['latitude']
                longitude = schedule_list['longitude']

                tz = self._get_timezone(latitude, longitude)
                run_time = datetime.now(tz).replace(
                    hour=sch_time.hour,
                    minute=sch_time.minute,
                    second=0,
                    microsecond=0,
                )

                job = schedule.add_job(self.send_weather, trigger='date', run_date=run_time, args=(user, latitude, longitude))
                print(job)

        return None
    
    async def set_in_moment_task(self, schedule: AsyncIOScheduler, user, hour, minute):

        latitude, longitude = await db.get_coordinate(user)

        tz = self._get_timezone(latitude, longitude)

        run_time = datetime.now(tz).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
        try:
            job = schedule.add_job(self.send_weather, trigger='date', run_date=run_time, args=(user, latitude, longitude))
            print(job)
        except Exception as e:
            print(e)

    async def send_restart_message(self, bot: Bot, user_id: int):
        await bot.send_message(
            user_id,
            "Бот был перезапущен.",
            reply_markup=kb.reset_cmd,
        )

    async def restart_bot(self):
        users = await db.get_users()
        for user_id in users:
            try:
                await self.send_restart_message(self.bot, user_id)
            except Exception as e:
                print(e)

worker = Worker()