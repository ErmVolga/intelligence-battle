import logging
import os
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
        logging.info("Подключение к базе данных 1 (информация о пользователях) успешно установлено.")
        return connection
    except Error as e:
        logging.error(f"Ошибка подключения к базе данных 1: {e}")
        return None

def drop_table(connection):
    try:
        cursor = connection.cursor()
        # Удаляем таблицу players
        drop_table_query = "DROP TABLE IF EXISTS players;"
        cursor.execute(drop_table_query)
        connection.commit()
        logging.info("Таблица 'players' удалена успешно.")
    except Error as e:
        logging.error(f"Ошибка удаления таблицы: {e}")

if __name__ == "__main__":
    connection = create_connection()
    if connection:
        drop_table(connection)
        connection.close()
