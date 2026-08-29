import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from collections import defaultdict

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "data.json"


# =========================
# CATEGORY DETECTION
# =========================

def detect_category(description):
    text = description.lower().strip()

    # 🚗 TRANSPORT
    transport_keywords = [
        "gas",
        "benzin",
        "benzine",
        "dizel",
        "metan",
        "propan",
        "yoqilg'i",
        "yoqilgi",
        "zapravka",
        "taksi",
        "taxi",
        "uber",
        "yandex",
        "metro",
        "avtobus",
        "bus",
        "parking",
        "parkovka",
        "transport",
        "shina",
        "avto",
        "avtomobil",
        "mashina",
        "moy"
    ]

    if any(word in text for word in transport_keywords):
        return "🚗 Transport"


    # 🍔 OZIQ-OVQAT
    food_keywords = [
        "non",
        "go'sht",
        "gosht",
        "et",
        "meat",
        "tovuq",
        "baliq",
        "sut",
        "qatiq",
        "pishloq",
        "tuxum",
        "guruch",
        "makaron",
        "un",
        "shakar",
        "yog'",
        "yog",
        "meva",
        "olma",
        "banan",
        "uzum",
        "sabzavot",
        "kartoshka",
        "piyoz",
        "pomidor",
        "bodring",
        "kolbasa",
        "shirinlik",
        "suv",
        "market",
        "supermarket",
        "magazin",
        "bozor",
        "ovqat",
        "tushlik",
        "nonushta",
        "kechki ovqat",
        "osh",
        "manti",
        "lag'mon",
        "lagmon",
        "somsa",
        "shaurma",
        "donar",
        "kabob",
        "kebab",
        "mastava",
        "sho'rva",
        "shorva",
        "chuchvara",
        "dimlama"
    ]

    if any(word in text for word in food_keywords):
        return "🍔 Oziq-ovqat"


    # ☕ KAFE
    cafe_keywords = [
        "kafe",
        "cafe",
        "restoran",
        "restaurant",
        "coffee",
        "kofe",
        "qahva",
        "choyxona",
        "oshxona",
        "pizza",
        "burger",
        "lavash",
        "shashlik",
        "fast food",
        "fastfood"
    ]

    if any(word in text for word in cafe_keywords):
        return "☕ Kafe"


    # 💊 SOG'LIQ
    health_keywords = [
        "dori",
        "apteka",
        "dorixona",
        "shifokor",
        "doktor",
        "kasalxona",
        "klinika",
        "analiz",
        "tibbiyot",
        "vitamin",
        "stomatolog",
        "tish doktori"
    ]

    if any(word in text for word in health_keywords):
        return "💊 Sog'liq"


    # 📚 TA'LIM
    education_keywords = [
        "kitob",
        "kurs",
        "o'qish",
        "oqish",
        "universitet",
        "institut",
        "maktab",
        "kollej",
        "dars",
        "repetitor",
        "ingliz tili",
        "imtihon",
        "kontrakt",
        "ta'lim"
    ]

    if any(word in text for word in education_keywords):
        return "📚 Ta'lim"


    # 💳 KREDIT
    credit_keywords = [
        "kredit",
        "qarz",
        "rassrochka",
        "nasiya",
        "muddatli to'lov",
        "muddatli tolov"
    ]

    if any(word in text for word in credit_keywords):
        return "💳 Kredit"


    # 📱 ALOQA
    communication_keywords = [
        "telefon",
        "sim karta",
        "simkarta",
        "tarif",
        "mobil",
        "internet",
        "wifi",
        "wi-fi",
        "ucell",
        "beeline",
        "uzmobile",
        "mobiuz",
        "humans"
    ]

    if any(word in text for word in communication_keywords):
        return "📱 Aloqa"


    # 🏠 UY-JOY
    home_keywords = [
        "ijara",
        "kvartira",
        "svet",
        "elektr",
        "elektr toki",
        "kommunal",
        "kommunalka",
        "remont",
        "mebel",
        "uy uchun",
        "gaz uchun"
    ]

    if any(word in text for word in home_keywords):
        return "🏠 Uy-joy"


    # 🛍 XARIDLAR
    shopping_keywords = [
        "kiyim",
        "futbolka",
        "shim",
        "ko'ylak",
        "koylak",
        "krossovka",
        "oyoq kiyim",
        "poyabzal",
        "sumka",
        "iphone",
        "telefon sotib",
        "noutbuk",
        "kompyuter",
        "quloqchin",
        "airpods",
        "texnika",
        "sovg'a",
        "sovga",
        "shopping"
    ]

    if any(word in text for word in shopping_keywords):
        return "🛍 Xaridlar"


    # 📦 BOSHQA
    return "📦 Boshqa"


