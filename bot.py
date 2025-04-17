import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
import sqlite3
import os

API_TOKEN = '8137004758:AAHaBW6aZwoMTn60rR9gK_FXqJ_69bEydMQ'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# === Datenbank einrichten ===
if not os.path.exists("users.db"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE users (telegram_id INTEGER PRIMARY KEY, paypal_email TEXT, amazon_link TEXT)''')
    c.execute('''CREATE TABLE reviews (telegram_id INTEGER, product_id TEXT, screenshot TEXT, photo TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# === FSM States ===
class Form(StatesGroup):
    paypal = State()
    amazon = State()
    choose_product = State()
    wait_review = State()

# === Produkte (statisch für Demo) ===
PRODUCTS = {
    "101": "USB-C Kabel",
    "102": "Bluetooth Kopfhörer",
    "103": "Fitness Tracker"
}

# === /start ===
@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.reply("Willkommen bei Testazon! Bitte sende mir deine PayPal-Email-Adresse.")
    await Form.paypal.set()

# === PayPal Adresse speichern ===
@dp.message_handler(state=Form.paypal)
async def process_paypal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['paypal'] = message.text
    await message.reply("Danke! Jetzt bitte deinen Amazon-Profil-Link senden.")
    await Form.amazon.set()

# === Amazon-Link speichern und User eintragen ===
@dp.message_handler(state=Form.amazon)
async def process_amazon(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    async with state.proxy() as data:
        paypal = data['paypal']
        amazon = message.text
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("REPLACE INTO users (telegram_id, paypal_email, amazon_link) VALUES (?, ?, ?)",
              (telegram_id, paypal, amazon))
    conn.commit()
    conn.close()
    await message.reply("Top! Hier sind die verfügbaren Produkte:")
    product_list = "\n".join([f"ID {pid}: {name}" for pid, name in PRODUCTS.items()])
    await message.reply(product_list + "\n\nBitte gib die Produkt-ID ein, die du testen möchtest.")
    await Form.choose_product.set()

# === Produkt auswählen ===
@dp.message_handler(state=Form.choose_product)
async def process_product(message: types.Message, state: FSMContext):
    product_id = message.text.strip()
    if product_id not in PRODUCTS:
        await message.reply("Ungültige Produkt-ID. Bitte nochmal versuchen.")
        return
    async with state.proxy() as data:
        data['product_id'] = product_id
    await message.reply(f"Bitte kaufe nun das Produkt '{PRODUCTS[product_id]}' bei Amazon.\nWenn es ankommt, sende den Screenshot der Rezension und ein Foto des Produkts.")
    await Form.wait_review.set()

# === Screenshot und Foto empfangen ===
@dp.message_handler(content_types=['photo', 'document'], state=Form.wait_review)
async def process_review(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    async with state.proxy() as data:
        product_id = data['product_id']
    photo_id = None
    file_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    if message.document:
        file_id = message.document.file_id
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO reviews (telegram_id, product_id, screenshot, photo, status) VALUES (?, ?, ?, ?, 'pending')",
              (telegram_id, product_id, file_id, photo_id))
    conn.commit()
    conn.close()
    await message.reply("Danke! Wir prüfen deine Unterlagen und melden uns. Die Rückerstattung erfolgt nach Bestätigung über PayPal.")
    await state.finish()

# === Admin: Liste aller offenen Aufträge ===
@dp.message_handler(commands='auftraege')
async def admin_list(message: types.Message):
    if message.from_user.id != DEIN_TELEGRAM_ADMIN_ID:
        return
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT r.telegram_id, r.product_id, r.screenshot, r.photo, r.status FROM reviews r WHERE r.status='pending'")
    rows = c.fetchall()
    if not rows:
        await message.reply("Keine offenen Aufträge.")
        return
    for row in rows:
        uid, pid, screenshot, photo, status = row
        text = f"User: {uid}\nProdukt: {PRODUCTS.get(pid, pid)}\nStatus: {status}"
        await message.reply(text)
        if screenshot:
            await bot.send_document(message.chat.id, screenshot)
        if photo:
            await bot.send_photo(message.chat.id, photo)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
