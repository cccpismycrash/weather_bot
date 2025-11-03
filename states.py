from aiogram.fsm.state import State, StatesGroup

class States(StatesGroup):
    start = State()
    waiting_for_location = State()
    editing_schedule = State()
    deleting_schedule = State()

class setTime(StatesGroup):
    hour = State()
    minute = State()