# =========================
# DATA FUNCTIONS
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
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# MENU
# =========================

def menu():
    return ReplyKeyboardMarkup(
        [
            ["💰 Kirim", "💸 Xarajat"],
            ["📊 Hisobot", "📜 Tarix"],
            ["🗑 O'chirish"]
        ],
        resize_keyboard=True
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "💵 Finance Bot\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=menu()
    )


# =========================
# INCOME
# =========================

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "income"

    await update.message.reply_text(
        "💰 Kirimni kiriting.\n\n"
        "Misol:\n"
        "5000000 Maosh\n\n"
        "Yoki boshqa kirim:\n"
        "1000000 Bonus"
    )


# =========================
# EXPENSE
# =========================

async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "expense"

    await update.message.reply_text(
        "💸 Xarajatni kiriting.\n\n"
        "Kategoriya tanlash shart emas — bot o'zi aniqlaydi.\n\n"
        "Masalan:\n"
        "50000 ovqat\n"
        "120000 benzin\n"
        "30000 avtobus\n"
        "200000 kontrakt\n"
        "150000 kommunal\n\n"
        "🔄 Ketma-ket bir nechta xarajat yozishingiz mumkin."
    )


# =========================
# SAVE TRANSACTION
# =========================

async def save_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    mode = context.user_data.get("mode")

    if mode not in ["income", "expense"]:
        return

    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        await update.message.reply_text(
            "❗ Iltimos, summa va izohni birga yozing.\n\n"
            "Misol:\n"
            "50000 ovqat"
        )
        return

    try:
        amount_text = (
            parts[0]
            .replace(",", "")
            .replace(".", "")
            .replace(" ", "")
        )

        amount = float(amount_text)

    except ValueError:

        await update.message.reply_text(
            "❗ Summa noto'g'ri.\n\n"
            "Misol:\n"
            "50000 ovqat"
        )
        return

    description = parts[1]

    if amount <= 0:
        await update.message.reply_text(
            "❗ Summa 0 dan katta bo'lishi kerak."
        )
        return


    # Kategoriya
    if mode == "expense":
        category = detect_category(description)
    else:
        category = "💰 Kirim"


    # Data
    data = load_data()

    transaction = {
        "user_id": update.effective_user.id,
        "type": mode,
        "amount": amount,
        "description": description,
        "category": category,
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    data.append(transaction)

    save_data(data)


    # Response
    if mode == "income":

        text_response = (
            "✅ Kirim saqlandi!\n\n"
            f"💰 {amount:,.0f} so'm\n"
            f"📝 {description}"
        )

    else:

        text_response = (
            "✅ Xarajat saqlandi!\n\n"
            f"{category}\n"
            f"💸 {amount:,.0f} so'm\n"
            f"📝 {description}\n\n"
            "Yana xarajat yozishingiz mumkin."
        )


    await update.message.reply_text(
        text_response,
        reply_markup=menu()
    )


# =========================
# MONTHLY REPORT
# =========================

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    user_id = update.effective_user.id

    month = datetime.now().strftime("%Y-%m")


    rows = [
        x for x in data
        if x["user_id"] == user_id
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

            categories[
                x["category"]
            ] += x["amount"]


    text = (
        "📊 OYLIK HISOBOT\n"
        f"📅 {month}\n\n"
        f"💰 Kirim: {income_total:,.0f} so'm\n"
        f"💸 Xarajat: {expense_total:,.0f} so'm\n"
        f"💵 Qoldiq: {balance:,.0f} so'm\n\n"
        "📋 KATEGORIYALAR\n"
    )


    if categories:

        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )


        for category, amount in sorted_categories:

            text += (
                f"{category}: "
                f"{amount:,.0f} so'm\n"
            )


        top_category = sorted_categories[0]

        text += (
            "\n🏆 Eng ko'p xarajat:\n"
            f"{top_category[0]}\n"
            f"{top_category[1]:,.0f} so'm"
        )

    else:

        text += "Xarajat yo'q."


    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================
# HISTORY
# =========================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = [
        x for x in load_data()
        if x["user_id"] == update.effective_user.id
    ]


    last_transactions = data[-10:]


    if not last_transactions:

        await update.message.reply_text(
            "📜 Tarix bo'sh.",
            reply_markup=menu()
        )

        return


    text = "📜 OXIRGI 10 TA\n\n"


    for x in reversed(last_transactions):

        if x["type"] == "income":

            sign = "+"
            emoji = "💰"
            category = "Kirim"

        else:

            sign = "-"
            emoji = x["category"]
            category = x["category"]


        text += (
            f"{emoji}\n"
            f"{sign}{x['amount']:,.0f} so'm\n"
            f"📝 {x['description']}\n"
            f"📂 {category}\n"
            f"🕐 {x['date']}\n\n"
        )


    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================
