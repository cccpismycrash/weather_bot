from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, Location
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter

import logging

from states import *
from workers import worker

import db.requests as db
import kb

extractor = worker.extractor
router = Router()


@router.message(StateFilter(None), F.text == "Начать")
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(States.start)
    await message.answer(f"""Что ты хочешь сделать?
                         
*Вы можете:*
  _1. Передать новое местоположение, предыдущее местоположение будет удалено._
  _2. Посмотреть погоду по своему местоположению._
  _3. Настроить себе уведомления при резкой смене температуры в вашем городе. Ваш город определяется, исходя из вашего местоположения._""", reply_markup=kb.start_actions)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        _, user = await db.get_notification_config_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer(f"""Привет, {message.from_user.first_name}!
Это бот с прогнозами погоды. Передайте ваши координаты, если вы ранее их не передавали, чтобы мы могли предоставлять данные о погоде.

*Вы можете:*
  _1. Передать новое местоположение, предыдущее местоположение будет удалено._
  _2. Посмотреть погоду по своему местоположению._
  _3. Настроить себе уведомления при резкой смене температуры в вашем городе. Ваш город определяется, исходя из вашего местоположения._""", reply_markup=kb.start_cmd)            
        else:
            await state.set_state(States.start)
            answer = await message.answer(text=f"""Привет, {message.from_user.first_name}!
Это бот с прогнозами погоды. Что ты хочешь сделать?

*Вы можете:*
  _1. Передать новое местоположение, предыдущее местоположение будет удалено._
  _2. Посмотреть погоду по своему местоположению._
  _3. Настроить себе уведомления при резкой смене температуры в вашем городе. Ваш город определяется, исходя из вашего местоположения._""", reply_markup=kb.start_actions)
        logging.info(f"The message \"/start\" was received from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.start, F.location)
async def add_loc(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    try:
        await db.add_user(telegram_id=message.from_user.id, latitude=latitude, longitude=longitude)
        await message.answer(f"Геопозиция получена!\n_Широта:_ {latitude}\n_Долгота:_ {longitude}\nВаши данные успешно добавлены.", 
                             reply_markup=kb.start_actions)
        logging.info(f"The coordinates were successfully transmitted from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.start_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.start, F.text == "Показать погоду")
async def show_weather(message: Message, state: FSMContext):
    try:
        latitude, longitude = await db.get_coordinate(telegram_id=message.from_user.id)
        if latitude is not None and longitude is not None:
            temp = await extractor.get_temp(latitude, longitude)
            await message.answer(f"Сейчас на улице *{temp}°C.*", 
                                reply_markup=kb.start_actions)
            logging.info(f"Successful request for a weather from {message.from_user.id} ID")
        else:
            await message.answer(f"У нас нет ваших данных, дайте нам ваше местоположение.", 
                                reply_markup=kb.start_actions)
            logging.warning(f"Failed request for a weather from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.start, F.text == "Вернуться")
async def pos_start(message: Message, state: FSMContext):
    try:
        _, user = await db.get_notification_config_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("Передайте ваши координаты, чтобы мы могли предоставлять данные о погоде.", reply_markup=kb.start_cmd)            
        else:
            await state.set_state(States.start)
            answer = await message.answer(text=f"Что ты хочешь сделать?", reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.start, F.text == "Управление уведомлениями")
async def edit_notifications(message: Message, state: FSMContext):
    await state.set_state(States.editing_notification)
    answer = await message.answer("Что необходимо отредактировать?", reply_markup=kb.notification_actions)


@router.message(States.editing_notification, F.text == "Посмотреть уведомления")
async def show_notifications(message: Message, state: FSMContext):
    try:
        text, _ = await db.get_notification_config_for_user(telegram_id=message.from_user.id)
        await state.set_state(States.start)
        await message.answer(text, reply_markup=kb.start_actions)
        logging.info(f"Successful request to display notification settings from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.editing_notification, F.text == "Добавить уведомление")
async def add_difference(message: Message, state: FSMContext):
    try:
        _, user = await db.get_notification_config_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("У нас нет ваших данных, мы не можем добавлять уведомления. Предоставьте ваши координаты.", reply_markup=kb.start_actions)            
        else:
            await state.set_state(setConfig.diff)
            answer = await message.answer("Напишите, насколько должна изменяться температура, чтобы уведомить Вас _(например, 5.2 или 8)_.")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(setConfig.diff)
async def add_frequency(message: Message, state: FSMContext):
    try:
        diff = float(message.text)
        if diff >= -20 and diff <= 20:
            await state.update_data(diff=diff)
            await state.set_state(setConfig.freq)
            await message.answer("Принято, теперь укажите временной промежуток, за который должна изменяться температура.", reply_markup=kb.set_options)
            logging.info(f"Successful request to transmit the temperature difference from {message.from_user.id} ID")
        else:
            await message.answer("Необходимо указать разницу температур целым числом или десятичной дробью через точку в диапазоне от *-20* до *20* градусов. Повторите попытку.")
            logging.warning(f"Failed request to transmit the temperature difference from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(setConfig.freq)
async def add_notofication(message: Message, state: FSMContext):
    try:
        text = message.text
        match text:
            case "30 минут":
                freq = 1
            case "1 час":
                freq = 2
            case "2 часа":
                freq = 4
            case "4 часа":
                freq = 8
            case "8 часов":
                freq = 16
            case "24 часа":
                freq = 48
            case _:        
                raise Exception()
    
        await state.update_data(freq=freq)
    
        logging.info(f"Successful request to transmit the frequency from {message.from_user.id} ID")

        data = await state.get_data()
        freq = data["freq"]
        diff = data["diff"]

        lat, lon = await db.get_coordinate(message.from_user.id)

        users_temp, city_name = await extractor.get_temp_with_city_name(lat, lon)

        await db.delete_user_relations(message.from_user.id)

        await db.set_config(telegram_id=message.from_user.id,
                            frequency=freq,
                            diff_temp=diff,
                            users_temp=users_temp,
                            city_name=city_name)

        city_name_ru, city_latitude, city_longitude = await extractor.get_coord(city_name=city_name)

        city_temp = await extractor.get_temp(city_latitude, city_longitude)

        await db.update_city_data(city_name=city_name,
                                  city_name_ru=city_name_ru,
                                  latitude=city_latitude,
                                  longitude=city_longitude,
                                  city_temp=city_temp)

        await state.set_state(States.start)
        await message.answer("Принято, температура проверяется каждые полчаса.", reply_markup=kb.after_add_actions)
        logging.info(f"Successful request to updating data and relationships in the database from {message.from_user.id} ID")

    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.editing_notification, F.text == "Удалить данные")
async def delete_notofications(message: Message, state: FSMContext):
    try:
        _, user = await db.get_notification_config_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("У вас нет уведомлений.", reply_markup=kb.start_actions)
        else:
            await state.set_state(States.deleting_notification)
            answer = await message.answer("Вы действительно хотите удалить уведомления?", reply_markup=kb.delete_notification_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.editing_notification, F.text == "Отмена")
async def return_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    answer = await message.answer(text=f"Действие отменено.", reply_markup=kb.after_add_actions)


@router.message(States.deleting_notification, F.text == "Да")
async def yes_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    try:
        await db.delete_user_data(telegram_id=message.from_user.id)
        answer = await message.answer("Уведомления удалены.", reply_markup=kb.after_add_actions)
        logging.info(f"Successful request to deleting data and relationships in the database from {message.from_user.id} ID")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)
        logging.error(f"An error was received\n{e}")


@router.message(States.deleting_notification, F.text == "Нет")
async def no_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    answer = await message.answer(text=f"Действие отменено.", reply_markup=kb.after_add_actions)