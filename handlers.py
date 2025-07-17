from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile
from config import ADMIN_IDS
from io import BytesIO
from keyboards import main_menu, back_menu
from database import register_user, get_balance, set_balance, add_balance, get_all_users
import io

router = Router()

@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    await register_user(msg.from_user.id, msg.from_user.username)
    balance = await get_balance(msg.from_user.id)
    user_name = msg.from_user.full_name or msg.from_user.username or "User"

    text = (
        f"🔐 Welcome to *CipherBot*, {user_name}.\n\n"
        f"💰 Your balance: £{balance}\n\n"
        "Type /help to begin."
    )
    await msg.answer(text, parse_mode="Markdown", reply_markup=main_menu())


@router.callback_query(F.data == "bin_lookup")
async def bin_lookup(cb: CallbackQuery):
    await cb.message.edit_text("🔍 Advanced BIN Lookup coming soon...", reply_markup=back_menu())

@router.callback_query(F.data == "ovo_charger")
async def ovo_charger(cb: CallbackQuery):
    await cb.message.edit_text("⚡ OvO Charger coming soon...", reply_markup=back_menu())

@router.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    balance = await get_balance(cb.from_user.id)
    username = cb.from_user.username or "NoUsername"
    
    text = (
        f"CipherBot 🛠️\n\n"
        f"Telegram: @{username}\n"
        f"Balance: £{balance}\n\n"
        f"Welcome back! Use the menu below to continue."
    )
    
    await cb.message.edit_text(text, reply_markup=main_menu())
    await cb.answer()  # optionally answer the callback to remove loading spinner


@router.message(F.text.startswith("/setbalance"))
async def set_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, uid, amount = msg.text.split()
        await set_balance(int(uid), int(amount))
        await msg.reply("✅ Balance set.")
    except:
        await msg.reply("❌ Usage: /setbalance <id> <amount>")

@router.message(F.text.startswith("/addbalance"))
async def add_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, uid, amount = msg.text.split()
        await add_balance(int(uid), int(amount))
        await msg.reply("✅ Balance added.")
    except:
        await msg.reply("❌ Usage: /addbalance <id> <amount>")

@router.message(F.text == "/viewusers")
async def view_users(msg: Message):
    users = await get_all_users()  # your function returning list of user dicts
    text = "\n".join(f"{u['id']} @{u['username']} £{u['balance']}" for u in users)

    # Convert to bytes (UTF-8) and wrap in BytesIO
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = "users.txt"  # set filename attribute so Telegram knows the filename

    # Send as document
    await msg.answer_document(InputFile(bio))
