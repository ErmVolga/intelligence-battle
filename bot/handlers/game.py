from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from bot.utils.db import create_connection
from bot.keyboards import game_kb
from bot.handlers.commands import get_welcome_message, start_buttons
import logging
import asyncio
from bot.utils.logging_config import setup_logging
from typing import Optional

setup_logging()
router = Router()


class GameStates(StatesGroup):
    waiting_for_room_id = State()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню с приветственным сообщением"""
    try:
        # Очищаем состояние
        await state.clear()

        # Удаляем предыдущее сообщение с кнопками (если нужно)
        try:
            await callback.message.delete()
        except:
            pass

        # Отправляем новое приветственное сообщение
        await callback.message.answer(
            await get_welcome_message(callback.message),
            reply_markup=start_buttons
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в back_to_main_handler: {e}")
        await callback.answer("❌ Произошла ошибка")

async def is_user_in_room(user_id: int) -> bool:
    """Проверяет, находится ли пользователь в какой-либо комнате"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT current_room_id FROM players WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] is not None if result else False
        except Exception as e:
            logging.error(f"Ошибка проверки нахождения в комнате: {e}")
            return False
        finally:
            connection.close()
    return False


async def add_player_to_room(user_id: int, room_id: int) -> bool:
    """Добавляет игрока в комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # 1. Обновляем запись игрока
            cursor.execute(
                "UPDATE players SET current_room_id = %s WHERE id = %s",
                (room_id, user_id)
            )

            # 2. Обновляем таблицу rooms
            # Сначала проверяем, куда можно добавить игрока
            cursor.execute("""
                SELECT 
                    player1_id, player2_id, player3_id, player4_id 
                FROM rooms 
                WHERE id = %s
            """, (room_id,))
            room_data = cursor.fetchone()

            if room_data:
                update_query = None
                if room_data[0] is None:  # player1_id пуст
                    update_query = "UPDATE rooms SET player1_id = %s WHERE id = %s"
                elif room_data[1] is None:  # player2_id пуст
                    update_query = "UPDATE rooms SET player2_id = %s WHERE id = %s"
                elif room_data[2] is None:  # player3_id пуст
                    update_query = "UPDATE rooms SET player3_id = %s WHERE id = %s"
                elif room_data[3] is None:  # player4_id пуст
                    update_query = "UPDATE rooms SET player4_id = %s WHERE id = %s"

                if update_query:
                    cursor.execute(update_query, (user_id, room_id))

            connection.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления игрока: {e}")
            connection.rollback()
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

            # 1. Получаем room_id перед удалением
            cursor.execute("SELECT current_room_id FROM players WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            room_id = result[0] if result else None

            # 2. Обновляем запись игрока
            cursor.execute(
                "UPDATE players SET current_room_id = NULL WHERE id = %s",
                (user_id,)
            )

            # 3. Обновляем таблицу rooms (удаляем игрока оттуда)
            if room_id:
                cursor.execute("""
                    UPDATE rooms SET
                        player1_id = CASE WHEN player1_id = %s THEN NULL ELSE player1_id END,
                        player2_id = CASE WHEN player2_id = %s THEN NULL ELSE player2_id END,
                        player3_id = CASE WHEN player3_id = %s THEN NULL ELSE player3_id END,
                        player4_id = CASE WHEN player4_id = %s THEN NULL ELSE player4_id END
                    WHERE id = %s
                """, (user_id, user_id, user_id, user_id, room_id))

            connection.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления игрока из комнаты: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    return False


async def get_room_players_count(room_id: int) -> int:
    """Возвращает количество игроков в комнате"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM players WHERE current_room_id = %s", (room_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"Ошибка получения количества игроков: {e}")
            return 0
        finally:
            connection.close()
    return 0


async def get_user_room_id(user_id: int) -> Optional[int]:
    """Возвращает ID комнаты пользователя"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT current_room_id FROM players WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] is not None else None
        except (ValueError, TypeError) as e:
            logging.error(f"Ошибка преобразования room_id: {e}")
            return None
        except Exception as e:
            logging.error(f"Ошибка получения комнаты игрока: {e}")
            return None
        finally:
            connection.close()
    return None


async def get_room_players(room_id: int) -> list[int]:
    """Возвращает список ID игроков в комнате"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM players WHERE current_room_id = %s", (room_id,))
            result = cursor.fetchall()
            return [row[0] for row in result] if result else []
        except Exception as e:
            logging.error(f"Ошибка получения списка игроков: {e}")
            return []
        finally:
            connection.close()
    return []


async def create_room(user_id: int, is_private: bool) -> int:
    """Создает новую комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # 1. Получаем случайный вопрос
            cursor.execute("SELECT id FROM questions ORDER BY RAND() LIMIT 1")
            question_id = cursor.fetchone()[0]

            # 2. Создаем комнату
            cursor.execute(
                "INSERT INTO rooms (player1_id, question_id, is_private) VALUES (%s, %s, %s)",
                (user_id, question_id, is_private)
            )
            room_id = cursor.lastrowid

            # 3. Обновляем запись игрока
            cursor.execute(
                "UPDATE players SET current_room_id = %s WHERE id = %s",
                (room_id, user_id)
            )

            connection.commit()
            return int(room_id)
        except Exception as e:
            logging.error(f"Ошибка создания комнаты: {e}")
            connection.rollback()
            raise Exception("Не удалось создать комнату")
        finally:
            connection.close()
    raise Exception("Не удалось подключиться к базе данных")


async def find_or_create_public_room(user_id: int) -> int:
    """Находит или создает публичную комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Ищем комнату с доступными слотами
            cursor.execute("""
                SELECT r.id 
                FROM rooms r
                WHERE r.is_private = FALSE 
                AND (
                    SELECT COUNT(*) 
                    FROM players p 
                    WHERE p.current_room_id = r.id
                ) < 4
                LIMIT 1
            """)
            room = cursor.fetchone()

            if room:
                return int(room[0])
            else:
                return await create_room(user_id, is_private=False)
        except Exception as e:
            logging.error(f"Ошибка поиска публичной комнаты: {e}")
            raise Exception("Не удалось найти или создать комнату")
        finally:
            connection.close()
    raise Exception("Не удалось подключиться к базе данных")


async def update_room_status_periodically(message: Message, room_id: int, stop_event: asyncio.Event):
    """Фоновая задача для обновления статуса комнаты без логирования"""
    last_count = 0

    while not stop_event.is_set():
        try:
            current_count = await get_room_players_count(room_id)

            if current_count != last_count:
                try:
                    await message.edit_reply_markup(
                        reply_markup=game_kb.get_room_status_keyboard(room_id, current_count)
                    )
                    last_count = current_count

                    max_players_in_room = 4

                    if current_count >= max_players_in_room:
                        await message.edit_text("🎮 Начинаем игру!")
                        stop_event.set()
                        return

                except Exception:
                    # Полностью игнорируем все ошибки при обновлении кнопки
                    pass

            await asyncio.sleep(1)

        except Exception:
            # Игнорируем все ошибки в фоновой задаче
            pass


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
    """Обновление статуса комнаты без логирования"""
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
    except Exception:
        await callback.answer("❌ Ошибка обновления")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    try:
        await state.clear()

        # Для inline-сообщений используем edit_text с inline-клавиатурой
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=game_kb.back_to_main_inline_keyboard  # Новая inline-клавиатура
        )
        await callback.answer()
    except Exception as e:
        # Если не получилось отредактировать (например, если было ReplyKeyboardMarkup),
        # просто отправляем новое сообщение
        await callback.message.answer(
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
