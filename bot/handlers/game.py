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
    waiting_for_friends_action = State()


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
            # Явная проверка на NULL и числовые значения
            cursor.execute(
                "SELECT current_room_id FROM players WHERE id = %s AND current_room_id IS NOT NULL",
                (user_id,)
            )
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logging.error(f"Ошибка проверки нахождения в комнате: {e}")
            return False
        finally:
            connection.close()
    return False


async def add_player_to_room(user_id: int, room_id: int) -> bool:
    """Добавляет игрока в комнату"""
    if await is_user_in_room(user_id):
        return False

    connection = create_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()

        # Обновляем запись игрока
        cursor.execute(
            "UPDATE players SET current_room_id = %s WHERE id = %s",
            (room_id, user_id)
        )

        # Находим первый пустой слот в комнате
        cursor.execute("""
            SELECT 
                player1_id, 
                player2_id, 
                player3_id, 
                player4_id 
            FROM rooms 
            WHERE id = %s
            FOR UPDATE
        """, (room_id,))
        players = cursor.fetchone()

        update_query = None
        params = ()

        # Проверяем слоты и обновляем первый пустой
        for i in range(4):
            if players[i] is None:
                column_name = f"player{i + 1}_id"
                update_query = f"UPDATE rooms SET {column_name} = %s WHERE id = %s"
                params = (user_id, room_id)
                break

        if not update_query:
            logging.error(f"Нет свободных слотов в комнате {room_id}")
            return False

        cursor.execute(update_query, params)
        connection.commit()
        return True

    except Exception as e:
        logging.error(f"Ошибка добавления игрока {user_id} в комнату {room_id}: {str(e)}")
        connection.rollback()
        return False
    finally:
        connection.close()


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
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    (player1_id IS NOT NULL) + 
                    (player2_id IS NOT NULL) + 
                    (player3_id IS NOT NULL) + 
                    (player4_id IS NOT NULL)
                FROM rooms
                WHERE id = %s
            """, (room_id,))
            result = cursor.fetchone()
            if result is None:
                logging.warning(f"[room {room_id}] Комната не найдена.")
                return 0
            count = result[0]
            logging.info(f"[room {room_id}] В комнате {count} игроков")
            return count
        except Exception as e:
            logging.error(f"[room {room_id}] Ошибка при подсчёте игроков: {e}")
        finally:
            connection.close()
    return 0




# Новая функция для автоматического старта игры
async def start_game_automatically(room_id: int):
    """Запускает игру автоматически и уведомляет игроков"""
    try:
        connection = create_connection()
        if connection:
            players = await get_room_players(room_id)
            for player_id in players:
                # Отправляем сообщение каждому игроку
                # Здесь должна быть логика начала игры (ваш код)
                pass
            logging.info(f"Игра в комнате {room_id} начата автоматически")
    except Exception as e:
        logging.error(f"Ошибка при автоматическом старте игры: {e}")


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
    """Создает новую комнату (без установки current_room_id у игрока)"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Получаем случайный вопрос
            cursor.execute("SELECT id FROM questions ORDER BY RAND() LIMIT 1")
            question_id = cursor.fetchone()[0]

            # Создаем комнату (без назначения игрока в player1_id!)
            cursor.execute(
                "INSERT INTO rooms (question_id, is_private) VALUES (%s, %s)",
                (question_id, is_private)
            )
            room_id = cursor.lastrowid

            connection.commit()
            return int(room_id)

        except Exception as e:
            logging.error(f"Ошибка создания комнаты: {e}")
            connection.rollback()
            raise Exception("Не удалось создать комнату")

        finally:
            cursor.close()
            connection.close()

    raise Exception("Не удалось подключиться к базе данных")


async def find_or_create_public_room(user_id: int) -> int:
    """Находит или создает публичную комнату"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Исправленный SQL-запрос (добавлена закрывающая скобка)
            cursor.execute("""
                SELECT r.id 
                FROM rooms r
                WHERE r.is_private = FALSE 
                AND (
                    r.player1_id IS NULL OR
                    r.player2_id IS NULL OR
                    r.player3_id IS NULL OR
                    r.player4_id IS NULL
                )  # <-- Закрывающая скобка добавлена
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


