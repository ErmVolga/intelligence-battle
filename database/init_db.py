import logging
from pymysql import Error
from dotenv import load_dotenv
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()


def create_table(connection):
    try:
        cursor = connection.cursor()

        # Создаем таблицу вопросов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                wrong_answer_1 TEXT,
                wrong_answer_2 TEXT,
                wrong_answer_3 TEXT,
                wrong_answer_4 TEXT,
                wrong_answer_5 TEXT,
                wrong_answer_6 TEXT,
                wrong_answer_7 TEXT,
                wrong_answer_8 TEXT,
                wrong_answer_9 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.info("Таблица 'questions' создана")

        # Создаем таблицу комнат (rooms)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player1_id BIGINT DEFAULT NULL,
                player2_id BIGINT DEFAULT NULL,
                player3_id BIGINT DEFAULT NULL,
                player4_id BIGINT DEFAULT NULL,
                question_id INT NOT NULL,
                is_private BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_timer_time TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)
        logging.info("Таблица 'rooms' создана")

        # ✅ Создаем таблицу игроков (players) — БЕЗ внешнего ключа на rooms!
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id BIGINT PRIMARY KEY,
                score INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                wrong_answers INT DEFAULT 0,
                wins INT DEFAULT 0,
                current_room_id INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.info("Таблица 'players' создана без FOREIGN KEY")

        # Создаем таблицу игровых сессий
        create_game_sessions_table = """
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_id INT NOT NULL,
            round_number INT DEFAULT 1,
            current_question_id INT DEFAULT NULL,
            status ENUM('waiting', 'active', 'finished') DEFAULT 'waiting',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_game_sessions_table)
        logging.info("Таблица 'game_sessions' создана")

        # Таблица участников внутри игры
        create_game_players_table = """
        CREATE TABLE IF NOT EXISTS game_players (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_id INT NOT NULL,
            user_id BIGINT NOT NULL,
            score INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            is_banked BOOLEAN DEFAULT FALSE,
            last_answer_correct BOOLEAN DEFAULT NULL,
            answered_this_round BOOLEAN DEFAULT FALSE
        );
        """
        cursor.execute(create_game_players_table)
        logging.info("Таблица 'game_players' создана")

        # Добавляем тестовые вопросы
        cursor.execute("SELECT COUNT(*) FROM questions")
        if cursor.fetchone()[0] == 0:
            test_questions = [
                ("Столица Франции?", "Париж", "Лондон", "Берлин", "Мадрид"),
                ("2 + 2?", "4", "5", "3", "22")
            ]
            cursor.executemany(
                "INSERT INTO questions (question, correct_answer, wrong_answer_1, wrong_answer_2, wrong_answer_3) VALUES (%s, %s, %s, %s, %s)",
                test_questions
            )
            connection.commit()
            logging.info("Тестовые вопросы добавлены")

        connection.commit()

    except Error as e:
        logging.error(f"Ошибка создания таблиц: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()
