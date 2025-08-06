import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router
from database import init_db_pool

from aiogram.types import MenuButtonCommands, BotCommand

from check_bins import check_bins_loop

async def on_startup(dispatcher):
    # Start your background task here
    asyncio.create_task(check_bins_loop(bot))

dp.startup.register(on_startup)

async def main():
    await init_db_pool()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Set default menu button to show bot commands like /start
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    # Register visible bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="setovo", description="Set your OVO ID"),
        # Add other commands here if needed
    ])

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
