import logging
import os
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
from bot.utils.db import create_connection
from bot.keyboards import admin_kb
from bot.keyboards.game_kb import start_buttons
from bot.utils.logging_config import setup_logging

# Настройка логгирования и переменных окружения
setup_logging()
load_dotenv()

ADMIN_IDS = os.getenv("ADMIN_IDS").split(",")

router = Router()


# Состояния для FSM
class AddQuestion(StatesGroup):
    question = State()
    correct_answer = State()
    wrong_answers = State()


class DeleteQuestion(StatesGroup):
    question_id = State()


class EditQuestion(StatesGroup):
    question_id = State()
    field_to_edit = State()
    new_value = State()


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# Список всех админских callback_data
ADMIN_CALLBACKS = [
    "re_question", "add_question", "delete_question", "edit_question",
    "back_to_admin_panel", "back_to_questions", "question", "correct_answer",
    "wrong_answer_1", "wrong_answer_2", "wrong_answer_3", "exit_admin"  # Добавлено
]


# Вход в админ-панель
@router.message(Command("admin", prefix="?"))
async def admin_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id

        if is_admin(user_id):
            logging.info(f"Пользователь {user_id} запросил админ-панель")
            await msg.answer("Добро пожаловать в админ-панель!",
                             reply_markup=admin_kb.main_admin_keyboard)
        else:
            logging.warning(f"Пользователь {user_id} попытался получить доступ к админ-панели")
            await msg.answer("Вы не имеете доступа к админ-панели.")

    except Exception as e:
        logging.error(f"Ошибка в admin_handler: {e}")
        await msg.answer("Произошла ошибка. Попробуйте позже.")


# Обработчик колбэков админ-панели
@router.callback_query(F.data.in_(ADMIN_CALLBACKS))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    try:
        # Проверка прав администратора
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступ запрещён!", show_alert=True)
            return

        data = callback.data
        logging.info(f"Админский колбэк: {data} от {callback.from_user.id}")

        if data == "re_question":
            await callback.message.edit_text(
                text="Что сделать с вопросами?",
                reply_markup=admin_kb.re_question
            )

        elif data == "add_question":
            await callback.message.edit_text("Введите текст вопроса:")
            await state.set_state(AddQuestion.question)

        elif data == "delete_question":
            await callback.message.edit_text("Введите ID вопроса для удаления:")
            await state.set_state(DeleteQuestion.question_id)

        elif data == "edit_question":
            await callback.message.edit_text("Введите ID вопроса для изменения:")
            await state.set_state(EditQuestion.question_id)

        elif data == "back_to_admin_panel":
            await callback.message.edit_text(
                text="Добро пожаловать в админ-панель!",
                reply_markup=admin_kb.main_admin_keyboard
            )

        elif data == "back_to_questions":
            await callback.message.edit_text(
                text="Что сделать с вопросами?",
                reply_markup=admin_kb.re_question
            )

        elif data in ["question", "correct_answer", "wrong_answer_1", "wrong_answer_2", "wrong_answer_3"]:
            await state.update_data(field_to_edit=data)
            await callback.message.edit_text(f"Введите новое значение для поля '{data}':")
            await state.set_state(EditQuestion.new_value)

        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в admin_callback_handler: {e}")
        await callback.answer("❌ Произошла ошибка!")


