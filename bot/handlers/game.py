from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from bot.utils.db import create_connection
from bot.keyboards import game_kb
import logging
import asyncio
from bot.utils.logging_config import setup_logging
from typing import Optional

setup_logging()
router = Router()


class GameStates(StatesGroup):
    waiting_for_room_id = State()


async def is_user_in_room(user_id: int) -> bool:
    """Проверяет, находится ли пользователь в какой-либо комнате"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM active_players WHERE user_id = %s", (user_id,))
            return bool(cursor.fetchone())
        finally:
            connection.close()
    return False


async def add_player_to_room(user_id: int, room_id: int) -> bool:
    """Добавляет игрока в комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO active_players (user_id, room_id) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE room_id = VALUES(room_id)",
                (user_id, room_id)
            )
            connection.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления игрока: {e}")
            return False
        finally:
            connection.close()
    return False


async def remove_player_from_room(user_id: int) -> bool:
    """Удаляет игрока из комнаты"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM active_players WHERE user_id = %s", (user_id,))
            connection.commit()
            return cursor.rowcount > 0
        finally:
            connection.close()
    return False


async def get_room_players_count(room_id: int) -> int:
    """Возвращает количество игроков в комнате"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM active_players WHERE room_id = %s", (room_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            connection.close()
    return 0


async def get_user_room_id(user_id: int) -> Optional[int]:
    """Возвращает ID комнаты пользователя"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT room_id FROM active_players WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return int(result[0]) if result else None
        except (ValueError, TypeError):
            return None
        finally:
            connection.close()
    return None


async def create_room(user_id: int, is_private: bool) -> int:
    """Создает новую комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM questions ORDER BY RAND() LIMIT 1")
            question_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO rooms (player1_id, question_id, is_private) VALUES (%s, %s, %s)",
                (user_id, question_id, is_private)
            )
            connection.commit()
            return int(cursor.lastrowid)
        finally:
            connection.close()
    raise Exception("Не удалось подключиться к базе данных")


async def find_or_create_public_room(user_id: int) -> int:
    """Находит или создает публичную комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id FROM rooms 
                WHERE is_private = FALSE 
                AND (player2_id IS NULL OR player3_id IS NULL OR player4_id IS NULL)
                LIMIT 1
            """)
            room = cursor.fetchone()

            if room:
                return int(room[0])
            else:
                return await create_room(user_id, is_private=False)
        finally:
            connection.close()
    raise Exception("Не удалось подключиться к базе данных")


async def update_room_status_periodically(message: Message, room_id: int, stop_event: asyncio.Event):
    """Фоновая задача для автоматического обновления статуса комнаты"""
    last_count = 0

    while not stop_event.is_set():
        try:
            current_count = await get_room_players_count(room_id)

            if current_count != last_count:
                await message.edit_reply_markup(
                    reply_markup=game_kb.get_room_status_keyboard(room_id, current_count)
                )
                last_count = current_count

                if current_count >= 2:
                    await message.edit_text("🎮 Начинаем игру!")
                    stop_event.set()
                    return

        except Exception as e:
            logging.error(f"Ошибка автообновления: {e}")

        await asyncio.sleep(1)


@router.message(F.text == "Начать игру")
async def start_game_handler(msg: Message):
    """Обработчик кнопки 'Начать игру'"""
    try:
        if await is_user_in_room(msg.from_user.id):
            await msg.answer("⚠️ Вы уже находитесь в комнате. Выйдите сначала.")
            return

        await msg.answer("Выберите тип игры:", reply_markup=game_kb.game_type_keyboard)
    except Exception as e:
        logging.error(f"Ошибка в start_game_handler: {e}")
        await msg.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data.in_(["play_with_friends", "play_random"]))
