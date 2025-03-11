import logging
from aiogram import types, F, Router, html
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from bot.keyboards import start_buttons
from bot.keyboards.game_kb import game_start_keyboard
from bot.utils.db import create_connection, insert_players
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    try:
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


@router.message(F.text == "Моя статистика")
async def my_stats_handler(msg: types.Message):
    user_id = msg.from_user.id  # Получаем ID пользователя
    connection = create_connection()  # Устанавливаем соединение с базой данных

    if connection is not None:
        try:
            cursor = connection.cursor()

            # Запрос на получение статистики
            query = """
                SELECT score, correct_answers, wrong_answers, wins
                FROM players
                WHERE id = %s;
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()

            if result:
                # Извлекаем данные
                score, correct_answers, wrong_answers, wins = result
                total_answers = correct_answers + wrong_answers

                # Вычисляем долю правильных ответов
                if total_answers > 0:
                    accuracy = correct_answers / total_answers
                    accuracy_percentage = round(accuracy * 100, 2)  # Процент с округлением
                else:
                    accuracy_percentage = 0.0

                # Формируем и отправляем сообщение
                await msg.answer(
                    f"📊 Ваша статистика:\n\n"
                    f"🏆 Очки: {score}\n"
                    f"✅ Правильных ответов: {correct_answers}\n"
                    f"❌ Неправильных ответов: {wrong_answers}\n"
                    f"📈 Доля правильных ответов: {accuracy_percentage}%\n"
                    f"🥇 Побед: {wins}"
                )

                # Логируем успешное выполнение команды
                logging.info(f"Статистика пользователя {user_id} успешно отправлена.")
            else:
                # Если пользователя нет в базе
                await msg.answer("У вас пока нет статистики. Начните игру, чтобы её создать!")
                logging.info(f"Пользователь с id {user_id} запрашивал статистику, но не найден в базе.")
        except Exception as e:
            # Логируем ошибку
            logging.error(f"Ошибка при обработке статистики для пользователя {user_id}: {e}")
            await msg.answer("Произошла ошибка при получении вашей статистики. Попробуйте позже.")
        finally:
            connection.close()
    else:
        # Логируем ошибку подключения к базе данных
        logging.error("Ошибка подключения к базе данных.")
        await msg.answer("Ошибка подключения к базе данных. Попробуйте позже.")

@router.message(F.text == "Начать игру")
async def start_game(msg: types.Message):
    try:
        # Отправляем пользователю инлайн-клавиатуру с выбором действия
        await msg.answer("Выберите действие:", reply_markup=game_start_keyboard)
        logging.info(f"Пользователь {msg.from_user.id} начал процесс создания/присоединения к комнате.")
    except Exception as e:
        logging.error(f"Ошибка в start_game для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте позже.")

'''
@router.message(F.text & ~F.text.startswith("/"))
async def message_handler(msg: Message):
    await msg.answer(f"Твой id: {msg.from_user.id}")
'''

