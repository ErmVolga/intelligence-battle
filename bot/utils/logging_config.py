import logging

def setup_logging():
    logging.basicConfig(
        filename="app.log",               # Файл для записи логов
        level=logging.DEBUG,              # Уровень логирования
        format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",  # Формат записи
        filemode="a",                      # Режим добавления в файл
        encoding='utf-8'                   # Кодировка для поддержки Unicode
    )