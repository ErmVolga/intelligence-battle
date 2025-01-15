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
        connection.commit()
        logging.info("Таблица 'players' создана успешно")
    except Error as e:
        logging.error(f"Ошибка создания таблицы: {e}")
