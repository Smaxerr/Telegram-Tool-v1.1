from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
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
        "Use the menu below to continue."
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
        f"🔐 Welcome to *CipherBot*, {username}.\n\n"
        f"💰 Your balance: £{balance}\n\n"
        "Use the menu below to continue."
    )
    
    await cb.message.edit_text(text, reply_markup=main_menu())
    await cb.answer()  # optionally answer the callback to remove loading spinner


@router.message(F.text.startswith("/setbalance"))
async def set_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorized to use this command.")
    try:
        _, uid, amount = msg.text.split()
        await set_balance(int(uid), int(amount))
        await msg.reply("✅ Balance set.")
    except:
        await msg.reply("❌ Usage: /setbalance <id> <amount>")

@router.message(F.text.startswith("/addbalance"))
async def add_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorized to use this command.")
    try:
        _, uid, amount = msg.text.split()
        await add_balance(int(uid), int(amount))
        await msg.reply("✅ Balance added.")
    except:
        await msg.reply("❌ Usage: /addbalance <id> <amount>")

@router.message(F.text == "/viewusers")
async def view_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorized to use this command.")

    users = await get_all_users()
    lines = [
        f"{u['id']} | @{u['username'] or '—'} | £{u['balance']}"
        for u in users
    ]
    text = "\n".join(lines) or "No users yet."

    buffer = io.BytesIO(text.encode("utf-8"))
    file = BufferedInputFile(buffer.getvalue(), filename="users.txt")

    await msg.answer_document(file, caption="📄 All registered users")
