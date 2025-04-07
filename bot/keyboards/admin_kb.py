from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


main_admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard = [
        [
            InlineKeyboardButton(text="Редактор вопросов", callback_data="re_question"),
            InlineKeyboardButton(text="Действие 2", callback_data="button_2")
        ],
        [
            InlineKeyboardButton(text="Действие 3", callback_data="button_3"),
            InlineKeyboardButton(text="Действие 4", callback_data="button_4")
        ],
    ]
)
# В клавиатуру re_question добавьте кнопку "Отмена"
re_question = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить вопрос", callback_data="add_question"),
            InlineKeyboardButton(text="Удалить вопрос", callback_data="delete_question"),
        ],
        [
            InlineKeyboardButton(text="Изменить вопрос", callback_data="edit_question"),
            InlineKeyboardButton(text="Отмена", callback_data="back_to_admin_panel")
        ]
    ]
)

# Клавиатура для выбора поля для изменения вопроса
edit_question_fields_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Вопрос", callback_data="question"),
            InlineKeyboardButton(text="Правильный ответ", callback_data="correct_answer")
        ],
        [
            InlineKeyboardButton(text="Неправильный ответ 1", callback_data="wrong_answer_1"),
            InlineKeyboardButton(text="Неправильный ответ 2", callback_data="wrong_answer_2")
        ],
        [
            InlineKeyboardButton(text="Неправильный ответ 3", callback_data="wrong_answer_3"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_questions")
        ]
    ]
)