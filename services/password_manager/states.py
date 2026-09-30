from aiogram.fsm.state import State, StatesGroup

class CategoryStates(StatesGroup):
    waiting_for_category_name = State()

class AccountAddStates(StatesGroup):
    category_id = State()
    waiting_for_title = State()
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_note = State()

class PINSetupStates(StatesGroup):
    waiting_for_new_pin = State()
    waiting_for_confirm_pin = State()

class PINVerifyStates(StatesGroup):
    account_id = State()
    waiting_for_pin = State()

class PINChangeStates(StatesGroup):
    waiting_for_old_pin = State()
    waiting_for_new_pin = State()
    waiting_for_confirm_new_pin = State()

class PINRecoveryStates(StatesGroup):
    waiting_for_recovery_code = State()
    waiting_for_sample_cred = State()
    waiting_for_new_pin = State()
    waiting_for_confirm_new_pin = State()

class AccountEditStates(StatesGroup):
    account_id = State()
    waiting_for_field_choice = State()
    waiting_for_new_value = State()
