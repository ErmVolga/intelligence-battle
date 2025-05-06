from aiogram import types, Router, F
from aiogram.filters import Command
import logging

router = Router()

@router.message(F.text == "Помощь")
@router.message(Command("help"))
async def help_handler(msg: types.Message):
    try:
        help_text = (
            "ℹ️ <b>Помощь по боту</b>\n\n"
            "Этот бот — интеллектуальная викторина для 2–4 игроков.\n"
            "Вы можете играть с друзьями или со случайными соперниками.\n\n"
            "<b>Основные команды:</b>\n"
            "• <b>Начать игру</b> — создайте комнату или присоединитесь к другим\n"
            "• <b>Моя статистика</b> — узнайте свои очки, победы и точность\n"
            "• <b>Правила</b> — описание игровых правил и механик\n"
            "• <b>Помощь</b> — это сообщение с инструкциями\n\n"
            "<b>Как играть:</b>\n"
            "1. Выберите режим: с друзьями или случайно\n"
            "2. Ответьте на вопрос за 20 секунд\n"
            "3. Зарабатывайте очки и выбывайте, если набрали меньше всех\n"
            "4. Можно выйти в банк 💰, чтобы сохранить очки, но вы выбываете\n\n"
            "📢 Если возникнут ошибки — перезапустите бота командой /start\n\n"
            "<b>Связь с разработчиками:</b>\n"
            "👨‍💻 <a href='https://t.me/ErmakVlg'>@ErmakVlg</a>\n"
            "👨‍🔧 <a href='https://t.me/JamalJamalovich'>@JamalJamalovich</a>\n"
        )

        await msg.answer(help_text, parse_mode="HTML", disable_web_page_preview=True)
        logging.info(f"Пользователь {msg.from_user.id} вызвал помощь")
    except Exception as e:
        logging.error(f"Ошибка в help_handler: {e}")
        await msg.answer("Произошла ошибка при отображении помощи. Попробуйте позже.")
