from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from config import ADMIN_IDS
from keyboards import main_menu, back_menu
from database import *
import io
import asyncpg
from config import DB_CONFIG

router = Router()

@router.message(F.text == "/start")
async def cmd_start(msg: Message, state, bot):
    async with asyncpg.connect(**DB_CONFIG) as conn:
        await register_user(conn, msg.from_user.id, msg.from_user.username)
        balance = await get_balance(conn, msg.from_user.id)
    await msg.answer(f"💰 Your balance: £{balance}", reply_markup=main_menu())

@router.callback_query(F.data == "bin_lookup")
async def bin_lookup(cb: CallbackQuery):
    await cb.message.edit_text("🔍 Advanced BIN Lookup coming soon...", reply_markup=back_menu())

@router.callback_query(F.data == "ovo_charger")
async def ovo_charger(cb: CallbackQuery):
    await cb.message.edit_text("⚡ OvO Charger coming soon...", reply_markup=back_menu())

@router.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    async with asyncpg.connect(**DB_CONFIG) as conn:
        balance = await get_balance(conn, cb.from_user.id)
    await cb.message.edit_text(f"💰 Your balance: £{balance}", reply_markup=main_menu())

@router.message(F.text.startswith("/setbalance"))
async def set_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, uid, amount = msg.text.split()
        async with asyncpg.connect(**DB_CONFIG) as conn:
            await set_balance(conn, int(uid), int(amount))
        await msg.reply("✅ Balance set.")
    except:
        await msg.reply("❌ Usage: /setbalance <id> <amount>")

@router.message(F.text.startswith("/addbalance"))
async def add_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        _, uid, amount = msg.text.split()
        async with asyncpg.connect(**DB_CONFIG) as conn:
            await add_balance(conn, int(uid), int(amount))
        await msg.reply("✅ Balance added.")
    except:
        await msg.reply("❌ Usage: /addbalance <id> <amount>")

@router.message(F.text == "/viewusers")
async def view_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    async with asyncpg.connect(**DB_CONFIG) as conn:
        users = await get_all_users(conn)

    content = "\n".join([f"{u['id']} | {u['username']} | £{u['balance']}" for u in users])
    file = io.StringIO(content)
    await msg.answer_document(FSInputFile(file, filename="users.txt"))
