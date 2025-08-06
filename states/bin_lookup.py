from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class BinLookupState(StatesGroup):
    waiting_for_bin = State()

class OvoStates(StatesGroup):
    awaiting_cards = State()

class APITokenStates(StatesGroup):
    waiting_for_api_token = State()

class BINInterestStates(StatesGroup):
    waiting_for_bin_add = State()
    waiting_for_bin_remove = State()

class AutobuyStates(StatesGroup):
    waiting_for_autobuy_bin_add = State()
    waiting_for_autobuy_bin_remove = State()