# Обработчик для удаления вопроса по ID
@router.message(DeleteQuestion.question_id)
async def process_delete_question(msg: types.Message, state: FSMContext):
    try:
        question_id = msg.text.strip()  # Получаем ID вопроса из сообщения

        # Проверяем, что введённый ID является числом
        if not question_id.isdigit():
            await msg.answer("❌ Ошибка: ID вопроса должен быть числом. Попробуйте снова.")
            logging.warning(f"Пользователь {msg.from_user.id} ввёл некорректный ID вопроса: {question_id}")
            return

        # Подключаемся к базе данных
        connection = create_connection()
        if connection:
            cursor = connection.cursor()

            # Проверяем, существует ли вопрос с таким ID
            check_query = "SELECT id FROM questions WHERE id = %s"
            cursor.execute(check_query, (question_id,))
            result = cursor.fetchone()

            if result:
                # Если вопрос существует, удаляем его
                delete_query = "DELETE FROM questions WHERE id = %s"
                cursor.execute(delete_query, (question_id,))
                connection.commit()
                cursor.close()
                connection.close()

                await msg.answer(f"✅ Вопрос с ID {question_id} успешно удалён!")
                logging.info(f"Пользователь {msg.from_user.id} успешно удалил вопрос с ID {question_id}.")

                # Возвращаем администратора в меню управления вопросами
                await msg.answer("Что сделать с вопросами?", reply_markup=admin_kb.re_question)
            else:
                await msg.answer(f"❌ Вопрос с ID {question_id} не найден.")
                logging.warning(
                    f"Пользователь {msg.from_user.id} попытался удалить несуществующий вопрос с ID {question_id}.")
        else:
            await msg.answer("❌ Ошибка подключения к базе данных.")
            logging.error(f"Ошибка подключения к базе данных при удалении вопроса пользователем {msg.from_user.id}.")

        await state.clear()  # Очищаем состояние

    except Exception as e:
        logging.error(f"Ошибка в process_delete_question для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик для изменения вопроса (шаг 1 — ввод ID вопроса)
@router.message(EditQuestion.question_id)
async def process_edit_question_id(msg: types.Message, state: FSMContext):
    try:
        question_id = msg.text.strip()  # Получаем ID вопроса из сообщения

        # Проверяем, что введённый ID является числом
        if not question_id.isdigit():
            await msg.answer("❌ Ошибка: ID вопроса должен быть числом. Попробуйте снова.")
            logging.warning(f"Пользователь {msg.from_user.id} ввёл некорректный ID вопроса: {question_id}")
            return

        # Сохраняем ID вопроса в состоянии
        await state.update_data(question_id=question_id)

        # Запрашиваем поле для изменения
        await msg.answer(
            "Какое поле вы хотите изменить?",
            reply_markup=admin_kb.edit_question_fields_keyboard  # Клавиатура для выбора поля
        )
        await state.set_state(EditQuestion.field_to_edit)
        logging.info(f"Пользователь {msg.from_user.id} ввёл ID вопроса для изменения: {question_id}")

    except Exception as e:
        logging.error(f"Ошибка в process_edit_question_id для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик для изменения вопроса (шаг 2 — выбор поля для изменения)
@router.callback_query(EditQuestion.field_to_edit)
async def process_edit_question_field(callback: CallbackQuery, state: FSMContext):
    try:
        field_to_edit = callback.data  # Получаем выбранное поле из callback_data

        # Сохраняем выбранное поле в состоянии
        await state.update_data(field_to_edit=field_to_edit)

        # Запрашиваем новое значение для выбранного поля
        await callback.message.edit_text(f"Введите новое значение для поля '{field_to_edit}':")
        await state.set_state(EditQuestion.new_value)
        logging.info(f"Пользователь {callback.from_user.id} выбрал поле для изменения: {field_to_edit}")

        await callback.answer()  # Закрывает всплывающее уведомление

    except Exception as e:
        logging.error(f"Ошибка в process_edit_question_field для пользователя {callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")


# Обработчик для изменения вопроса (шаг 3 — ввод нового значения)
@router.message(EditQuestion.new_value)
async def process_edit_question_value(msg: types.Message, state: FSMContext):
    try:
        new_value = msg.text.strip()  # Получаем новое значение из сообщения

        # Получаем сохранённые данные из состояния
        data = await state.get_data()
        question_id = data["question_id"]
        field_to_edit = data["field_to_edit"]

        # Подключаемся к базе данных
        connection = create_connection()
        if connection:
            cursor = connection.cursor()

            # Обновляем выбранное поле в базе данных
            update_query = f"UPDATE questions SET {field_to_edit} = %s WHERE id = %s"
            cursor.execute(update_query, (new_value, question_id))
            connection.commit()
            cursor.close()
            connection.close()

            await msg.answer(f"✅ Поле '{field_to_edit}' вопроса с ID {question_id} успешно изменено!")
            logging.info(
                f"Пользователь {msg.from_user.id} успешно изменил поле '{field_to_edit}' вопроса с ID {question_id}.")

            # Возвращаем администратора в меню управления вопросами
            await msg.answer("Что сделать с вопросами?", reply_markup=admin_kb.re_question)
        else:
            await msg.answer("❌ Ошибка подключения к базе данных.")
            logging.error(f"Ошибка подключения к базе данных при изменении вопроса пользователем {msg.from_user.id}.")

        await state.clear()  # Очищаем состояние

    except Exception as e:
        logging.error(f"Ошибка в process_edit_question_value для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик для получения текста вопроса (шаг 1)
@router.message(AddQuestion.question)
async def process_question_text(msg: types.Message, state: FSMContext):
    try:
        await state.update_data(question=msg.text)  # Сохраняем вопрос
        await msg.answer("Теперь введите правильный ответ:")
        await state.set_state(AddQuestion.correct_answer)  # Переходим к следующему шагу
    except Exception as e:
        logging.error(f"Ошибка при получении вопроса: {e}")
        await msg.answer("❌ Ошибка. Попробуйте снова.")
        await state.clear()


# Обработчик для получения правильного ответа
@router.message(AddQuestion.correct_answer)
async def process_correct_answer(msg: types.Message, state: FSMContext):
    await state.update_data(correct_answer=msg.text)
    await msg.answer("Введите до 9 неправильных ответов через запятую:\nПример: Вариант 1, Вариант 2, ...")
    await state.set_state(AddQuestion.wrong_answers)


# Обработчик для получения неправильных ответов
@router.message(AddQuestion.wrong_answers)
async def process_wrong_answers(msg: types.Message, state: FSMContext):
    try:
        wrong_answers = [ans.strip() for ans in msg.text.split(",") if ans.strip()]

        # Берём первые 9 ответов и заменяем пустые строки на None
        wrong_answers = wrong_answers[:9] + [None] * (9 - len(wrong_answers))

        data = await state.get_data()
        connection = create_connection()
        if connection:
            cursor = None
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO questions (question, correct_answer, "
                    "wrong_answer_1, wrong_answer_2, wrong_answer_3, "
                    "wrong_answer_4, wrong_answer_5, wrong_answer_6, "
                    "wrong_answer_7, wrong_answer_8, wrong_answer_9) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        data["question"],
                        data["correct_answer"],
                        *wrong_answers
                    )
                )
                connection.commit()

                # После успешного добавления показываем меню управления вопросами
                await msg.answer(
                    "✅ Вопрос добавлен!",
                    reply_markup=admin_kb.re_question  # <-- Клавиатура управления вопросами
                )

            except Exception as e:
                logging.error(f"Ошибка выполнения SQL-запроса: {e}")
                await msg.answer(
                    "❌ Ошибка при работе с базой данных.",
                    reply_markup=admin_kb.re_question  # <-- Возврат даже при ошибке
                )
                connection.rollback()
            finally:
                if cursor:
                    cursor.close()
                connection.close()
        else:
            await msg.answer(
                "❌ Ошибка подключения к БД.",
                reply_markup=admin_kb.re_question  # <-- Возврат при ошибке подключения
            )

        await state.clear()

    except Exception as e:
        logging.error(f"Общая ошибка обработки ответов: {e}")
        await msg.answer(
            "❌ Произошла непредвиденная ошибка. Попробуйте снова.",
            reply_markup=admin_kb.re_question  # <-- Возврат при общей ошибке
        )
        await state.clear()


# Новый обработчик для выхода
@router.callback_query(F.data == "exit_admin")
async def exit_admin_handler(callback: CallbackQuery, state: FSMContext):
    try:
        # Удаляем сообщение с админ-панелью
        await callback.message.delete()

        # Отправляем новое сообщение с главным меню
        await callback.message.answer(
            "🔙 Вы вернулись в главное меню",
            reply_markup=start_buttons  # Используем основную клавиатуру
        )

        # Очищаем состояние
        await state.clear()
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка в exit_admin_handler: {e}")
        await callback.answer("❌ Не удалось выйти из админ-панели")