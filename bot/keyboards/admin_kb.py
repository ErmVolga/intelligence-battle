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

re_question = InlineKeyboardMarkup(
    inline_keyboard = [
        [
            InlineKeyboardButton(text="Добавить вопрос", callback_data="add_question"),
            InlineKeyboardButton(text="Удалить вопрос", callback_data="delete_question"),
        ],
[
            InlineKeyboardButton(text="Назад", callback_data="pass"),
            InlineKeyboardButton(text="Изменить вопрос", callback_data="change_question"),
        ]
    ]
)