from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class BinLookupState(StatesGroup):
    waiting_for_bin = State()

class RoyalMailStates(StatesGroup):
    awaiting_cards = State()
