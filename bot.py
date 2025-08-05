import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonCommands, BotCommand, BotCommandScopeUser
from config import BOT_TOKEN, ADMIN_IDS  # ✅ uses your existing admin list
from handlers import router
from database import init_db_pool

async def main():
    await init_db_pool()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Set default menu button
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    # ✅ Global commands for all users
    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="setovo", description="Set your OVO ID"),
    ])

    # ✅ Admin-only commands
    for admin_id in ADMIN_IDS:
        await bot.set_my_commands(
            commands=[
                BotCommand(command="setbalance", description="Set a user's balance"),
                BotCommand(command="addbalance", description="Add to a user's balance"),
                BotCommand(command="viewusers", description="View all users"),
            ],
            scope=BotCommandScopeUser(user_id=admin_id)
        )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
