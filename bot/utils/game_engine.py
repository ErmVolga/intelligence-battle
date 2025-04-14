import asyncio
import random
import logging
from bot.utils.db import create_connection
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class GameEngine:
    def __init__(self, room_id: int, bot):
        self.room_id = room_id
        self.bot = bot
        self.message_ids = {}  # user_id: message_id
        self.current_question = None
        self.answer_mapping = {}  # answer_text: is_correct
        self.players = []

    async def load_players(self):
        """Загружает игроков комнаты"""
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT user_id FROM game_players 
                    WHERE room_id = %s AND is_active = TRUE
                """, (self.room_id,))
                self.players = [row[0] for row in cursor.fetchall()]
            finally:
                connection.close()

    async def start_round(self):
        """Начинает раунд: отправляет вопрос и кнопки игрокам"""
        await self.load_players()
        self.current_question = await self.get_random_question()
        self.answer_mapping = self.shuffle_answers(self.current_question)

        for user_id in self.players:
            await self.send_question(user_id)

        # запускаем таймер
        asyncio.create_task(self.round_timer())

    async def round_timer(self):
        """Ожидание ответов 20 сек"""
        await asyncio.sleep(20)
        await self.finish_round()

    async def send_question(self, user_id: int):
        """Отправляет игроку вопрос с кнопками"""
        text = f"Вопрос\n\n{self.current_question['question']}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=txt, callback_data=f"answer:{txt}")]
                for txt in self.answer_mapping.keys()
            ] + [[InlineKeyboardButton(text="💰 Банк", callback_data="bank")]]
        )
        msg = await self.bot.send_message(user_id, text, reply_markup=keyboard)
        self.message_ids[user_id] = msg.message_id

    async def handle_answer(self, user_id: int, answer_text: str):
        """Обработка ответа игрока"""
        is_correct = self.answer_mapping.get(answer_text, False)

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE game_players
                    SET last_answer_correct = %s,
                        answered_this_round = TRUE,
                        score = score + CASE WHEN %s THEN 100 ELSE 0 END
                    WHERE user_id = %s AND room_id = %s
                """, (is_correct, is_correct, user_id, self.room_id))
                connection.commit()
            finally:
                connection.close()

    async def finish_round(self):
        """Завершает раунд и проверяет выбывание"""
        # Здесь будет логика определения, кто выбывает и кто продолжает
        # И запуск следующего раунда или завершение игры
        pass

    async def get_random_question(self):
        """Получает случайный вопрос из БД"""
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 1")
                row = cursor.fetchone()
                return {
                    "id": row[0],
                    "question": row[1],
                    "correct": row[2],
                    "wrong": [x for x in row[3:12] if x]
                }
            finally:
                connection.close()

    def shuffle_answers(self, question_data):
        """Перемешивает ответы"""
        all_answers = [question_data["correct"]] + question_data["wrong"]
        random.shuffle(all_answers)
        return {ans: (ans == question_data["correct"]) for ans in all_answers}
