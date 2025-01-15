from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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
