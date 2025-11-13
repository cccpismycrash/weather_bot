from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    start = State()
    waiting_for_location = State()
    editing_notification = State()
    deleting_notification = State()


class setConfig(StatesGroup):
    freq = State()
    diff = State()