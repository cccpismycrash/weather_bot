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
        [KeyboardButton(text="Управление уведомлениями")],
        ],
    resize_keyboard=True,
)


set_options = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="30 минут"), KeyboardButton(text="1 час")],
        [KeyboardButton(text="2 часа"), KeyboardButton(text="4 часа")],
        [KeyboardButton(text="8 часов"), KeyboardButton(text="24 часа")],
        ],
    resize_keyboard=True,
)


notification_actions = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть уведомления")],        
        [KeyboardButton(text="Добавить уведомление")],
        [KeyboardButton(text="Удалить данные")],
        [KeyboardButton(text="Отмена")]
        ],
    resize_keyboard=True,
)


delete_notification_actions = ReplyKeyboardMarkup(
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