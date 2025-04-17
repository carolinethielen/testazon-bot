import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
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

# 🔐 --- Load sensitive data from environment variables ---
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN or not ADMIN_ID:
    raise RuntimeError("❌ API_TOKEN oder ADMIN_ID fehlt in den Umgebungsvariablen!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("❌ ADMIN_ID muss eine Zahl sein!")

# 🔢 --- States for Conversation ---
(
    MENU,
    ENTER_PAYPAL,
    ENTER_AMAZON,
    UPLOAD_PROFILE,
    PRODUCT_SELECTION,
    REVIEW_UPLOAD
) = range(6)

# 📁 --- Benutzerdaten (im RAM, du kannst das später in DB auslagern) ---
users = {}

# 🔘 --- Hauptmenü Buttons ---
def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍️ Verfügbare Produkte", "📦 Aktive Bestellungen"],
        ["💸 Rückerstattungsstatus", "📜 Regeln & Infos"],
        ["🆘 Support"]
    ], resize_keyboard=True)

# 🧠 --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = users.get(user_id, {
        "paypal": None,
        "amazon_link": None,
        "profile_pic": None,
        "orders": []
    })

    await update.message.reply_text(
        "👋 Willkommen bei *Testazon Produkttests!* \n\n"
        "Bitte gib zuerst deine PayPal E-Mail-Adresse ein, um fortzufahren:",
        parse_mode="Markdown"
    )
    return ENTER_PAYPAL

# 💳 --- PayPal Adresse erfassen ---
async def enter_paypal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Bitte gib eine gültige PayPal E-Mail-Adresse ein.")
        return ENTER_PAYPAL

    user_id = update.effective_user.id
    users[user_id]["paypal"] = email
    await update.message.reply_text("✅ PayPal E-Mail gespeichert!\n\n📸 Bitte sende jetzt einen Screenshot deines *Amazon-Profils*.")
    return UPLOAD_PROFILE

# 🖼️ --- Profilbild speichern ---
async def upload_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text("❌ Bitte sende ein Bild deines Amazon-Profils.")
        return UPLOAD_PROFILE

    photo_file_id = update.message.photo[-1].file_id
    users[user_id]["profile_pic"] = photo_file_id
    await update.message.reply_text("✅ Amazon-Profilbild gespeichert!", reply_markup=main_menu_keyboard())
    return MENU

# 🛍️ --- Verfügbare Produkte ---
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not users[user_id]["paypal"] or not users[user_id]["profile_pic"]:
        await update.message.reply_text("⚠️ Bitte gib zuerst deine PayPal-E-Mail und dein Amazon-Profilbild ein mit /start.")
        return MENU

    keyboard = [
        [InlineKeyboardButton("🧴 Produkt 1 – ID: 1234", callback_data='order_1234')],
        [InlineKeyboardButton("🎧 Produkt 2 – ID: 5678", callback_data='order_5678')],
    ]
    await update.message.reply_text("🛍️ Verfügbare Produkte:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

# 📝 --- Callback für Produktauswahl ---
async def handle_order_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    product_id = query.data.replace("order_", "")
    users[user_id]["orders"].append({"id": product_id, "status": "🕒 Ausstehend"})

    await query.edit_message_text(
        text=f"✅ Du hast Produkt *{product_id}* ausgewählt.\n"
             f"Bitte bestelle das Produkt und sende danach den *Rezensionslink* sowie ein Bild!",
        parse_mode="Markdown"
    )
    return MENU

# 📦 --- Aktive Bestellungen anzeigen ---
async def active_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = users[user_id].get("orders", [])
    if not orders:
        await update.message.reply_text("📭 Du hast aktuell keine aktiven Bestellungen.")
    else:
        msg = "📦 *Deine aktiven Bestellungen:*\n\n"
        for order in orders:
            msg += f"- Produkt-ID: `{order['id']}` – Status: {order['status']}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    return MENU

# 🔁 --- Rückerstattungsstatus ---
async def refund_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Deine Rückerstattung ist *in Bearbeitung*. Bitte hab etwas Geduld.")
    return MENU

# 📜 --- Regeln & Infos ---
async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *Regeln für Produkttests:*\n"
        "- Nur 1 Produkt gleichzeitig testen\n"
        "- Ehrliche Rezension schreiben\n"
        "- Rückerstattung nach Prüfung durch den Händler\n"
        "- PayPal & Amazon-Profil müssen gültig sein\n"
        "- Keine Fake-Bewertungen!",
        parse_mode="Markdown"
    )
    return MENU

# 🆘 --- Support ---
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Bei Fragen schreibe bitte an: support@testazon.com")
    return MENU

# 🧼 --- Fallback / Unbekannte Nachrichten ---
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Bitte nutze die Buttons oder starte mit /start neu.")

# 🧠 --- Main Funktion ---
def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_PAYPAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_paypal)],
            UPLOAD_PROFILE: [MessageHandler(filters.PHOTO, upload_profile)],
            MENU: [
                MessageHandler(filters.Regex("🛍️ Verfügbare Produkte"), show_products),
                MessageHandler(filters.Regex("📦 Aktive Bestellungen"), active_orders),
                MessageHandler(filters.Regex("💸 Rückerstattungsstatus"), refund_status),
                MessageHandler(filters.Regex("📜 Regeln & Infos"), show_rules),
                MessageHandler(filters.Regex("🆘 Support"), support)
            ]
        },
        fallbacks=[MessageHandler(filters.ALL, fallback)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_order_selection))

    print("🤖 Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
