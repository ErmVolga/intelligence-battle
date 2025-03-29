import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from handlers import *
from utils.logging_config import setup_logging
from utils.db import create_connection
from database.init_db import create_table

setup_logging()
load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        )
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Включаем все роутеры
    dp.include_router(commands_router)  # роутер команд
    dp.include_router(admin_router)     # роутер для админ панели
    dp.include_router(game_router)      # роутер для игры (комнаты)

    connection = create_connection()
    if connection:
        create_table(connection)
        logging.info("Таблица проверена и создана, если не существовала.")
    else:
        logging.error("Не удалось установить соединение с базой данных!")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
    logging.info("Бот запущен")