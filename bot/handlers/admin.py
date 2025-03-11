from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.utils.db import create_connection
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
import os
import logging
from bot.utils.logging_config import setup_logging
from bot.keyboards import admin_kb

# Настройка логгирования
setup_logging()
load_dotenv()

ADMIN_IDS = os.getenv("ADMIN_IDS").split(",")

router = Router()


# Состояния для FSM (машины состояний)
class AddQuestion(StatesGroup):
    question = State()
    correct_answer = State()
    wrong_answers = State()


# Состояние для удаления вопроса
class DeleteQuestion(StatesGroup):
    question_id = State()


# Состояния для изменения вопроса
class EditQuestion(StatesGroup):
    question_id = State()  # Шаг 1: Ввод ID вопроса
    field_to_edit = State()  # Шаг 2: Выбор поля для изменения
    new_value = State()  # Шаг 3: Ввод нового значения


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# Вход в админ-панель
@router.message(Command("admin", prefix="?"))
async def admin_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id

        if is_admin(user_id):
            logging.info(f"Пользователь {user_id} запросил админ-панель")
            await msg.answer("Добро пожаловать в админ-панель!", reply_markup=admin_kb.main_admin_keyboard)
        else:
            logging.warning(
                f"Пользователь {user_id} попытался получить доступ к админ-панели, но не является администратором.")
            await msg.answer("Вы не имеете доступа к админ-панели.")

    except Exception as e:
        logging.error(f"Ошибка в admin_handler для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте позже.")


# Клавиатура для меню управления вопросами
@router.callback_query()
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    try:
        data = callback.data  # Получаем callback_data кнопки

        if data == "re_question":
            await callback.message.edit_text(
                text="Что сделать с вопросами?",
                reply_markup=admin_kb.re_question
            )
            logging.info(f"Пользователь {callback.from_user.id} открыл меню управления вопросами.")

        elif data == "add_question":
            await callback.message.edit_text("Введите текст вопроса:")
            await state.set_state(AddQuestion.question)
            logging.info(f"Пользователь {callback.from_user.id} начал добавление нового вопроса.")

        elif data == "delete_question":
            await callback.message.edit_text("Введите ID вопроса для удаления:")
            await state.set_state(DeleteQuestion.question_id)
            logging.info(f"Пользователь {callback.from_user.id} начал процесс удаления вопроса.")

        elif data == "edit_question":  # Обработчик для кнопки "Изменить вопрос"
            await callback.message.edit_text("Введите ID вопроса для изменения:")
            await state.set_state(EditQuestion.question_id)
            logging.info(f"Пользователь {callback.from_user.id} начал процесс изменения вопроса.")

        elif data == "back_to_admin_panel":
            await callback.message.edit_text(
                text="Добро пожаловать в админ-панель!",
                reply_markup=admin_kb.main_admin_keyboard
            )

        elif data == "back_to_questions":
            await callback.message.edit_text(
                text="Что делать с вопросами?",
                reply_markup=admin_kb.re_question
            )

        await callback.answer()  # Закрывает всплывающее уведомление

    except Exception as e:
        logging.error(f"Ошибка в admin_callback_handler для пользователя {callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")


# Обработчик текстового ввода (шаг 1 — ввод вопроса)
@router.message(AddQuestion.question)
async def process_question(msg: types.Message, state: FSMContext):
    try:
        await state.update_data(question=msg.text)
        await msg.answer("Введите правильный ответ:")
        await state.set_state(AddQuestion.correct_answer)
        logging.info(f"Пользователь {msg.from_user.id} ввёл текст вопроса: {msg.text}")

    except Exception as e:
        logging.error(f"Ошибка в process_question для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик текстового ввода (шаг 2 — ввод правильного ответа)
@router.message(AddQuestion.correct_answer)
async def process_correct_answer(msg: types.Message, state: FSMContext):
    try:
        await state.update_data(correct_answer=msg.text)
        await msg.answer("Введите 3 неправильных ответа через запятую (можно до 9):")
        await state.set_state(AddQuestion.wrong_answers)
        logging.info(f"Пользователь {msg.from_user.id} ввёл правильный ответ: {msg.text}")

    except Exception as e:
        logging.error(f"Ошибка в process_correct_answer для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик текстового ввода (шаг 3 — ввод неправильных ответов)
@router.message(AddQuestion.wrong_answers)
async def process_wrong_answers(msg: types.Message, state: FSMContext):
    try:
        wrong_answers = [ans.strip() for ans in msg.text.split(",") if ans.strip()]
        if len(wrong_answers) < 3:
            await msg.answer("Ошибка! Нужно минимум 3 неправильных ответа. Попробуйте снова:")
            logging.warning(
                f"Пользователь {msg.from_user.id} ввёл недостаточное количество неправильных ответов: {msg.text}")
            return

        # Получаем сохранённые данные
        data = await state.get_data()
        question = data["question"]
        correct_answer = data["correct_answer"]

        # Сохраняем в БД
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            query = """
            INSERT INTO questions (question, correct_answer, wrong_answer_1, wrong_answer_2, wrong_answer_3)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (question, correct_answer, *wrong_answers[:3]))
            connection.commit()
            cursor.close()
            connection.close()
            await msg.answer("✅ Вопрос успешно добавлен!")
            logging.info(
                f"Пользователь {msg.from_user.id} успешно добавил вопрос: {question} с правильным ответом: {correct_answer} и неправильными ответами: {wrong_answers[:3]}")

            # Возвращаем администратора в меню управления вопросами
            await msg.answer("Что сделать с вопросами?", reply_markup=admin_kb.re_question)
        else:
            await msg.answer("❌ Ошибка при сохранении в БД.")
            logging.error(f"Ошибка при сохранении вопроса пользователем {msg.from_user.id} в БД.")

        await state.clear()  # Очищаем состояние

    except Exception as e:
        logging.error(f"Ошибка в process_wrong_answers для пользователя {msg.from_user.id}: {e}")
        await msg.answer("Произошла ошибка. Попробуйте снова.")


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
