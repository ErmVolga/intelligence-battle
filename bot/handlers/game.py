from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.db import create_connection
from bot.keyboards import game_kb
import logging
from bot.utils.logging_config import setup_logging

setup_logging()
router = Router()

# Состояния для FSM (машины состояний)
class JoinRoom(StatesGroup):
    waiting_for_room_id = State()  # Ожидание ввода ID комнаты

# Обработчик для кнопки "Создать комнату"
@router.callback_query(F.data == "create_room")
async def create_room(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            # Создаем новую комнату
            create_room_query = """
                INSERT INTO rooms (player1_id, question_id)
                VALUES (%s, %s);
            """
            # В качестве question_id можно пока использовать 1 (или любой другой ID вопроса)
            cursor.execute(create_room_query, (user_id, 1))
            connection.commit()

            # Получаем ID созданной комнаты
            room_id = cursor.lastrowid

            cursor.close()
            connection.close()

            await callback.message.answer(f"✅ Комната создана! ID комнаты: {room_id}")
            logging.info(f"Пользователь {user_id} создал комнату с ID {room_id}.")
        else:
            await callback.message.answer("❌ Ошибка подключения к базе данных.")
            logging.error(f"Ошибка подключения к базе данных при создании комнаты пользователем {user_id}.")

        await callback.answer()  # Закрываем всплывающее уведомление

    except Exception as e:
        logging.error(f"Ошибка в create_room для пользователя {callback.from_user.id}: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

# Обработчик для кнопки "Присоединиться к случайной комнате"
@router.callback_query(F.data == "join_random_room")
async def join_random_room(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            # Ищем комнату с свободными местами
            find_room_query = """
                SELECT id FROM rooms
                WHERE player2_id IS NULL OR player3_id IS NULL OR player4_id IS NULL
                LIMIT 1;
            """
            cursor.execute(find_room_query)
            result = cursor.fetchone()

            if result:
                room_id = result[0]

                # Обновляем комнату, добавляя пользователя
                update_room_query = """
                    UPDATE rooms
                    SET player2_id = COALESCE(player2_id, %s),
                        player3_id = COALESCE(player3_id, %s),
                        player4_id = COALESCE(player4_id, %s)
                    WHERE id = %s;
                """
                cursor.execute(update_room_query, (user_id, user_id, user_id, room_id))
                connection.commit()

                await callback.message.answer(f"✅ Вы присоединились к комнате с ID {room_id}!")
                logging.info(f"Пользователь {user_id} присоединился к комнате с ID {room_id}.")
            else:
                await callback.message.answer("❌ Нет доступных комнат. Создайте новую комнату.")
                logging.info(f"Пользователь {user_id} попытался присоединиться к случайной комнате, но свободных комнат нет.")

            cursor.close()
            connection.close()
        else:
            await callback.message.answer("❌ Ошибка подключения к базе данных.")
            logging.error(f"Ошибка подключения к базе данных при присоединении к комнате пользователем {user_id}.")

        await callback.answer()  # Закрываем всплывающее уведомление

    except Exception as e:
        logging.error(f"Ошибка в join_random_room для пользователя {callback.from_user.id}: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

# Обработчик для кнопки "Присоединиться по ID комнаты"
@router.callback_query(F.data == "join_room_by_id")
async def join_room_by_id(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Введите ID комнаты:")
        await state.set_state(JoinRoom.waiting_for_room_id)
        logging.info(f"Пользователь {callback.from_user.id} начал процесс присоединения к комнате по ID.")
        await callback.answer()  # Закрываем всплывающее уведомление
    except Exception as e:
        logging.error(f"Ошибка в join_room_by_id для пользователя {callback.from_user.id}: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

# Обработчик для ввода ID комнаты
@router.message(JoinRoom.waiting_for_room_id)
async def process_room_id(msg: types.Message, state: FSMContext):
    try:
        room_id = msg.text.strip()
        user_id = msg.from_user.id
        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            # Проверяем, существует ли комната с таким ID
            check_room_query = """
                SELECT id FROM rooms WHERE id = %s;
            """
            cursor.execute(check_room_query, (room_id,))
            result = cursor.fetchone()

            if result:
                # Обновляем комнату, добавляя пользователя
                update_room_query = """
                    UPDATE rooms
                    SET player2_id = COALESCE(player2_id, %s),
                        player3_id = COALESCE(player3_id, %s),
                        player4_id = COALESCE(player4_id, %s)
                    WHERE id = %s;
                """
                cursor.execute(update_room_query, (user_id, user_id, user_id, room_id))
                connection.commit()

                await msg.answer(f"✅ Вы присоединились к комнате с ID {room_id}!")
                logging.info(f"Пользователь {user_id} присоединился к комнате с ID {room_id}.")
            else:
                await msg.answer("❌ Комната с таким ID не найдена.")
                logging.info(f"Пользователь {user_id} попытался присоединиться к несуществующей комнате с ID {room_id}.")

            cursor.close()
            connection.close()
        else:
            await msg.answer("❌ Ошибка подключения к базе данных.")
            logging.error(f"Ошибка подключения к базе данных при присоединении к комнате пользователем {user_id}.")

        await state.clear()  # Очищаем состояние

    except Exception as e:
        logging.error(f"Ошибка в process_room_id для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте позже.")