from aiogram.fsm.state import State, StatesGroup

class FinanceState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_wallet = State()
    waiting_for_category = State()
    waiting_for_new_category_name = State()
    waiting_for_note = State()
    waiting_for_wallet_name = State()
    waiting_for_set_balance = State()
    waiting_for_category_rename = State()
    waiting_for_new_cat_manual_name = State()
