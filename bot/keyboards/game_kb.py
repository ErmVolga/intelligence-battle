from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Создание клавиатуры
start_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать игру")],
        [
            KeyboardButton(text="Чемпионы"),
            KeyboardButton(text="Моя статистика")
        ],
        [
            KeyboardButton(text="Правила"),
            KeyboardButton(text="Помощь")
        ]
    ],
    resize_keyboard=True  # Уменьшает клавиатуру под размер экрана
)

# Клавиатура для выбора действия (создать комнату, присоединиться к случайной комнате, присоединиться по ID)
game_start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Создать комнату", callback_data="create_room"),
            InlineKeyboardButton(text="Присоединиться к случайной комнате", callback_data="join_random_room")
        ],
        [
            InlineKeyboardButton(text="Присоединиться по ID комнаты", callback_data="join_room_by_id"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")
        ]
    ]
)