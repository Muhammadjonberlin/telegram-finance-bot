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


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"


# =========================================================
# CATEGORY DETECTION
# =========================================================

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
        "mashina"
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
        "stomatolog"
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
        "uy uchun"
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


    return "📦 Boshqa"


# =========================================================
# DATA
# =========================================================

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


# =========================================================
# MENU
# =========================================================

def menu():

    return ReplyKeyboardMarkup(
        [
            ["💰 Kirim", "💸 Xarajat"],
            ["📊 Hisobot", "📜 Tarix"],
            ["🗑 O'chirish"]
        ],
        resize_keyboard=True
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "💵 Finance Bot\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=menu()
    )


# =========================================================
# INCOME
# =========================================================

async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "income"

    await update.message.reply_text(
        "💰 Kirimni kiriting.\n\n"
        "Masalan:\n"
        "5000000 Maosh"
    )


# =========================================================
# EXPENSE
# =========================================================

async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "expense"

    await update.message.reply_text(
        "💸 Xarajatlarni kiriting.\n\n"
        "Bittadan yozishingiz mumkin:\n"
        "50000 ovqat\n\n"
        "Yoki bir xabarda bir nechta:\n"
        "50000 ovqat\n"
        "120000 benzin\n"
        "30000 avtobus\n\n"
        "🔄 Xarajat rejimidan chiqish uchun menyudagi boshqa tugmani bosing."
    )


# =========================================================
# SAVE MULTIPLE TRANSACTIONS
# =========================================================

async def save_transactions(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    mode = context.user_data.get("mode")

    if mode not in ["income", "expense"]:
        return


    # -----------------------------------------------------
    # Bir xabarda bir nechta qatorni ajratamiz
    # -----------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


    data = load_data()

    saved = []
    errors = []


    # -----------------------------------------------------
    # Har bir xarajatni alohida saqlash
    # -----------------------------------------------------

    for line in lines:

        parts = line.split(maxsplit=1)


        if len(parts) < 2:

            errors.append(line)

            continue


        amount_text = (
            parts[0]
            .replace(",", "")
            .replace(".", "")
            .replace(" ", "")
        )


        try:

            amount = float(amount_text)

        except ValueError:

            errors.append(line)

            continue


        if amount <= 0:

            errors.append(line)

            continue


        description = parts[1]


        # Kategoriya
        if mode == "expense":

            category = detect_category(description)

        else:

            category = "💰 Kirim"


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

        saved.append(transaction)


    # -----------------------------------------------------
    # Saqlash
    # -----------------------------------------------------

    if saved:

        save_data(data)


    # -----------------------------------------------------
    # Javob
    # -----------------------------------------------------

    if not saved and errors:

        await update.message.reply_text(
            "❗ Xarajatni quyidagi formatda yozing:\n\n"
            "50000 ovqat\n"
            "120000 benzin"
        )

        return


    response = ""


    if saved:

        response += "✅ SAQLANDI:\n\n"


        for item in saved:

            if item["type"] == "expense":

                response += (
                    f"{item['category']}\n"
                    f"💸 {item['amount']:,.0f} so'm\n"
                    f"📝 {item['description']}\n\n"
                )

            else:

                response += (
                    "💰 Kirim\n"
                    f"{item['amount']:,.0f} so'm\n"
                    f"📝 {item['description']}\n\n"
                )


    if errors:

        response += (
            "⚠️ Saqlanmagan yozuvlar:\n\n"
        )

        for error in errors:

            response += f"❌ {error}\n"


    # Muhim:
    # mode o'chirilmaydi!
    # Shuning uchun keyingi xarajatni yana yozish mumkin.

    await update.message.reply_text(
        response
    )


# =========================================================
# MONTHLY REPORT
# =========================================================

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


        top = sorted_categories[0]

        text += (
            "\n🏆 Eng ko'p xarajat:\n"
            f"{top[0]}\n"
            f"{top[1]:,.0f} so'm"
        )

    else:

        text += "Xarajat yo'q."


    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================================================
# HISTORY
# =========================================================

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

            emoji = "💰"
            sign = "+"

        else:

            emoji = x["category"]
            sign = "-"


        text += (
            f"{emoji}\n"
            f"{sign}{x['amount']:,.0f} so'm\n"
            f"📝 {x['description']}\n"
            f"🕐 {x['date']}\n\n"
        )


    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================================================
# DELETE LAST
# =========================================================

async def delete_last(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = load_data()

    user_data = [
        x for x in data
        if x["user_id"] == update.effective_user.id
    ]


    if not user_data:

        await update.message.reply_text(
            "🗑 O'chirish uchun yozuv yo'q.",
            reply_markup=menu()
        )

        return


    last = user_data[-1]


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
        "🗑 Oxirgi yozuvni o'chiraymi?\n\n"
        f"💸 {last['amount']:,.0f} so'm\n"
        f"📝 {last['description']}\n"
        f"📂 {last['category']}",
        reply_markup=keyboard
    )


# =========================================================
# CALLBACK
# =========================================================

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
            i
            for i, item in enumerate(data)
            if item["user_id"] == user_id
        ]


        if not indexes:

            await query.edit_message_text(
                "❗ Yozuv topilmadi."
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


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text


    # Menyu tugmalari
    if text == "💰 Kirim":

        await income(update, context)
        return


    if text == "💸 Xarajat":

        await expense(update, context)
        return


    if text == "📊 Hisobot":

        # Rejimni yopamiz
        context.user_data.clear()

        await report(update, context)
        return


    if text == "📜 Tarix":

        context.user_data.clear()

        await history(update, context)
        return


    if text == "🗑 O'chirish":

        context.user_data.clear()

        await delete_last(update, context)
        return


    # Kirim yoki xarajat
    if context.user_data.get("mode") in [
        "income",
        "expense"
    ]:

        await save_transactions(
            update,
            context
        )

        return


    await update.message.reply_text(
        "❗ Avval menyudan bo'lim tanlang.",
        reply_markup=menu()
    )


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

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


# =========================================================
# START
# =========================================================

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
