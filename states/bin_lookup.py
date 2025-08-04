from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class ccformatterstate(StatesGroup):
    ccformatter = State()

class BinLookupState(StatesGroup):
    waiting_for_bin = State()

class RoyalMailStates(StatesGroup):
    awaiting_cards = State()

