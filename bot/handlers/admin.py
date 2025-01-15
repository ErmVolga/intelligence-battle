from aiogram import Router, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
import os
import logging
from bot.utils.logging_config import setup_logging
from bot.keyboards import admin_kb

setup_logging()
load_dotenv()

ADMIN_IDS = os.getenv("ADMIN_IDS").split(",")

router = Router()

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

@router.message(Command("admin", prefix= "?"))
async def admin_handler(msg: types.Message):
    user_id = msg.from_user.id

    if is_admin(user_id):
        logging.info(f"Пользователь {user_id} запросил админ-панель")
        await msg.answer("Добро пожаловать в админ-панель!", reply_markup=admin_kb.main_admin_keyboard)
    else:
        logging.warning(f"Пользователь {user_id} попытался получить доступ к админ-панели, но не является администратором.")
        await msg.answer("Вы не имеете доступа к админ-панели.")
