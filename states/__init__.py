# states/bin_lookup_state.py
from aiogram.fsm.state import StatesGroup, State

class BinLookupState(StatesGroup):
    waiting_for_bin = State()
