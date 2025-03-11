import logging
from pymysql import Error
from dotenv import load_dotenv
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()

def create_table(connection):
    try:
        cursor = connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS players (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,    -- ID игрока, автоинкремент
                score INT DEFAULT 0,                   -- Количество очков (начальное значение 0)
                correct_answers INT DEFAULT 0,         -- Количество правильных ответов (начальное значение 0)
                wrong_answers INT DEFAULT 0,           -- Количество неправильных ответов (начальное значение 0)
                wins INT DEFAULT 0,                    -- Количество побед (начальное значение 0)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Время создания записи
            );
        """
        cursor.execute(create_table_query)

        # Создание таблицы вопросов
        create_questions_table_query = """
                    CREATE TABLE IF NOT EXISTS questions (
                        id INT AUTO_INCREMENT PRIMARY KEY,     -- ID вопроса
                        question TEXT NOT NULL,                 -- Вопрос викторины
                        correct_answer TEXT NOT NULL,           -- Правильный ответ
                        wrong_answer_1 TEXT,                    -- Неправильный ответ 1
                        wrong_answer_2 TEXT,                    -- Неправильный ответ 2
                        wrong_answer_3 TEXT,                    -- Неправильный ответ 3
                        wrong_answer_4 TEXT,                    -- Неправильный ответ 4 (опционально)
                        wrong_answer_5 TEXT,                    -- Неправильный ответ 5 (опционально)
                        wrong_answer_6 TEXT,                    -- Неправильный ответ 6 (опционально)
                        wrong_answer_7 TEXT,                    -- Неправильный ответ 7 (опционально)
                        wrong_answer_8 TEXT,                    -- Неправильный ответ 8 (опционально)
                        wrong_answer_9 TEXT,                    -- Неправильный ответ 9 (опционально)
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Время создания вопроса
                    );
        """

        cursor.execute(create_questions_table_query)

        # Создание таблицы комнат
        create_table_rooms = """
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор комнаты
                player1_id BIGINT DEFAULT NULL,     -- ID первого игрока
                player2_id BIGINT DEFAULT NULL,     -- ID второго игрока
                player3_id BIGINT DEFAULT NULL,     -- ID третьего игрока
                player4_id BIGINT DEFAULT NULL,     -- ID четвертого игрока
                question_id INT NOT NULL,           -- ID текущего вопроса
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Время создания комнаты
            );
        """

        cursor.execute(create_table_rooms)

        # Фиксируем изменения
        connection.commit()
        logging.info("Таблицы 'players', 'questions', 'rooms' созданы успешно")

    except Error as e:
        logging.error(f"Ошибка создания таблицы: {e}")
