from aiogram.fsm.state import State, StatesGroup

class BinLookupState(StatesGroup):
    waiting_for_bin = State()