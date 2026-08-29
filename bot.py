import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from collections import defaultdict

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"
PORT = int(os.getenv("PORT", "10000"))

CATEGORIES = [
    "🍔 Oziq-ovqat",
    "🚗 Transport",
    "🏠 Uy-joy",
    "🛍 Xaridlar",
    "☕ Kafe",
    "💊 Sog'liq",
    "📱 Aloqa",
    "📚 Ta'lim",
    "💳 Kredit",
    "📦 Boshqa",
]

# Xarajatni avtomatik kategoriya qilish uchun kalit so'zlar
CATEGORY_KEYWORDS = {
    "🍔 Oziq-ovqat": [
        "non", "go'sht", "gosht", "mol go'shti", "qo'y", "tovuq",
        "baliq", "sut", "qatiq", "pishloq", "tuxum", "guruch",
        "makaron", "un", "shakar", "yog'", "yog", "meva", "olma",
        "banan", "sabzavot", "kartoshka", "piyoz", "pomidor",
        "bodring", "kolbasa", "shirinlik", "suv", "ichimlik",
        "market", "supermarket", "magazin", "bozor"
    ],

    "🚗 Transport": [
        "benzin", "dizel", "gaz", "metan", "propan", "yoqilg'i",
        "yoqilgi", "taksi", "taxi", "uber", "yandex", "metro",
        "avtobus", "bus", "mashina", "avto", "parking", "parkovka",
        "transport", "moy", "shina", "zapravka"
    ],

    "🏠 Uy-joy": [
        "ijara", "kvartira", "uy", "svet", "elektr", "elektr toki",
        "gaz", "suv", "kommunal", "kommunalka", "internet uy",
        "remont", "mebel", "mebel", "uy uchun"
    ],

    "🛍 Xaridlar": [
        "kiyim", "futbolka", "shim", "ko'ylak", "koylak", "krossovka",
        "oyoq kiyim", "poyabzal", "sumka", "telefon", "iphone",
        "noutbuk", "kompyuter", "quloqchin", "airpods", "texnika",
        "sovg'a", "sovga", "xarid", "shopping"
    ],

    "☕ Kafe": [
        "kafe", "cafe", "restoran", "restaurant", "coffee", "kofe",
        "qahva", "choyxona", "oshxona", "pizza", "burger",
        "lavash", "shashlik", "fast food", "fastfood"
    ],

    "💊 Sog'liq": [
        "dori", "apteka", "dorixona", "shifokor", "doktor",
        "kasalxona", "klinika", "analiz", "tibbiyot", "vitamin",
        "stomatolog", "tish doktori"
    ],

    "📱 Aloqa": [
        "telefon", "sim karta", "simkarta", "tarif", "mobil",
        "internet", "wifi", "wi-fi", "ucell", "beeline",
        "uzmobile", "mobiuz", "humans"
    ],

    "📚 Ta'lim": [
        "kitob", "kurs", "kursga", "o'qish", "oqish", "universitet",
        "institut", "maktab", "kollej", "dars", "repetitor",
        "ingliz tili", "imtihon", "kontrakt", "ta'lim"
    ],

    "💳 Kredit": [
        "kredit", "qarz", "rassrochka", "nasiya", "muddatli to'lov",
        "muddatli tolov", "bank krediti"
    ],
}


# =========================
# WEB SERVER - RENDER UCHUN
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Finance Bot is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================
# DATA
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# MENU
# =========================

def menu():
    return ReplyKeyboardMarkup(
        [
            ["💰 Kirim", "💸 Xarajat"],
            ["📊 Hisobot", "📜 Tarix"],
            ["🗑 O'chirish"],
        ],
        resize_keyboard=True,
    )


# =========================
# AUTO CATEGORY
# =========================

def detect_category(description):
    text = description.lower()

    # Avval aniqroq kategoriyalarni tekshiramiz
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "📦 Boshqa"


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "💵 Finance Bot\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=menu(),
    )


# =========================
# INCOME
# =========================

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "income"

    await update.message.reply_text(
        "💰 Kirimni kiriting.\n\n"
        "Masalan:\n"
        "5000000 Maosh\n"
        "1000000 Bonus"
    )


# =========================
# EXPENSE
# =========================

async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "expense"

    await update.message.reply_text(
        "💸 Xarajatlarni kiriting.\n\n"
        "Bir nechta xarajatni bitta xabarda yozishingiz mumkin.\n\n"
        "Masalan:\n"
        "50000 non\n"
        "120000 benzin\n"
        "35000 kafe\n"
        "200000 dori\n\n"
        "Bot kategoriyani avtomatik aniqlaydi."
    )


# =========================
# SAVE TRANSACTIONS
# =========================

