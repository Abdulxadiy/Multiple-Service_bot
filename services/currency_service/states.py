from aiogram.fsm.state import State, StatesGroup

class CurrencyState(StatesGroup):
    waiting_for_convert_input = State()
