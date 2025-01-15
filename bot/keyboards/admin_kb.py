from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


main_admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard = [
        [
            InlineKeyboardButton(text="Действие 1", callback_data="button_1"),
            InlineKeyboardButton(text="Действие 2", callback_data="button_2")
        ],
        [
            InlineKeyboardButton(text="Действие 3", callback_data="button_3"),
            InlineKeyboardButton(text="Действие 4", callback_data="button_4")
        ],
    ]
)