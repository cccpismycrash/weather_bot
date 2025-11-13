from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import logging

from extractor import Extractor

import db.requests as db
import kb


class Worker:

    def __init__(self) -> None:
        self.extractor = Extractor()

        
    def set_bot(self, 
                bot: Bot
                ) -> None:
        
        """
        Set bot at the Worker

        """

        self.bot = bot
        logging.info("The Bot was set at Worker")


    def set_api(self, 
                api_key: str
                ) -> None:
        
        """
        Set API key at the Worker

        """

        self.extractor.set_api(api_key)
        logging.info("The API key was set at Worker")


    async def send_weather(self, 
                           telegram_id: int, 
                           latitude: float, 
                           longitude: float
                           ) -> None:
        
        """
        Send message to certain user

        """

        temp = self.extractor.get_temp(latitude, longitude)
        text = f"Сейчас на улице *{temp}°C*."
        logging.info("The weather was sent to user")
        await self.bot.send_message(telegram_id, text)


    async def set_task(self) -> None:
        
        """
        Contains a task for weather monitoring

        """

        cities_id = await db.get_cities_id()

        if len(cities_id) == 0:
            return

        logging.info("The task for sending a weather message was started")

        for city_id, _ in cities_id:
            data = await db.get_city_data(city_id=city_id)
            old_temp = await db.get_city_temp(city_id)
            temp = await self.extractor.get_temp(data['latitude'], data['longitude'])
            await db.update_city_temp(city_id=city_id,temp=temp)
            subscribers = await db.get_city_subscribers_id(city_id=city_id)
            for sub_id in subscribers:
                user_data = await db.get_user_attrs(sub_id)
                if user_data['users_temp'] - user_data['diff_temp'] > temp:
                    await self.bot.send_message(
                        sub_id,
                        f"В городе резко похолодало!\n\n"
                        f"*{old_temp}°C* -> *{temp}°C*\n\n"
                        f"-------",
                        reply_markup=kb.reset_cmd,
                    )                    
                    await db.update_user_counter(sub_id, user_data['frequency'])
                    await db.update_user_temp(sub_id, temp)
                    logging.info(f"The trigger was triggered, the message was sent to the user with {sub_id} ID")
                elif user_data['users_temp'] + user_data['diff_temp'] < temp:
                    await self.bot.send_message(
                        sub_id,
                        f"В городе резко потеплело!\n\n"
                        f"*{old_temp}°C* -> *{temp}°C*\n\n"
                        f"-------",
                        reply_markup=kb.reset_cmd,
                    )                    
                    await db.update_user_counter(sub_id, user_data['frequency'])
                    await db.update_user_temp(sub_id, temp)
                    logging.info(f"The trigger was triggered, the message was sent to the user with {sub_id} ID")
                else:
                    await db.update_user_counter(sub_id, user_data['counter'] - 1)
                    logging.info(f"The user with {sub_id} ID counter was reduced")
                    if user_data['counter'] - 1 == 0:
                        await db.update_user_counter(sub_id, user_data['frequency'])
                        await db.update_user_temp(sub_id, temp)
                        logging.info(f"Counter was rebooted")
            
        logging.info("The task of monitoring the weather was set")


    async def send_restart_message(self, 
                                   bot: Bot, 
                                   user_id: int
                                   ) -> None:
        
        """
        Send reboot message to certain user

        """

        await bot.send_message(
            user_id,
            "*Бот был перезапущен.*",
            reply_markup=kb.reset_cmd,
        )
        

    async def restart_bot(self) -> None:

        """
        Send reboot message to users

        """

        users = await db.get_users_id()
        for user_id in users:
            try:
                await self.send_restart_message(self.bot, user_id)
                logging.info("The reboot message has been sent to users")
            except Exception as e:
                logging.error("Error sending message")


worker = Worker()