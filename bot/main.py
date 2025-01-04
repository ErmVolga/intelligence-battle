import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from dotenv import load_dotenv

# Загружаем токен из .env файла
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Основные обработчики

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я бот для викторины. Давай играть!")

# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("Я помогу тебе сыграть в викторину. Вопросы появятся после начала игры.")

# Запуск бота
async def on_start():
    print("Бот запущен!")
    await dp.start_polling()

# Функция для запуска бота
def start_bot():
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
