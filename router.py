from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, Location
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
import kb
from states import *
import db.requests as db
from scheduler import schedule
from workers import worker

extractor = worker.extractor
router = Router()

# @router.message(CommandStart())
# async def cmd_start(message: Message, state: FSMContext):
#     await state.set_state(GetLocation.waiting_for_location)
#     answer = await message.answer(text=f"""Привет, {message.from_user.first_name}!
#         Это бот с прогнозами погоды. Что ты хочешь сделать?""", reply_markup=kb.start_actions)
#     await state.update_data(waiting_for_location = answer.message_id)

# @router.message(GetLocation.waiting_for_location, F.location)
# async def cmd_start(message: Message, state: FSMContext):
#     data = await state.get_data()
#     if data['waiting_for_location']:
#         await message.bot.delete_message(message.chat.id, data['waiting_for_location'])
#     state.clear()
#     latitude = message.location.latitude
#     longitude = message.location.longitude
#     await message.answer(f"Геопозиция получена!\n{latitude}\n{longitude}")

@router.message(StateFilter(None), F.text == "Начать")
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(States.start)
    await message.answer(f"Что ты хочешь сделать?", reply_markup=kb.start_actions)            

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        _, user = await db.get_schedule_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer(f"""Привет, {message.from_user.first_name}!
Это бот с прогнозами погоды. Передайте ваши координаты, чтобы мы могли предоставлять данные о погоде.""", reply_markup=kb.start_cmd)            
        else:
            await state.set_state(States.start)
            answer = await message.answer(text=f"""Привет, {message.from_user.first_name}!
Это бот с прогнозами погоды. Что ты хочешь сделать?""", reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

@router.message(States.start, F.location)
async def add_loc(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    try:
        await db.add_user(telegram_id=message.from_user.id, latitude=latitude, longitude=longitude)
        await message.answer(f"Геопозиция получена!\nШирота: {latitude}\nДолгота: {longitude}\nВаши данные успешно добавлены.", 
                             reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.start_actions)

# ----------------------------------------

@router.message(States.start, F.text == "Показать погоду")
async def show_weather(message: Message, state: FSMContext):
    try:
        latitude, longitude = await db.get_coordinate(telegram_id=message.from_user.id)
        if latitude is not None and longitude is not None:
            temp = extractor.get_temp(latitude, longitude)
            await message.answer(f"Сейчас на улице {temp}°C.", 
                                reply_markup=kb.start_actions)
        else:
            await message.answer(f"У нас нет ваших данных, дайте нам ваше местоположение.", 
                                reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

@router.message(States.start, F.text == "Вернуться")
async def pos_start(message: Message, state: FSMContext):
    try:
        _, user = await db.get_schedule_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("Передайте ваши координаты, чтобы мы могли предоставлять данные о погоде.", reply_markup=kb.start_cmd)            
        else:
            await state.set_state(States.start)
            answer = await message.answer(text=f"Что ты хочешь сделать?", reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

# ----------------------------------------

@router.message(States.start, F.text == "Редактировать расписание")
async def edit_schedule(message: Message, state: FSMContext):
    await state.set_state(States.editing_schedule)
    answer = await message.answer("Что необходимо отредактировать?", reply_markup=kb.schedule_actions)
    
# ----------------------------------------

@router.message(States.editing_schedule, F.text == "Посмотреть расписание")
async def show_schedule(message: Message, state: FSMContext):
    try:
        text, _ = await db.get_schedule_for_user(telegram_id=message.from_user.id)
        await state.set_state(States.start)
        await message.answer(text, reply_markup=kb.start_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

# ----------------------------------------

@router.message(States.editing_schedule, F.text == "Добавить время уведомления")
async def add_time(message: Message, state: FSMContext):
    try:
        _, user = await db.get_schedule_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("У нас нет ваших данных, мы не можем формировать расписание.", reply_markup=kb.start_actions)            
        else:
            await state.set_state(setTime.hour)
            answer = await message.answer("Напишите час, когда необходимо уведомлять о погоде.")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

@router.message(setTime.hour)
async def add_hour(message: Message, state: FSMContext):
    try:
        hour = int(message.text)
        if hour >= 0 and hour <= 23:
            await state.update_data(hour=hour)
            await state.set_state(setTime.minute)
            await message.answer("Принято, теперь укажите минуту.")
        else:
            await message.answer("Часы должны находиться в диапазоне от 0 до 23. Повторите попытку.")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

# @router.message(setTime.minute, F.text == "Вернуться")
# async def return_cmd(message: Message, state: FSMContext):
#     await state.set_state(States.start)
#     answer = await message.answer(text=f"Что ты хочешь сделать?", reply_markup=kb.start_actions)

@router.message(setTime.minute)
async def add_minute(message: Message, state: FSMContext):
    try:
        minute = int(message.text)
        if minute >= 0 and minute <= 59:
            await state.update_data(minute=minute)
            data = await state.get_data()
            hour = data["hour"]
            minute = data["minute"]
            if len(str(minute)) == 1:
                str_min = f"0{minute}"
            else:
                str_min = f"{minute}"
            await db.add_schedule_for_user(telegram_id=message.from_user.id, hour=hour, minute=minute)
            await state.set_state(States.start)
            await message.answer("Время уведомления успешно добавлено. Уведомления будут приходить в " +
            f"{hour}:{str_min}.", reply_markup=kb.after_add_actions)

            await worker.set_in_moment_task(schedule=schedule, 
                                      user=message.from_user.id,
                                      hour=hour,
                                      minute=minute)
        else:
            await message.answer("Минуты должны находиться в диапазоне от 0 до 59. Повторите попытку.")
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

# ----------------------------------------

@router.message(States.editing_schedule, F.text == "Удалить данные")
async def delete_schedule(message: Message, state: FSMContext):
    try:
        _, user = await db.get_schedule_for_user(telegram_id=message.from_user.id)
        if not user:
            await state.set_state(States.start)
            await message.answer("У вас нет расписания.", reply_markup=kb.start_actions)            
        else:
            await state.set_state(States.deleting_schedule)
            answer = await message.answer("Вы действительно хотите удалить расписание?", reply_markup=kb.delete_schedule_actions)
    except:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)   

@router.message(States.editing_schedule, F.text == "Отмена")
async def return_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    answer = await message.answer(text=f"Действие отменено.", reply_markup=kb.after_add_actions)

@router.message(States.deleting_schedule, F.text == "Да")
async def yes_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    try:
        await db.delete_user_relations(telegram_id=message.from_user.id)
        answer = await message.answer("Расписание удалено.", reply_markup=kb.after_add_actions)
    except Exception as e:
        await state.set_state(States.start)
        await message.answer("Что-то пошло не так. Повторите попытку.", reply_markup=kb.after_add_actions)

@router.message(States.deleting_schedule, F.text == "Нет")
async def no_cmd(message: Message, state: FSMContext):
    await state.set_state(States.start)
    answer = await message.answer(text=f"Действие отменено.", reply_markup=kb.after_add_actions)

# ----------------------------------------