async def game_type_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора типа игры"""
    try:
        user_id = callback.from_user.id

        if await is_user_in_room(user_id):
            await callback.answer("⚠️ Вы уже в другой комнате!", show_alert=True)
            return

        stop_event = asyncio.Event()
        room_id = None
        msg = None

        try:
            if callback.data == "play_with_friends":
                room_id = await create_room(user_id, is_private=True)
                if not await add_player_to_room(user_id, room_id):
                    raise Exception("Не удалось добавить игрока в комнату")

                msg = await callback.message.answer(
                    f"🔒 Приватная комната: {room_id}\n"
                    "Пригласите друзей, отправив им этот ID",
                    reply_markup=game_kb.get_room_status_keyboard(room_id, 1)
                )

            elif callback.data == "play_random":
                room_id = await find_or_create_public_room(user_id)
                if not await add_player_to_room(user_id, room_id):
                    raise Exception("Не удалось добавить игрока в комнату")

                msg = await callback.message.answer(
                    "🔎 Ищем случайных соперников...",
                    reply_markup=game_kb.get_room_status_keyboard(room_id, 1)
                )

            if room_id and msg:
                try:
                    task = asyncio.create_task(update_room_status_periodically(msg, room_id, stop_event))
                    await state.update_data({
                        'room_id': room_id,
                        'stop_event': stop_event,
                        'status_message_id': msg.message_id,
                        'background_task': task
                    })
                except Exception as e:
                    logging.error(f"Ошибка при запуске автообновления: {e}")
                    stop_event.set()
                    await callback.message.answer("⚠️ Произошла ошибка при создании комнаты")

            await callback.answer()

        except Exception as e:
            logging.error(f"Ошибка создания комнаты: {e}")
            await callback.message.answer("❌ Не удалось создать комнату")
            if stop_event:
                stop_event.set()
    except Exception as e:
        logging.error(f"Неожиданная ошибка в game_type_handler: {e}")
        await callback.answer("❌ Произошла непредвиденная ошибка")


@router.callback_query(F.data.startswith("leave_room:"))
async def leave_room_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выхода из комнаты"""
    try:
        user_id = callback.from_user.id
        data = await state.get_data()

        if 'background_task' in data:
            data['stop_event'].set()
            data['background_task'].cancel()

        success = await remove_player_from_room(user_id)
        if success:
            await callback.message.edit_text(
                "✅ Вы вышли из комнаты",
                reply_markup=game_kb.back_to_main_keyboard
            )
        else:
            await callback.message.edit_text(
                "❌ Не удалось выйти из комнаты",
                reply_markup=game_kb.back_to_main_keyboard
            )

        await state.clear()
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка выхода из комнаты: {e}")
        await callback.answer("❌ Ошибка при выходе")


@router.callback_query(F.data == "refresh_room_status")
async def refresh_room_status_handler(callback: CallbackQuery):
    """Ручное обновление статуса комнаты"""
    try:
        user_id = callback.from_user.id
        room_id = await get_user_room_id(user_id)

        if room_id:
            players_count = await get_room_players_count(room_id)
            await callback.message.edit_reply_markup(
                reply_markup=game_kb.get_room_status_keyboard(room_id, players_count)
            )
            await callback.answer("♻️ Статус обновлен")
        else:
            await callback.answer("❌ Вы не в комнате")
    except Exception as e:
        logging.error(f"Ошибка обновления статуса: {e}")
        await callback.answer("❌ Ошибка обновления")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=game_kb.start_buttons
    )
    await callback.answer()


@router.callback_query(F.data == "join_room_by_id")
async def join_room_by_id_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик ввода ID комнаты"""
    await callback.message.answer("Введите ID комнаты:")
    await state.set_state(GameStates.waiting_for_room_id)
    await callback.answer()


@router.message(GameStates.waiting_for_room_id)
async def process_room_id(msg: Message, state: FSMContext):
    """Обработчик присоединения по ID"""
    try:
        user_id = msg.from_user.id
        room_id = int(msg.text.strip())

        if await is_user_in_room(user_id):
            await msg.answer("❌ Вы уже в другой комнате!")
            return

        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM rooms WHERE id = %s", (room_id,))
            if cursor.fetchone():
                await add_player_to_room(user_id, room_id)

                stop_event = asyncio.Event()
                msg = await msg.answer(
                    f"✅ Вы в комнате {room_id}",
                    reply_markup=game_kb.get_room_status_keyboard(
                        room_id,
                        await get_room_players_count(room_id)
                    )
                )

                try:
                    task = asyncio.create_task(update_room_status_periodically(msg, room_id, stop_event))
                    await state.update_data({
                        'room_id': room_id,
                        'stop_event': stop_event,
                        'status_message_id': msg.message_id,
                        'background_task': task
                    })
                except Exception as e:
                    logging.error(f"Ошибка запуска автообновления: {e}")
                    stop_event.set()
            else:
                await msg.answer("❌ Комната не найдена")
            connection.close()
    except ValueError:
        await msg.answer("❌ Введите числовой ID комнаты")
    except Exception as e:
        logging.error(f"Ошибка присоединения к комнате: {e}")
        await msg.answer("❌ Ошибка присоединения")
    finally:
        await state.clear()