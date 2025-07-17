from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from config import ADMIN_IDS
from io import BytesIO
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states.bin_lookup import BinLookupState
from keyboards import main_menu, back_menu
from database import register_user, get_balance, set_balance, add_balance, get_all_users
from states.bin_lookup import RoyalMailStates

import io

router = Router()

@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    await register_user(msg.from_user.id, msg.from_user.username)
    balance = await get_balance(msg.from_user.id)
    user_name = msg.from_user.full_name or msg.from_user.username or "User"

    text = (
        f"💻 Welcome to CipherBot, {user_name}.\n\n"
        f"💰 You have **{balance}** credits remaining.\n\n"
        "Use the menu below to continue."
    )
    await msg.answer(text, parse_mode="Markdown", reply_markup=main_menu())


# =========================
# BIN Lookup Handlers
# =========================
import aiohttp
import aiofiles
import pandas as pd
from io import StringIO
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import register_user, get_balance, set_balance
from states import BinLookupState  # your FSM states module



CSV_URL = "https://raw.githubusercontent.com/venelinkochev/bin-list-data/refs/heads/master/bin-list-data.csv"  # Replace with your actual URL
binlookupbutton = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Go Back", callback_data="go_back_from_bin")]
])

@router.message(BinLookupState.waiting_for_bin)
async def bin_lookup(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "NoName"

    # Register user if not exists
    user_balance = await get_balance(user_id)
    if user_balance is None:
        await register_user(user_id, username)
        user_balance = 0

    if user_balance < 0.1:
        await message.answer(
            "❌ Insufficient balance to perform BIN lookup."
        )
        await state.clear()
        return

    # Deduct £0.10 from balance
    new_balance = user_balance - 0.1
    if new_balance < 0:
        new_balance = 0
    await set_balance(user_id, new_balance)

    # Delete prompt message if exists
    data = await state.get_data()
    prompt_id = data.get("prompt_id")
    try:
        if prompt_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
        await message.delete()
    except Exception as e:
        print(f"⚠️ Failed to delete messages: {e}")

    user_input = message.text.strip().lower()

    try:
        # Fetch CSV data
        async with aiohttp.ClientSession() as session:
            async with session.get(CSV_URL) as resp:
                if resp.status != 200:
                    await message.answer("⚠️ Couldn't fetch BIN database.")
                    await state.clear()
                    return
                csv_data = await resp.text()

        # Load CSV
        df = pd.read_csv(StringIO(csv_data))

        # Filter UK BINs >= 400000
        df = df[
            (df['CountryName'].astype(str).str.lower() == "united kingdom") &
            (df['BIN'].astype(str).str.isdigit()) &
            (df['BIN'].astype(int) >= 400000)
        ]

        if user_input.isdigit():
            if len(user_input) == 6:
                rows = df[df['BIN'].astype(str) == user_input]

                if rows.empty:
                    await message.answer("❌ No matching UK BINs found.")
                    await state.clear()
                    return

                r = rows.iloc[0]
                response = (
                    f"✅ BIN Info:\n"
                    f"🔢 BIN: {r['BIN']}\n"
                    f"💳 Brand: {r.get('Brand', 'N/A')}\n"
                    f"🏦 Bank: {r.get('Issuer', 'N/A')}\n"
                    f"🌍 Country: {r.get('CountryName', 'N/A')}\n"
                    f"💻 Type: {r.get('Type', 'N/A')}\n"
                    f"📂 Category: {r.get('Category', 'N/A')}"
                )
                await message.answer(response)
                await state.clear()
                return


            else:
                await message.answer("❌ Please enter a valid 6-digit BIN.")
                await state.clear()
                return

        else:
            # Search by keyword in issuer/brand/type
            rows = df[
                df['Issuer'].astype(str).str.lower().str.contains(user_input) |
                df['Brand'].astype(str).str.lower().str.contains(user_input) |
                df['Type'].astype(str).str.lower().str.contains(user_input)
            ]

            if rows.empty:
                await message.answer("❌ No matching UK BINs found.")
                await state.clear()
                return

            credit_rows = rows[rows['Type'].astype(str).str.lower().str.contains("credit")]
            debit_rows = rows[rows['Type'].astype(str).str.lower().str.contains("debit")]

            output_lines = []

            if not credit_rows.empty:
                output_lines.append("=== 💳 CREDIT CARDS ===")
                for _, r in credit_rows.iterrows():
                    output_lines.append(
                        f"{r['BIN']}, {r['Issuer']}, {r['Type']}, {r['Brand']}, {r.get('Category', 'N/A')}"
                    )

            if not debit_rows.empty:
                output_lines.append("\n=== 🏦 DEBIT CARDS ===")
                for _, r in debit_rows.iterrows():
                    output_lines.append(
                        f"{r['BIN']}, {r['Issuer']}, {r['Type']}, {r['Brand']}, {r.get('Category', 'N/A')}"
                    )

            if not output_lines:
                await message.answer("❌ No matching UK BINs found.")
                await state.clear()
                return

            filepath = "/tmp/uk_bin_results.txt"
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write("\n".join(output_lines))

            msg = await message.answer_document(
                FSInputFile(filepath),
                caption=f"📄 UK BINs matching: '{user_input}'"
            )
            await state.update_data(result_msg_id=msg.message_id)

    except Exception as e:
        await message.answer(f"⚠️ Error: {e}")
        print(f"BIN lookup error: {e}")

    await state.clear()


@router.callback_query(F.data == "BINlookup")
async def start_bin_lookup(callback: CallbackQuery, state: FSMContext):
    prompt = await callback.message.answer(
        "🔍 Enter a BIN (6 digits) or a keyword (e.g. bank name, 'credit', 'debit'):"
    )
    await state.update_data(prompt_id=prompt.message_id)
    await state.set_state(BinLookupState.waiting_for_bin)
    await callback.answer()


# ===== Button click triggers FSM =====
@router.callback_query(F.data == "royalmail_charger")
async def royalmail_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RoyalMailStates.awaiting_cards)
    await callback.message.answer("Please send the card(s), one per line:")
    await callback.answer()

# ===== User sends card list =====
@router.message(RoyalMailStates.awaiting_cards)
async def handle_card_list(message: Message, state: FSMContext):
    cards = [line.strip() for line in message.text.splitlines() if line.strip()]
    if not cards:
        await message.answer("❌ No cards found. Please send again.")
        return

    await message.answer(f"🔍 Received {len(cards)} card(s). Starting...")

    for idx, card in enumerate(cards, start=1):
        await message.answer(f"📦 Processing card {idx}: `{card}`", parse_mode="Markdown")
        screenshot_path = await take_royalmail_screenshot(card)

        if screenshot_path:
            await message.answer_photo(FSInputFile(screenshot_path))
            os.remove(screenshot_path)
        else:
            await message.answer(f"❌ Failed to process card `{card}`")

    await message.answer("✅ All done.")
    await state.clear()


@router.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    balance = await get_balance(cb.from_user.id)
    username = cb.from_user.username or "NoUsername"
    
    text = (
        f"💻 Welcome to CipherBot, {username}.\n\n"
        f"💰 You have **{balance}** credits remaining.\n\n"
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
