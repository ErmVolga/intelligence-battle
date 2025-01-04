from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer("Пробник")

@router.message()
async def message_handler(msg: Message):
    await msg.answer(f"Твой id: {msg.from_user.id}")