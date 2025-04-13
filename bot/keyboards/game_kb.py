import logging
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
game_type_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Играть с друзьями", callback_data="play_with_friends"),
            InlineKeyboardButton(text="Случайные соперники", callback_data="play_random")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="back_to_main")
        ]
    ]
)

back_to_main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ]
)


def get_room_status_keyboard(room_id: int, players_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔄 {players_count}/4 игроков",
                    callback_data="refresh_room_status"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Начать игру",
                    callback_data="start_private_game"
                ),
                InlineKeyboardButton(
                    text="🚪 Выйти",
                    callback_data=f"leave_room:{room_id}"
                )
            ]
        ]
    )


back_to_main_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Начать игру", callback_data="start_game")],
        [InlineKeyboardButton(text="Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="Правила", callback_data="rules")]
    ]
)

# Клавиатура для выбора действия с друзьями
friends_action_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Создать комнату", callback_data="create_room"),
            InlineKeyboardButton(text="Присоединиться по ID", callback_data="join_room_by_id")
        ],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ]
)


# Обновленная клавиатура статуса комнаты с таймером
def get_private_room_keyboard(room_id: int, players_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👥 Игроков: {players_count}/4",
                    callback_data="refresh_room_status"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Начать игру",
                    callback_data="start_private_game"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚪 Выйти",
                    callback_data=f"leave_room:{room_id}"
                )
            ]
        ]
    )
