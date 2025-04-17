import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext
from telegram.ext import Updater

# API-Token und Admin-ID als Umgebungsvariablen festlegen
API_TOKEN = os.getenv("API_TOKEN")  # Token aus der Umgebungsvariable
ADMIN_ID = os.getenv("ADMIN_ID")    # Admin-ID aus der Umgebungsvariable

# Sicherstellen, dass der API-Token und die Admin-ID gesetzt sind
if not API_TOKEN or not ADMIN_ID:
    raise ValueError("API_TOKEN oder ADMIN_ID wurde nicht gesetzt!")

# Status-Konstanten für den ConversationHandler
PRODUCT_SELECTION, PAYPAL_EMAIL, AMAZON_LINK, PRODUCT_ORDER, REVIEW_UPLOAD = range(5)

# Einfache Produkt-Datenbank (simuliert)
# Du kannst dies später durch ein API oder eine Datenbankabfrage ersetzen
products = {
    "123": {"name": "Smartphone", "price": 199.99},
    "124": {"name": "Laptop", "price": 999.99},
    "125": {"name": "Kopfhörer", "price": 59.99},
}

# Start Funktion
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text(
        f"Hallo {user.first_name}, willkommen bei Testazon! Ich kann dir helfen, Produkte zu kaufen und Rezensionen zu hinterlassen, um eine Rückerstattung vom Händler zu erhalten. "
        "Lass uns loslegen!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Verfügbare Produkte", callback_data="view_products"),
        ]])
    )
    return PRODUCT_SELECTION

# Funktion, um die verfügbaren Produkte anzuzeigen
def view_products(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"{product['name']} - ${product['price']}", callback_data=product_id)]
        for product_id, product in products.items()
    ]
    keyboard.append([InlineKeyboardButton("Abbrechen", callback_data="cancel")])

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        "Wähle ein Produkt aus:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return PAYPAL_EMAIL

# Funktion, um die PayPal-E-Mail vom Nutzer zu erhalten
def request_paypal_email(update: Update, context: CallbackContext):
    context.user_data["product_id"] = update.callback_query.data
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        "Bitte gib deine PayPal-E-Mail-Adresse ein, um fortzufahren:"
    )
    return PAYPAL_EMAIL

# Funktion, um die Amazon-Profil-Link vom Nutzer zu erhalten
def request_amazon_link(update: Update, context: CallbackContext):
    context.user_data["paypal_email"] = update.message.text
    update.message.reply_text(
        "Danke! Jetzt gib bitte deinen Amazon-Profil-Link ein:"
    )
    return AMAZON_LINK

# Funktion, um das Produkt zu bestellen
def order_product(update: Update, context: CallbackContext):
    context.user_data["amazon_link"] = update.message.text
    product_id = context.user_data["product_id"]
    product = products.get(product_id)
    
    # Bestellbestätigung
    update.message.reply_text(
        f"Du hast das Produkt **{product['name']}** bestellt. "
        "Wir prüfen deine PayPal-E-Mail und Amazon-Profil-Link und geben dir dann den Link zum Produkt, das du bewerten kannst."
    )

    # Rückerstattungsprozess und Verifizierung durch Admin (Nachricht an Admin)
    admin_message = f"Neuer Bestellvorgang: {product['name']}\n" \
                    f"Produkt ID: {product_id}\n" \
                    f"PayPal E-Mail: {context.user_data['paypal_email']}\n" \
                    f"Amazon Profil Link: {context.user_data['amazon_link']}\n" \
                    f"Benutzer-ID: {update.message.from_user.id}\n" \
                    f"Verifizierung erforderlich!"
    
    # Sende Nachricht an Admin
    context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    
    update.message.reply_text(
        "Bitte warte auf die Verifizierung. Du wirst benachrichtigt, sobald deine Bestellung abgeschlossen ist."
    )

    return REVIEW_UPLOAD

# Funktion, um die Rezension und das Bild hochzuladen
def upload_review(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Bitte lade deinen Amazon-Rezensionslink und ein Bild deines Produkts hoch. "
        "Sobald dies erledigt ist, erhältst du die Rückerstattung vom Händler."
    )
    return ConversationHandler.END

# Abbruch-Handler
def cancel(update: Update, context: CallbackContext):
    update.callback_query.answer()
    update.callback_query.edit_message_text("Der Vorgang wurde abgebrochen.")
    return ConversationHandler.END

# Hauptfunktion, die den Bot startet
def main():
    # Erstelle den Updater mit dem API-Token
    updater = Updater(API_TOKEN)

    # Dispatcher für die Bearbeitung von Nachrichten
    dispatcher = updater.dispatcher

    # ConversationHandler zur Steuerung des Gesprächsflusses
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCT_SELECTION: [CallbackQueryHandler(view_products, pattern="^view_products$")],
            PAYPAL_EMAIL: [CallbackQueryHandler(request_paypal_email, pattern=r"^\d{3,5}$")],
            AMAZON_LINK: [MessageHandler(Filters.text & ~Filters.command, request_amazon_link)],
            PRODUCT_ORDER: [MessageHandler(Filters.text & ~Filters.command, order_product)],
            REVIEW_UPLOAD: [MessageHandler(Filters.photo, upload_review)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
    )

    # Hinzufügen des ConversationHandlers
    dispatcher.add_handler(conversation_handler)

    # Startet den Bot
    updater.start_polling()

    # Blockiert, bis der Bot gestoppt wird
    updater.idle()

if __name__ == '__main__':
    main()