# DELETE LAST
# =========================

async def delete_last(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = [
        x for x in load_data()
        if x["user_id"] == update.effective_user.id
    ]


    if not data:

        await update.message.reply_text(
            "🗑 O'chirish uchun yozuv yo'q.",
            reply_markup=menu()
        )

        return


    last = data[-1]


    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ha",
                    callback_data="delete_yes"
                ),
                InlineKeyboardButton(
                    "❌ Yo'q",
                    callback_data="delete_no"
                )
            ]
        ]
    )


    await update.message.reply_text(
        "🗑 Oxirgi xarajatni o'chiraymi?\n\n"
        f"💸 {last['amount']:,.0f} so'm\n"
        f"📝 {last['description']}\n"
        f"📂 {last['category']}",
        reply_markup=keyboard
    )


# =========================
# CALLBACK
# =========================

async def callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    if query.data == "delete_no":

        await query.edit_message_text(
            "❌ O'chirish bekor qilindi."
        )

        return


    if query.data == "delete_yes":

        data = load_data()

        user_id = query.from_user.id


        indexes = [
            i for i, item in enumerate(data)
            if item["user_id"] == user_id
        ]


        if not indexes:

            await query.edit_message_text(
                "❗ O'chirish uchun yozuv topilmadi."
            )

            return


        index = indexes[-1]

        deleted = data.pop(index)

        save_data(data)


        await query.edit_message_text(
            "✅ O'chirildi!\n\n"
            f"💸 {deleted['amount']:,.0f} so'm\n"
            f"📝 {deleted['description']}"
        )


# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text


    if text == "💰 Kirim":

        await income(update, context)

        return


    if text == "💸 Xarajat":

        await expense(update, context)

        return


    if text == "📊 Hisobot":

        await report(update, context)

        return


    if text == "📜 Tarix":

        await history(update, context)

        return


    if text == "🗑 O'chirish":

        await delete_last(update, context)

        return


    if context.user_data.get("mode") in [
        "income",
        "expense"
    ]:

        await save_transaction(
            update,
            context
        )

        return


    await update.message.reply_text(
        "❗ Avval menyudan bo'lim tanlang.",
        reply_markup=menu()
    )


# =========================
# KEEP RENDER WEB SERVICE ALIVE
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"Finance Bot is running!"
        )

    def log_message(self, format, *args):
        return


def run_health_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


# =========================
# START BOT
# =========================

if not TOKEN:

    raise ValueError(
        "BOT_TOKEN environment variable topilmadi!"
    )


threading.Thread(
    target=run_health_server,
    daemon=True
).start()


app = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)


app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


app.add_handler(
    CallbackQueryHandler(
        callback
    )
)


app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    )
)


print("BOT ISHGA TUSHDI")


app.run_polling(
    drop_pending_updates=True
)
