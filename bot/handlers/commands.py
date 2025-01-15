import logging
from aiogram import types, F, Router, html
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from bot.keyboards import start_buttons
from bot.utils.db import create_connection, insert_players
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    try:
        logging.info(f"Получена команда /start от пользователя с id {msg.from_user.id}")

        # Подключение к базе данных
        try:
            connection = create_connection()
            if connection:
                logging.info("Подключение к базе данных успешно.")
            else:
                logging.error("Ошибка подключения к базе данных.")
                return  # Прерываем выполнение, если соединение не установлено
        except Exception as e:
            logging.error(f"Ошибка при попытке подключения к базе данных: {e}")
            return

        try:
            # Получаем id пользователя
            user_id = msg.from_user.id

            # Проверяем, есть ли пользователь в таблице
            cursor = connection.cursor()
            try:
                check_query = "SELECT * FROM players WHERE id = %s"
                cursor.execute(check_query, (user_id,))  # Передаем параметр как кортеж
                result = cursor.fetchone()

                if result is None:
                    # Если пользователя нет, добавляем его
                    try:
                        insert_players(connection, user_id)
                        logging.info(f"Пользователь с id {user_id} добавлен в таблицу.")
                    except Exception as e:
                        logging.error(f"Ошибка при добавлении игрока с id {user_id}: {e}")
                else:
                    logging.info(f"Пользователь с id {user_id} уже существует в таблице.")
            except Exception as e:
                logging.error(f"Ошибка при выполнении запроса для проверки пользователя с id {user_id}: {e}")

            try:
                # Отправляем приветственное сообщение
                await msg.answer(
                    f"Привет, {html.bold(html.quote(msg.from_user.full_name))}! 👋\n"
                    "Добро пожаловать в нашу интеллектуальную викторину! 🎉\n\n"
                    "Здесь ты можешь:\n"
                    "🧠 Проверить свои знания.\n"
                    "⚔️ Соревноваться с друзьями.\n"
                    "🏆 Стать чемпионом в захватывающей игре!\n\n"
                    "Вот что можно сделать:\n"
                    "- Нажми 'Начать игру', чтобы пригласить игроков и начать партию.\n"
                    "- Выбери 'Правила', чтобы узнать, как играть.\n"
                    "- Если возникнут вопросы, нажми 'Помощь'.\n\n"
                    "Готов? Тогда жми на кнопку ниже и вперёд к победе! 🚀",
                    reply_markup=start_buttons
                )
                logging.info(f"Приветственное сообщение отправлено пользователю с id {user_id}.")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю с id {user_id}: {e}")
        except Exception as e:
            logging.error(f"Ошибка при обработке команды /start: {e}")
        finally:
            try:
                connection.close()
                logging.info("Соединение с базой данных закрыто.")
            except Exception as e:
                logging.error(f"Ошибка при закрытии соединения с базой данных: {e}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /start: {e}")


@router.message()
async def message_handler(msg: Message):
    await msg.answer(f"Твой id: {msg.from_user.id}")

