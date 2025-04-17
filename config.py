import os

class Config:
    API_TOKEN = os.getenv('8137004758:AAHaBW6aZwoMTn60rR9gK_FXqJ_69bEydMQ')  # Telegram API-Token aus den Heroku Config Vars
    ADMIN_ID = os.getenv('6014547283')    # Deine Telegram-ID für Admin-Befehle
