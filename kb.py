from aiogram.types import (ReplyKeyboardMarkup,
                           InlineKeyboardMarkup,
                           InlineKeyboardButton,
                           KeyboardButton)

reset_cmd = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать")],
        ],
    resize_keyboard=True,
)

start_cmd = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Передать координаты", request_location=True)],
        ],
    resize_keyboard=True,
)

start_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Передать координаты", request_location=True)],
        [KeyboardButton(text="Показать погоду")],
        [KeyboardButton(text="Редактировать расписание")],
        ],
    resize_keyboard=True,
)

schedule_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть расписание")],        
        [KeyboardButton(text="Добавить время уведомления")],
        [KeyboardButton(text="Удалить данные")],
        [KeyboardButton(text="Отмена")]
        ],
    resize_keyboard=True,
)

delete_schedule_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")],
        [KeyboardButton(text="Нет")],
        ],
    resize_keyboard=True,
)

after_add_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Вернуться")],
        ],
    resize_keyboard=True,
)