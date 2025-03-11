from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.utils.db import create_connection
import logging

router = Router()


# Состояния для FSM (машины состояний)
class AddQuestion(StatesGroup):
    question = State()
    correct_answer = State()
    wrong_answers = State()


# Клавиатура для меню управления вопросами
re_question = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Добавить вопрос", callback_data="add_question")],
        [InlineKeyboardButton(text="Удалить вопрос", callback_data="delete_question")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ]
)


@router.callback_query()
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data  # Получаем callback_data кнопки

    if data == "re_question":
        await callback.message.edit_text(
            text="Что сделать с вопросами?",
            reply_markup=re_question
        )

    elif data == "add_question":
        await callback.message.edit_text("Введите текст вопроса:")
        await state.set_state(AddQuestion.question)

    await callback.answer()  # Закрывает всплывающее уведомление


# Обработчик текстового ввода (шаг 1 — ввод вопроса)
@router.message(AddQuestion.question)
async def process_question(msg: types.Message, state: FSMContext):
    await state.update_data(question=msg.text)
    await msg.answer("Введите правильный ответ:")
    await state.set_state(AddQuestion.correct_answer)


# Обработчик текстового ввода (шаг 2 — ввод правильного ответа)
@router.message(AddQuestion.correct_answer)
async def process_correct_answer(msg: types.Message, state: FSMContext):
    await state.update_data(correct_answer=msg.text)
    await msg.answer("Введите 3 неправильных ответа через запятую (можно до 9):")
    await state.set_state(AddQuestion.wrong_answers)


# Обработчик текстового ввода (шаг 3 — ввод неправильных ответов)
@router.message(AddQuestion.wrong_answers)
async def process_wrong_answers(msg: types.Message, state: FSMContext):
    wrong_answers = [ans.strip() for ans in msg.text.split(",") if ans.strip()]
    if len(wrong_answers) < 3:
        await msg.answer("Ошибка! Нужно минимум 3 неправильных ответа. Попробуйте снова:")
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
    else:
        await msg.answer("❌ Ошибка при сохранении в БД.")

    await state.clear()  # Очищаем состояние
