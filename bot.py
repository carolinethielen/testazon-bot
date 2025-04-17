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

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Lade Umgebungsvariablen
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN or not ADMIN_ID:
    raise RuntimeError("❌ API_TOKEN oder ADMIN_ID fehlt in den Umgebungsvariablen!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("❌ ADMIN_ID muss eine Zahl sein!")

# States
(MENU, ENTER_PAYPAL, ENTER_AMAZON, UPLOAD_PROFILE) = range(4)

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
        await asyncio.sleep(0.5)
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
        await asyncio.sleep(0.5)
        bar = "█" * i + "░" * (10 - i)
        await verification.edit_text(f"🔍 Bildprüfung... {bar}")

    await verification.edit_text("✅ Profil erfolgreich verifiziert!")
    await update.message.reply_text("🎉 Du kannst jetzt mit dem Produkttest starten!", reply_markup=main_menu_keyboard())
    return MENU

# Menü: Verfügbare Produkte
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not users[user_id]["paypal"] or not users[user_id]["profile_pic"]:
        await update.message.reply_text("⚠️ Bitte verifiziere zuerst dein Profil mit /start.")
        return MENU

    keyboard = [
        [InlineKeyboardButton("🧴 Produkt 1 – ID: 1234", callback_data="order_1234")],
        [InlineKeyboardButton("🎧 Produkt 2 – ID: 5678", callback_data="order_5678")]
    ]
    await update.message.reply_text("🛍️ Hier sind deine Produkte:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# Produktauswahl
async def handle_order_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    product_id = query.data.replace("order_", "")
    users[user_id]["orders"].append({"id": product_id, "status": "🕒 Ausstehend"})
    await query.edit_message_text(f"✅ Produkt *{product_id}* ausgewählt. Bitte bestelle es und sende danach den Rezensionslink.", parse_mode="Markdown")
    return MENU

# Aktive Bestellungen
async def active_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = users[user_id]["orders"]
    if not orders:
        await update.message.reply_text("📭 Keine aktiven Bestellungen.")
    else:
        msg = "📦 *Deine Bestellungen:*\n\n" + "\n".join([f"- ID: `{o['id']}` – Status: {o['status']}" for o in orders])
        await update.message.reply_text(msg, parse_mode="Markdown")
    return MENU

# Rückerstattung
async def refund_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💸 Deine Rückerstattung ist *in Bearbeitung*.\nBitte hab etwas Geduld.", parse_mode="Markdown")
    return MENU

# Regeln
async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 Regeln:\n1. Bestelle nur verifizierte Produkte\n2. Kein Betrug\n3. Rückerstattung nach Bewertung.")
    return MENU

# Bot-Setup
def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_PAYPAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_paypal)],
            ENTER_AMAZON: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amazon)],
            UPLOAD_PROFILE: [MessageHandler(filters.PHOTO, upload_profile)],
            MENU: [
                MessageHandler(filters.Regex("🛍️ Verfügbare Produkte"), show_products),
                MessageHandler(filters.Regex("📦 Aktive Bestellungen"), active_orders),
                MessageHandler(filters.Regex("💸 Rückerstattungsstatus"), refund_status),
                MessageHandler(filters.Regex("📜 Regeln & Infos"), show_rules),
            ],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_order_selection))

    app.run_polling()

if __name__ == "__main__":
    main()
