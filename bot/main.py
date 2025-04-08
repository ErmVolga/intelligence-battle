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
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Добавляем роутеры
    dp.include_router(commands_router)
    dp.include_router(admin_router)
    dp.include_router(game_router)

    # Принудительная инициализация БД
    connection = create_connection()
    if connection:
        try:
            from database.init_db import create_table
            create_table(connection)  # Явный вызов создания таблиц
            logging.info("Таблицы БД успешно созданы")
        except Exception as e:
            logging.error(f"FATAL: Не удалось создать таблицы: {e}")
            raise
        finally:
            connection.close()
    else:
        logging.error("Невозможно подключиться к БД. Проверьте .env и доступы")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
    logging.info("Бот запущен")