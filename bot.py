from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler,
                          MessageHandler, Filters, ConversationHandler, CallbackContext)
import re

# States
(PAYPAL_EMAIL, AMAZON_LINK, TESTING_COUNT, PRODUCT_ORDER, ACTIVE_ORDERS, HELP, RULES) = range(7)

def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Produkt auswählen", callback_data="order_product")],
        [InlineKeyboardButton("Aktive Bestellungen", callback_data="active_orders")],
        [InlineKeyboardButton("Regeln & Infos", callback_data="rules")],
        [InlineKeyboardButton("Hilfe & Support", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Willkommen zum Produkttester Bot! Bitte wähle eine Option:", reply_markup=reply_markup
    )
    return ConversationHandler.END

def show_rules(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Regeln:\n1. Nur ein Test pro Produkt\n2. Ehrliche Rezensionen\n3. Rückerstattung nach Bewertung")
    return ConversationHandler.END

def help_support(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Bei Fragen kontaktiere den Support unter @SupportHandle")
    return ConversationHandler.END

def order_product(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Bitte gib deine PayPal-Adresse ein:")
    return PAYPAL_EMAIL

def verify_paypal_email(update: Update, context: CallbackContext) -> int:
    email = update.message.text
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        context.user_data['paypal_email'] = email
        update.message.reply_text("Super! Bitte sende jetzt deinen Amazon-Profillink:")
        return AMAZON_LINK
    else:
        update.message.reply_text("Das sieht nicht wie eine gültige E-Mail aus. Bitte nochmal eingeben:")
        return PAYPAL_EMAIL

def request_amazon_link(update: Update, context: CallbackContext) -> int:
    link = update.message.text
    if "amazon" in link:
        context.user_data['amazon_link'] = link
        update.message.reply_text("Wie viele Produkte hast du bisher getestet?")
        return TESTING_COUNT
    else:
        update.message.reply_text("Bitte gib einen gültigen Amazon-Link ein:")
        return AMAZON_LINK

def set_testing_count(update: Update, context: CallbackContext) -> int:
    try:
        count = int(update.message.text)
        context.user_data['testing_count'] = count
        update.message.reply_text(f"Vielen Dank! Deine Angaben:\nPayPal: {context.user_data['paypal_email']}\nAmazon: {context.user_data['amazon_link']}\nGetestet: {count}\nWir melden uns bei dir mit einem passenden Produkt.")
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Bitte gib eine gültige Zahl ein:")
        return TESTING_COUNT

def show_active_orders(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Aktive Bestellungen:\n1. Produkt XY - Rückerstattung ausstehend\n2. Produkt Z - Rückerstattung erfolgt")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Abgebrochen. Du kannst mit /start neu beginnen.")
    return ConversationHandler.END

def main() -> None:
    updater = Updater("DEIN_BOT_TOKEN_HIER")
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PAYPAL_EMAIL: [MessageHandler(Filters.text & ~Filters.command, verify_paypal_email)],
            AMAZON_LINK: [MessageHandler(Filters.text & ~Filters.command, request_amazon_link)],
            TESTING_COUNT: [MessageHandler(Filters.text & ~Filters.command, set_testing_count)],
            PRODUCT_ORDER: [CallbackQueryHandler(order_product, pattern="^order_product$")],
            ACTIVE_ORDERS: [CallbackQueryHandler(show_active_orders, pattern="^active_orders$")],
            HELP: [CallbackQueryHandler(help_support, pattern="^help$")],
            RULES: [CallbackQueryHandler(show_rules, pattern="^rules$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
