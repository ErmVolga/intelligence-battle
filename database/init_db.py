import logging
from pymysql import Error
from dotenv import load_dotenv
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()


def create_table(connection):
    try:
        cursor = connection.cursor()

        # Создаем таблицу вопросов (должна быть первой, так как на нее есть ссылки)
        create_questions_table_query = """
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            wrong_answer_1 TEXT,
            wrong_answer_2 TEXT,
            wrong_answer_3 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_questions_table_query)

        # Создаем таблицу комнат
        create_table_rooms = """
        CREATE TABLE IF NOT EXISTS rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            player1_id BIGINT DEFAULT NULL,
            player2_id BIGINT DEFAULT NULL,
            player3_id BIGINT DEFAULT NULL,
            player4_id BIGINT DEFAULT NULL,
            question_id INT NOT NULL,
            is_private BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  # Уже есть
            start_timer_time TIMESTAMP DEFAULT NULL  # Добавляем новое поле
        );
        """
        cursor.execute(create_table_rooms)

        # Создаем таблицу игроков
        create_table_query = """
        CREATE TABLE IF NOT EXISTS players (
            id BIGINT PRIMARY KEY,
            score INT DEFAULT 0,
            correct_answers INT DEFAULT 0,
            wrong_answers INT DEFAULT 0,
            wins INT DEFAULT 0,
            current_room_id INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (current_room_id) REFERENCES rooms(id) ON DELETE SET NULL
        );
        """
        cursor.execute(create_table_query)

        connection.commit()
        logging.info("Таблицы 'questions', 'rooms' и 'players' созданы успешно")

        # Добавляем тестовые данные, если таблицы пустые
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
            logging.info("Добавлены тестовые вопросы")

    except Error as e:
        logging.error(f"Ошибка создания таблиц: {e}")
        connection.rollback()
        raise
