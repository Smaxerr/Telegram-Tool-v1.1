from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍Advanced BIN Lookup", callback_data="BINlookup")
    kb.button(text="⚡OvO Charger", callback_data="ovo_charger")
    kb.button(text="🧹Card Formatter", callback_data="ccformatter")
    kb.button(text="🔢 CC Count Checker", callback_data="bincountchecker")
    kb.button(text="⚙️Settings", callback_data="settings")
    kb.adjust(1)  # Each button takes 1 row
    return kb.as_markup()

def back_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Back to Main Menu", callback_data="back_main")
    return kb.as_markup()
