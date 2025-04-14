import asyncio
import random
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.db import create_connection

class GameEngine:
    def __init__(self, room_id: int, bot):
        self.room_id = room_id
        self.bot = bot
        self.message_ids = {}  # user_id: message_id
        self.current_question = None
        self.answer_mapping = {}  # answer_text: is_correct
        self.players = []
        self.answers = {}  # user_id: 'answer' / 'bank' / None
        self.round_number = 1

    async def start_game(self):
        await self.load_active_players()
        await self.start_round()

    async def load_active_players(self):
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
        self.current_question = await self.get_random_question()
        self.answer_mapping = self.shuffle_answers(self.current_question)
        self.answers = {pid: None for pid in self.players}

        question_text = f"<b>Вопрос №{self.round_number}</b>\n\n"
        question_text += f"{self.current_question['question']}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=ans, callback_data=f"answer:{ans}")]
                for ans in self.answer_mapping.keys()
            ] + [[InlineKeyboardButton(text="💰 Банк", callback_data="bank")]]
        )

        for user_id in self.players:
            msg = await self.bot.send_message(user_id, question_text, reply_markup=keyboard)
            self.message_ids[user_id] = msg.message_id

        asyncio.create_task(self.round_timer())

    async def round_timer(self):
        for _ in range(20):
            if all(v is not None for v in self.answers.values()):
                break
            await asyncio.sleep(1)
        await self.finish_round()

    async def handle_answer(self, user_id: int, answer_text: str):
        if self.answers.get(user_id) is not None:
            return  # уже ответил

        if answer_text == "bank":
            self.answers[user_id] = "bank"
            await self.mark_player_banked(user_id)
            return

        is_correct = self.answer_mapping.get(answer_text, False)
        self.answers[user_id] = ("correct" if is_correct else "wrong")

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE game_players
                    SET answered_this_round = TRUE,
                        last_answer_correct = %s,
                        score = score + CASE WHEN %s THEN 100 ELSE 0 END
                    WHERE user_id = %s AND room_id = %s
                """, (is_correct, is_correct, user_id, self.room_id))
                connection.commit()
            finally:
                connection.close()

    async def mark_player_banked(self, user_id: int):
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE game_players
                    SET is_banked = TRUE,
                        is_active = FALSE
                    WHERE user_id = %s AND room_id = %s
                """, (user_id, self.room_id))
                connection.commit()
            finally:
                connection.close()

    async def finish_round(self):
        connection = create_connection()
        eliminated = []
        survivors = []
        banker_ids = []

        if connection:
            try:
                cursor = connection.cursor()

                # Получаем всех игроков
                cursor.execute("""
                    SELECT user_id, score, is_banked, last_answer_correct, is_active
                    FROM game_players
                    WHERE room_id = %s
                """, (self.room_id,))
                data = cursor.fetchall()

                # Ищем минимальный балл среди активных
                scores = [row[1] for row in data if row[4]]
                min_score = min(scores) if scores else 0

                for user_id, score, is_banked, correct, is_active in data:
                    if is_banked:
                        banker_ids.append(user_id)
                    elif is_active:
                        if score == min_score and not correct:
                            eliminated.append(user_id)
                        else:
                            survivors.append(user_id)

                # Выкидываем проигравших
                for user_id in eliminated:
                    cursor.execute("""
                        UPDATE game_players SET is_active = FALSE WHERE user_id = %s AND room_id = %s
                    """, (user_id, self.room_id))
                connection.commit()
            finally:
                connection.close()

        # Показываем итоги всем
        for user_id in self.players:
            status = self.answers.get(user_id)
            if status == "bank":
                symbol = "💰"
            elif status == "correct":
                symbol = "✅"
            elif status == "wrong":
                symbol = "❌"
            else:
                symbol = "⏳"

            text = f"<b>Раунд завершён</b>\nВы: {symbol}"
            if user_id in eliminated:
                text += "\n\n<b>Вы выбыли из игры!</b>"
            elif user_id in banker_ids:
                text += "\n\nВы вышли в банк — очки сохранены."

            await self.bot.send_message(user_id, text)

        # Проверка — сколько игроков осталось
        await self.load_active_players()
        if len(self.players) == 1:
            self.round_number += 1
            await self.start_round()
        elif len(self.players) == 0:
            await self.bot.send_message(self.room_id, "Игра завершена.")
        else:
            self.round_number += 1
            await self.start_round()

    async def get_random_question(self):
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
        all_answers = [question_data["correct"]] + question_data["wrong"]
        random.shuffle(all_answers)
        return {ans: (ans == question_data["correct"]) for ans in all_answers}