# Модифицированная фоновая задача с таймерами
async def update_room_status_periodically(message: Message, room_id: int, stop_event: asyncio.Event):
    try:
        countdown_total = 90  # Общее время таймера (сек)
        countdown_remaining = countdown_total
        min_players_timer_started = False
        min_players_start_time = None

        while not stop_event.is_set():
            await asyncio.sleep(1)

            players_count = await get_room_players_count(room_id)

            if players_count == 0:
                logging.info(f"[room {room_id}] Нет игроков, удаляю комнату...")
                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
                        connection.commit()
                        logging.info(f"[room {room_id}] Комната удалена")
                    except Exception as e:
                        logging.error(f"[room {room_id}] Ошибка при удалении: {e}")
                    finally:
                        connection.close()
                stop_event.set()
                break

            # Если игроков >= 2, запускаем или продолжаем таймер
            if players_count >= 2:
                if not min_players_timer_started:
                    min_players_timer_started = True
                    min_players_start_time = asyncio.get_event_loop().time()
                    countdown_remaining = countdown_total  # Обновляем отсчёт

                else:
                    elapsed = asyncio.get_event_loop().time() - min_players_start_time
                    countdown_remaining = max(0, countdown_total - int(elapsed))

                # Если таймер истёк — запускаем игру
                if countdown_remaining == 0:
                    await message.edit_text("⌛ Время ожидания истекло. Игра начинается!")
                    await start_game_automatically(room_id)
                    stop_event.set()
                    break

                try:
                    await message.edit_text(
                        f"⏳ Игроков: {players_count}/4\n"
                        f"⌛ Игра начнётся через: {countdown_remaining} сек",
                        reply_markup=game_kb.get_room_status_keyboard(room_id, players_count)
                    )
                except:
                    pass

            # Если игроков стало меньше 2 — сбрасываем таймер
            else:
                if min_players_timer_started:
                    logging.info(f"В комнате {room_id} осталось <2 игроков — таймер сброшен")
                    min_players_timer_started = False
                    min_players_start_time = None
                    countdown_remaining = countdown_total

                try:
                    await message.edit_text(
                        f"🕐 Ожидаем игроков... ({players_count}/4)",
                        reply_markup=game_kb.get_room_status_keyboard(room_id, players_count)
                    )
                except:
                    pass

            await asyncio.sleep(1)

    except Exception as e:
        logging.error(f"Фоновая задача комнаты {room_id} завершилась с ошибкой: {e}", exc_info=True)


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


@router.callback_query(F.data == "play_with_friends")
async def play_with_friends_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Играть с друзьями'"""
    try:
        user_id = callback.from_user.id

        if await is_user_in_room(user_id):
            await callback.answer("⚠️ Вы уже в другой комнате!", show_alert=True)
            return
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=game_kb.friends_action_keyboard
        )
        await state.set_state(GameStates.waiting_for_friends_action)
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в play_with_friends_handler: {e}")


@router.callback_query(
    GameStates.waiting_for_friends_action,
    F.data.in_(["create_room", "join_room_by_id"])
)
async def handle_friends_action(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id

        if await is_user_in_room(user_id):
            await callback.answer("⚠️ Вы уже в другой комнате!", show_alert=True)
            return

        if callback.data == "create_room":
            # Создаем комнату
            room_id = await create_room(user_id, is_private=True)
            if not await add_player_to_room(user_id, room_id):
                raise Exception("Не удалось добавить игрока в комнату")

            msg = await callback.message.answer(
                f"🔒 Приватная комната: {room_id}\n"
                "Пригласите друзей, отправив им этот ID",
                reply_markup=game_kb.get_room_status_keyboard(room_id, 1)
            )

            # Запускаем фоновую задачу с таймерами
            stop_event = asyncio.Event()
            task = asyncio.create_task(update_room_status_periodically(msg, room_id, stop_event))

            await state.update_data({
                'room_id': room_id,
                'stop_event': stop_event,
                'status_message_id': msg.message_id,
                'background_task': task
            })

        else:
            await callback.message.answer("Введите ID комнаты:")
            await state.set_state(GameStates.waiting_for_room_id)

        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в handle_friends_action: {e}")
        await callback.answer("❌ Не удалось создать комнату")


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


@router.callback_query(F.data == "play_random")
async def play_random_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        # Добавить логи
        logging.info(f"Начало обработки play_random для пользователя {user_id}")

        if await is_user_in_room(user_id):
            await callback.answer("⚠️ Вы уже в другой комнате!", show_alert=True)
            return

        # Находим или создаем публичную комнату
        logging.info(f"Поиск публичной комнаты для {user_id}")
        room_id = await find_or_create_public_room(user_id)
        logging.info(f"Найдена/создана комната {room_id}")

        # Добавляем игрока в комнату
        logging.info(f"Попытка добавить {user_id} в комнату {room_id}")
        success = await add_player_to_room(user_id, room_id)
        if not success:
            await callback.answer("❌ Не удалось присоединиться")
            return

        # Отправляем сообщение
        logging.info(f"Отправка сообщения для {user_id}")
        msg = await callback.message.answer(
            f"✅ Вы в комнате {room_id}. Ожидаем игроков...",
            reply_markup=game_kb.get_room_status_keyboard(
                room_id,
                await get_room_players_count(room_id)
            )
        )
        logging.info(f"Сообщение отправлено: ID {msg.message_id}")

        # Запуск фоновой задачи
        stop_event = asyncio.Event()
        task = asyncio.create_task(update_room_status_periodically(msg, room_id, stop_event))
        await state.update_data({
            'room_id': room_id,
            'stop_event': stop_event,
            'status_message_id': msg.message_id,
            'background_task': task
        })

        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в play_random_handler: {e}", exc_info=True)
        await callback.answer("❌ Не удалось присоединиться к комнате")


@router.message(GameStates.waiting_for_room_id)
async def process_room_id(msg: Message, state: FSMContext):
    try:
        user_id = msg.from_user.id
        room_id = int(msg.text.strip())

        # Усиленная проверка
        if await is_user_in_room(user_id):
            await msg.answer("❌ Вы уже в другой комнате!")
            await state.clear()
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
