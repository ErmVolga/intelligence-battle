import os
import logging
import pymysql
from pymysql import Error
from dotenv import load_dotenv
from bot.utils.logging_config import setup_logging

setup_logging()
load_dotenv()

def create_connection():
    try:
        host = os.getenv("DB_host")
        user = os.getenv("DB_user")
        password = os.getenv("DB_password")
        database_name = os.getenv("DB_database")
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database_name
        )
        #logging.info("Подключение к базе данных 1 (информация о пользователях) успешно установлено.")
        return connection
    except Error as e:
        logging.error(f"Ошибка подключения к базе данных 1: {e}")
        return None



def insert_players(connection, user_id):
    try:
        cursor = connection.cursor()
        check_query = "SELECT * FROM players WHERE id = %s"
        cursor.execute(check_query, (user_id,))
        result = cursor.fetchone()

        if not result:
            insert_query = """
                INSERT INTO players (id, score, correct_answers, wrong_answers, wins)
                VALUES (%s, 0, 0, 0, 0);
            """
            cursor.execute(insert_query, (user_id,))
            connection.commit()
            logging.info(f"Игрок {user_id} добавлен в таблицу players")
    except Error as e:
        logging.error(f"Ошибка при добавлении игрока {user_id}: {e}")
    finally:
        if cursor:
            cursor.close()
