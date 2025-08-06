import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router
from database import init_db_pool
import logging
from aiogram.types import MenuButtonCommands, BotCommand
from check_bins import check_bins_loop

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)        # create global bot instance
dp = Dispatcher()           # create global dispatcher instance

async def on_startup():
    # Start your background task here, you can use global bot
    asyncio.create_task(check_bins_loop(bot))

async def main():
    await init_db_pool()
    dp.include_router(router)

    # Set default menu button to show bot commands like /start
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    # Register visible bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="setovo", description="Set your OVO ID"),
        # Add other commands here if needed
    ])

    await on_startup()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
