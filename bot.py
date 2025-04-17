import os
import logging
import re
import asyncio
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, Update, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)
from flask import Flask, request
from telegram import Bot

# Flask App für Webhooks
app = Flask(__name__)

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Lade Umgebungsvariablen
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN or not ADMIN_ID or not WEBHOOK_URL:
    raise RuntimeError("❌ API_TOKEN, ADMIN_ID oder WEBHOOK_URL fehlen in den Umgebungsvariablen!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("❌ ADMIN_ID muss eine Zahl sein!")

# States
(MENU, ENTER_PAYPAL, ENTER_AMAZON, UPLOAD_PROFILE, PROFILE_CHANGE, SUPPORT) = range(6)

# RAM-Datenbank (nur temporär!)
users = {}

# Menü-Tastatur
def main_menu_keyboard():
    return ReplyKeyboardMarkup([  
        ["🛍️ Verfügbare Produkte", "📦 Aktive Bestellungen"],
        ["💸 Rückerstattungsstatus", "📜 Regeln & Infos"],
        ["🆘 Support", "🔄 Profil ändern"]
    ], resize_keyboard=True)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {"paypal": None, "amazon_link": None, "profile_pic": None, "orders": []}
    await update.message.reply_text("👋 Willkommen bei Testazon!\n\nBitte gib deine PayPal-E-Mail ein:")
    return ENTER_PAYPAL

# PayPal E-Mail
async def enter_paypal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text("❌ Ungültige E-Mail. Bitte versuch's nochmal:")
        return ENTER_PAYPAL

    user_id = update.effective_user.id
    users[user_id]["paypal"] = email
    await update.message.reply_text("✅ PayPal gespeichert!\n\nBitte sende jetzt deinen Amazon-Profillink:")
    return ENTER_AMAZON

# Amazon-Link
async def enter_amazon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    if not re.match(r"https://www\.amazon\.de/gp/profile/amzn1\.account\.[A-Za-z0-9]+", link):
        await update.message.reply_text("❌ Ungültiger Link. Bitte sende deinen korrekten Amazon-Profil-Link.")
        return ENTER_AMAZON

    user_id = update.effective_user.id
    users[user_id]["amazon_link"] = link
    verification = await update.message.reply_text("🔍 Profil wird geprüft...")

    for i in range(1, 11):
        await asyncio.sleep(1)  # Verlangsamt die Schleife
        bar = "█" * i + "░" * (10 - i)
        await verification.edit_text(f"🔍 Prüfung... {bar}")
    
    await verification.edit_text("✅ Amazon-Link verifiziert!")
    await update.message.reply_text("📸 Bitte sende jetzt einen Screenshot deines Amazon-Profils.")
    return UPLOAD_PROFILE

# Profilbild
async def upload_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not update.message.photo:
        await update.message.reply_text("❌ Bitte sende ein *Bild* deines Profils.")
        return UPLOAD_PROFILE

    users[user_id]["profile_pic"] = update.message.photo[-1].file_id
    verification = await update.message.reply_text("🔍 Bild wird überprüft...")

    for i in range(1, 11):
        await asyncio.sleep(1)  # Verlangsamt die Schleife
        bar = "█" * i + "░" * (10 - i)
        await verification.edit_text(f"🔍 Bildprüfung... {bar}")

    await verification.edit_text("✅ Profil erfolgreich verifiziert!")
    await update.message.reply_text("🎉 Du kannst jetzt mit dem Produkttest starten!", reply_markup=main_menu_keyboard())
    return MENU

# Flask Webhook-Handler
@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = Update.de_json(json_str, Bot(API_TOKEN))
    application.process_update(update)
    return "OK"

# Webhook setzen
def set_webhook():
    bot = Bot(API_TOKEN)
    webhook_url = f"{WEBHOOK_URL}/{API_TOKEN}"
    bot.set_webhook(webhook_url)
    logging.info(f"Webhook gesetzt auf {webhook_url}")

if __name__ == "__main__":
    # Webhook setzen
    set_webhook()

    # Startet den Flask-Server und den Bot
    from threading import Thread
    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    # Flask-Server in einem separaten Thread starten
    thread = Thread(target=run_flask)
    thread.start()

    # Initialisiere den Bot
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Definiere die Handlers
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_PAYPAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_paypal)],
            ENTER_AMAZON: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amazon)],
            UPLOAD_PROFILE: [MessageHandler(filters.PHOTO, upload_profile)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        },
        fallbacks=[],
    ))

    # Setzt den Webhook über Flask
    set_webhook()

    # Hält den Bot in einem laufenden Zustand
    application.run_polling(drop_pending_updates=True)
