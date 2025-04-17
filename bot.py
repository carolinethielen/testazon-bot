import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# API Token von Heroku Config Vars
API_TOKEN = os.getenv("8137004758:AAHaBW6aZwoMTn60rR9gK_FXqJ_69bEydMQ")

# Admin ID, ebenfalls aus den Heroku Config Vars
ADMIN_ID = os.getenv("6014547283")

# Funktion für den Start-Befehl
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hallo! Ich bin der Testazon-Bot. Was möchtest du tun?\n'
                              'Wähle ein Produkt, gib deine PayPal E-Mail und Amazon-Link ein.')

# Funktion für das Registrieren der PayPal E-Mail
def set_paypal(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    if user_text.startswith('/paypal '):
        paypal_email = user_text.split(' ', 1)[1]
        # Speichern der PayPal E-Mail in einer Datei oder Datenbank (hier als Beispiel)
        update.message.reply_text(f"Deine PayPal-E-Mail wurde gespeichert: {paypal_email}")
    else:
        update.message.reply_text("Bitte sende deine PayPal-E-Mail mit dem Befehl: /paypal <deine_email@example.com>")

# Funktion für das Registrieren des Amazon-Links
def set_amazon_link(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    if user_text.startswith('/amazon '):
        amazon_link = user_text.split(' ', 1)[1]
        # Speichern des Amazon Links in einer Datei oder Datenbank (hier als Beispiel)
        update.message.reply_text(f"Dein Amazon-Link wurde gespeichert: {amazon_link}")
    else:
        update.message.reply_text("Bitte sende deinen Amazon-Link mit dem Befehl: /amazon <dein_amazon_link>")

# Funktion zur Anzeige von verfügbaren Produkten
def show_products(update: Update, context: CallbackContext) -> None:
    # Dies ist ein Beispiel für die Produktliste. Du kannst die Liste dynamisch anpassen.
    products = [
        {"id": "1", "name": "Produkt 1", "price": "10€"},
        {"id": "2", "name": "Produkt 2", "price": "20€"},
        {"id": "3", "name": "Produkt 3", "price": "30€"},
    ]

    message = "Verfügbare Produkte:\n"
    for product in products:
        message += f"{product['id']}. {product['name']} - {product['price']}\n"

    update.message.reply_text(message)

# Funktion für die Bestellung von Produkten
def order_product(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text
    
    if user_text.startswith('/order '):
        product_id = user_text.split(' ', 1)[1]
        # Hier logische Verbindung zum Bestellsystem oder zur API herstellen
        update.message.reply_text(f"Produkt {product_id} wurde erfolgreich bestellt.")
    else:
        update.message.reply_text("Bitte sende den Befehl /order <Produkt_ID>, um ein Produkt zu bestellen.")

# Funktion zum Hinzufügen von Feedback und Bildern nach der Bestellung
def feedback(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text
    
    if user_text.startswith('/feedback '):
        feedback_message = user_text.split(' ', 1)[1]
        # Hier Feedback speichern oder weiterverarbeiten
        update.message.reply_text(f"Dein Feedback wurde erhalten: {feedback_message}")
    else:
        update.message.reply_text("Bitte sende dein Feedback mit dem Befehl: /feedback <dein_feedback>")

# Hauptfunktion zum Starten des Bots
def main() -> None:
    # Telegram Updater initialisieren
    updater = Updater(API_TOKEN)

    # Dispatcher für die Handhabung der Commands
    dispatcher = updater.dispatcher

    # Handler für /start
    dispatcher.add_handler(CommandHandler("start", start))
    # Handler für /paypal
    dispatcher.add_handler(CommandHandler("paypal", set_paypal))
    # Handler für /amazon
    dispatcher.add_handler(CommandHandler("amazon", set_amazon_link))
    # Handler für /products
    dispatcher.add_handler(CommandHandler("products", show_products))
    # Handler für /order
    dispatcher.add_handler(CommandHandler("order", order_product))
    # Handler für /feedback
    dispatcher.add_handler(CommandHandler("feedback", feedback))

    # Starten des Bots
    updater.start_polling()

    # Lässt den Bot weiterlaufen
    updater.idle()

if __name__ == '__main__':
    main()
