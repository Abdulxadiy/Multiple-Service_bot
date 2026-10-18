from aiogram.fsm.state import State, StatesGroup

class ReminderState(StatesGroup):
    waiting_for_content = State()
    waiting_for_voice_confirm = State()
    waiting_for_edit_content = State()
    waiting_for_time = State()
    waiting_for_repeat = State()
    waiting_for_custom_snooze = State()