async def save_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if mode not in ["income", "expense"]:
        return

    lines = text.splitlines()

    data = load_data()
    saved = []
    errors = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        parts = line.split(maxsplit=1)

        if len(parts) < 2:
            errors.append(line)
            continue

        amount_text = parts[0]
        description = parts[1].strip()

        try:
            amount = float(
                amount_text
                .replace(",", "")
                .replace(".", "")
                .replace(" ", "")
            )
        except ValueError:
            errors.append(line)
            continue

        if amount <= 0:
            errors.append(line)
            continue

        if mode == "income":
            category = "💰 Kirim"
        else:
            category = detect_category(description)

        transaction = {
            "user_id": update.effective_user.id,
            "type": mode,
            "amount": amount,
            "description": description,
            "category": category,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        data.append(transaction)
        saved.append(transaction)

    save_data(data)

    if not saved:
        await update.message.reply_text(
            "❌ Xarajatni tushunmadim.\n\n"
            "To'g'ri format:\n"
            "50000 non\n"
            "120000 benzin",
            reply_markup=menu(),
        )
        return

    # Natijani chiqarish
    if mode == "expense":
        message = f"✅ {len(saved)} ta xarajat saqlandi!\n\n"

        total = 0

        for x in saved:
            total += x["amount"]

            message += (
                f"{x['category']}\n"
                f"💸 {x['amount']:,.0f} so'm\n"
                f"📝 {x['description']}\n\n"
            )

        message += f"💵 Jami: {total:,.0f} so'm"

    else:
        message = f"✅ {len(saved)} ta kirim saqlandi!\n\n"

        total = 0

        for x in saved:
            total += x["amount"]

            message += (
                f"💰 {x['amount']:,.0f} so'm\n"
                f"📝 {x['description']}\n\n"
            )

        message += f"💵 Jami: {total:,.0f} so'm"

    if errors:
        message += (
            "\n\n⚠️ Quyidagilar saqlanmadi:\n"
            + "\n".join(errors)
        )

    context.user_data.clear()

    await update.message.reply_text(
        message,
        reply_markup=menu(),
    )


# =========================
# REPORT
# =========================

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    uid = update.effective_user.id
    month = datetime.now().strftime("%Y-%m")

    rows = [
        x for x in data
        if x["user_id"] == uid
        and x["date"].startswith(month)
    ]

    income_total = sum(
        x["amount"]
        for x in rows
        if x["type"] == "income"
    )

    expense_total = sum(
        x["amount"]
        for x in rows
        if x["type"] == "expense"
    )

    balance = income_total - expense_total

    categories = defaultdict(float)

    for x in rows:
        if x["type"] == "expense":
            categories[x["category"]] += x["amount"]

    text = (
        "📊 OYLIK HISOBOT\n"
        f"📅 {month}\n\n"
        f"💰 Kirim: {income_total:,.0f} so'm\n"
        f"💸 Xarajat: {expense_total:,.0f} so'm\n"
        f"💵 Qoldiq: {balance:,.0f} so'm\n\n"
        "📋 KATEGORIYALAR\n"
    )

    if categories:
        for category, amount in sorted(
            categories.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            text += f"{category}: {amount:,.0f} so'm\n"

        top_category = max(
            categories,
            key=categories.get
        )

        text += (
            f"\n🏆 Eng ko'p xarajat:\n"
            f"{top_category} — "
            f"{categories[top_category]:,.0f} so'm"
        )

    else:
        text += "Xarajat yo'q."

    await update.message.reply_text(
        text,
        reply_markup=menu(),
    )


# =========================
# HISTORY
# =========================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = [
        x for x in load_data()
        if x["user_id"] == update.effective_user.id
    ]

    data = data[-10:]

    if not data:
        await update.message.reply_text(
            "📜 Tarix bo'sh.",
            reply_markup=menu(),
        )
        return

    text = "📜 OXIRGI 10 TA\n\n"

    for x in reversed(data):
        if x["type"] == "income":
            symbol = "💰"
            sign = "+"
        else:
            symbol = x["category"]
            sign = "-"

        text += (
            f"{symbol}\n"
            f"{sign}{x['amount']:,.0f} so'm\n"
            f"📝 {x['description']}\n"
            f"📅 {x['date']}\n\n"
        )

    await update.message.reply_text(
        text,
        reply_markup=menu(),
    )


# =========================
# DELETE LAST
# =========================

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = [
        x for x in load_data()
        if x["user_id"] == update.effective_user.id
    ]

    if not data:
        await update.message.reply_text(
            "🗑 O'chirish uchun yozuv yo'q.",
            reply_markup=menu(),
        )
        return

    x = data[-1]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ha",
                    callback_data="yes",
                ),
                InlineKeyboardButton(
                    "❌ Yo'q",
                    callback_data="no",
                ),
            ]
        ]
    )

    await update.message.reply_text(
        "🗑 Oxirgi yozuvni o'chiraymi?\n\n"
        f"{x['amount']:,.0f} so'm\n"
        f"{x['description']}\n"
        f"{x['category']}",
        reply_markup=keyboard,
    )


# =========================
# CALLBACK
# =========================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    if query.data == "no":
        await query.edit_message_text("❌ Bekor qilindi.")
        return

    data = load_data()
    uid = query.from_user.id

    indexes = [
        i for i, x in enumerate(data)
        if x["user_id"] == uid
    ]

    if not indexes:
        await query.edit_message_text(
            "❌ O'chirish uchun yozuv topilmadi."
        )
        return

    index = indexes[-1]

    deleted = data.pop(index)

    save_data(data)

    await query.edit_message_text(
        "✅ O'chirildi.\n\n"
        f"{deleted['amount']:,.0f} so'm\n"
        f"{deleted['description']}"
    )


# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💰 Kirim":
        return await income(update, context)

    if text == "💸 Xarajat":
        return await expense(update, context)

    if text == "📊 Hisobot":
        return await report(update, context)

    if text == "📜 Tarix":
        return await history(update, context)

    if text == "🗑 O'chirish":
        return await delete_last(update, context)

    if context.user_data.get("mode") in ["income", "expense"]:
        return await save_transactions(update, context)

    await update.message.reply_text(
        "👇 Kerakli bo'limni tanlang.",
        reply_markup=menu(),
    )


# =========================
# MAIN
# =========================

def main():
    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable topilmadi!"
        )

    # Render Web Service port talab qiladi
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(callback)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    print("BOT ISHGA TUSHDI")

    application.run_polling()


if __name__ == "__main__":
    main()
