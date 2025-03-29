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
        # Проверяем, существует ли уже пользователь с таким id
        cursor = connection.cursor()
        check_query = "SELECT * FROM players WHERE id = %s"
        cursor.execute(check_query, (user_id,))
        result = cursor.fetchone()

        if result:
            # Если пользователь уже существует, логируем это
            logging.info(f"Пользователь с id {user_id} уже существует в базе данных.")
        else:
            # Если пользователя нет, добавляем его
            insert_query = """
                INSERT INTO players (id, score, correct_answers, wrong_answers, wins)
                VALUES (%s, %s, %s, %s, %s);
            """
            values = (user_id, 0, 0, 0, 0)  # Добавляем только необходимые значения

            cursor.execute(insert_query, values)
            connection.commit()
            logging.info(f"Игрок с id {user_id} добавлен в таблицу")

    except Error as e:
        logging.error(f"Ошибка при добавлении данных для пользователя с id {user_id}: {e}")
