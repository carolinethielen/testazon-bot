import os
import logging
import time
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update
)
from telegram.constants import ParseMode  # Änderung hier
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    filters, 
    ContextTypes
)

# 🌍 --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔐 --- Load sensitive data from environment variables ---
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN or not ADMIN_ID:
    raise RuntimeError("❌ API_TOKEN oder ADMIN_ID fehlt in den Umgebungsvariablen!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("❌ ADMIN_ID muss eine Zahl sein!")

# 🌐 --- Conversation states ---
AMAZON_PROFILE, PAYPAL_EMAIL, VERIFY_PROFILE = range(3)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"User {user.first_name} started the bot.")

    # Send the main menu with options
    keyboard = [
        [InlineKeyboardButton("📥 Gebe deine PayPal Email ein", callback_data="paypal_email"),
         InlineKeyboardButton("🛒 Amazon Profil bearbeiten", callback_data="amazon_profile")],
        [InlineKeyboardButton("🔄 Überprüfen des Amazon Profils", callback_data="verify_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen im Testazon Bot! Wähle eine Option:", reply_markup=reply_markup)

    return AMAZON_PROFILE

# PayPal Email Eingabe
async def enter_paypal_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Ask for PayPal email
    await query.edit_message_text("Bitte gib deine PayPal Email-Adresse ein:")

    return PAYPAL_EMAIL

# Amazon Profil bearbeiten
async def edit_amazon_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Ask for Amazon profile link
    await query.edit_message_text("Bitte gib deinen Amazon Profil-Link ein:")

    return AMAZON_PROFILE

# Verifizieren des Amazon Profils (mit Ladebalken)
async def verify_amazon_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Show progress bar for verification
    await query.edit_message_text("🔄 Dein Amazon Profil wird jetzt überprüft. Einen Moment bitte...")

    for i in range(101):
        time.sleep(0.05)  # Simulate verification time
        progress_bar = "⬛" * (i // 10) + "⚪" * (10 - i // 10)
        await query.edit_message_text(f"🔄 Verifizierung läuft...\n\n{progress_bar} {i}%")

    # After verification is done
    await query.edit_message_text("✅ Dein Amazon Profil wurde erfolgreich verifiziert!")

    # Ask if they want to edit their profile again
    keyboard = [
        [InlineKeyboardButton("🔄 Amazon Profil ändern", callback_data="amazon_profile"),
         InlineKeyboardButton("✉️ PayPal Email ändern", callback_data="paypal_email")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Möchtest du dein Profil ändern?", reply_markup=reply_markup)

    return AMAZON_PROFILE

# Handle text messages (just in case the user types something)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"User {update.message.from_user.first_name} sent: {user_message}")

    await update.message.reply_text("Bitte benutze die Buttons, um fortzufahren.")

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"User {user.first_name} cancelled the conversation.")
    
    await update.message.reply_text("Die Konversation wurde abgebrochen. Wenn du Hilfe benötigst, kannst du jederzeit wieder starten!")

    return ConversationHandler.END

# Main function to set up the application
async def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AMAZON_PROFILE: [
                CallbackQueryHandler(edit_amazon_profile, pattern="amazon_profile"),
                CallbackQueryHandler(enter_paypal_email, pattern="paypal_email"),
                CallbackQueryHandler(verify_amazon_profile, pattern="verify_profile"),
            ],
            PAYPAL_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            VERIFY_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Run the bot
    await app.run_polling()

if __name__ == "__main__":
    app = ApplicationBuilder().token("API_TOKEN").build()
    app.run_polling()
