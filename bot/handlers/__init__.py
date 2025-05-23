from .commands import router as commands_router  # роутер команд
from .admin import router as admin_router  # роутер админ панели
from .game import router as game_router  # Подключаем роутер из game.py
from .help import router as help_router

# Экспортируем все роутеры
__all__ = ["commands_router", "admin_router", "game_router", "help_router"]