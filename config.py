import os

class Config:
    API_TOKEN = os.getenv('API_TOKEN')  # Telegram API-Token aus den Heroku Config Vars
    ADMIN_ID = os.getenv('ADMIN_ID')    # Deine Telegram-ID für Admin-Befehle
