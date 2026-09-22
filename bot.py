import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
from datetime import datetime

import psycopg2
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


# =========================================================
# HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    print(f"HTTP SERVER ISHGA TUSHDI: {port}")

    server.serve_forever()


# =========================================================
# DATABASE
# =========================================================

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # =====================================================
    # ESKI BOSHQA KATEGORIYASIDAGI BOZOR XARAJATLARINI
    # 🛒 BOZORGA KO'CHIRISH
    # =====================================================

    cur.execute("""
        UPDATE transactions
        SET category = '🛒 Bozor'
        WHERE type = 'expense'
          AND category = '📦 Boshqa'
          AND (
              LOWER(description) LIKE '%bozor%'
              OR LOWER(description) LIKE '%do''kon%'
              OR LOWER(description) LIKE '%dokon%'
              OR LOWER(description) LIKE '%do‘kon%'
              OR LOWER(description) LIKE '%do’kon%'

              OR LOWER(description) LIKE '%go''sht%'
              OR LOWER(description) LIKE '%gosht%'
              OR LOWER(description) LIKE '%mol go''shti%'
              OR LOWER(description) LIKE '%mol goshti%'
              OR LOWER(description) LIKE '%qo''y go''shti%'
              OR LOWER(description) LIKE '%qoy goshti%'

              OR LOWER(description) LIKE '%tovuq%'
              OR LOWER(description) LIKE '%baliq%'
              OR LOWER(description) LIKE '%suv%'
              OR LOWER(description) LIKE '%non%'
              OR LOWER(description) LIKE '%sut%'
              OR LOWER(description) LIKE '%qatiq%'
              OR LOWER(description) LIKE '%pishloq%'
              OR LOWER(description) LIKE '%tvorog%'
              OR LOWER(description) LIKE '%qaymoq%'
              OR LOWER(description) LIKE '%smetana%'
              OR LOWER(description) LIKE '%tuxum%'

              OR LOWER(description) LIKE '%guruch%'
              OR LOWER(description) LIKE '%makaron%'
              OR LOWER(description) LIKE '%un%'
              OR LOWER(description) LIKE '%shakar%'
              OR LOWER(description) LIKE '%tuz%'
              OR LOWER(description) LIKE '%moy%'
              OR LOWER(description) LIKE '%yog''%'
              OR LOWER(description) LIKE '%yog‘%'

              OR LOWER(description) LIKE '%kartoshka%'
              OR LOWER(description) LIKE '%piyoz%'
              OR LOWER(description) LIKE '%sabzi%'
              OR LOWER(description) LIKE '%pomidor%'
              OR LOWER(description) LIKE '%bodring%'
              OR LOWER(description) LIKE '%karam%'
              OR LOWER(description) LIKE '%qalampir%'
              OR LOWER(description) LIKE '%baqlajon%'
              OR LOWER(description) LIKE '%lavlagi%'
              OR LOWER(description) LIKE '%sabzavot%'

              OR LOWER(description) LIKE '%meva%'
              OR LOWER(description) LIKE '%olma%'
              OR LOWER(description) LIKE '%banan%'
              OR LOWER(description) LIKE '%uzum%'
              OR LOWER(description) LIKE '%apelsin%'
              OR LOWER(description) LIKE '%mandarin%'
              OR LOWER(description) LIKE '%limon%'
              OR LOWER(description) LIKE '%shaftoli%'
              OR LOWER(description) LIKE '%o''rik%'
              OR LOWER(description) LIKE '%orik%'
              OR LOWER(description) LIKE '%anor%'
              OR LOWER(description) LIKE '%tarvuz%'
              OR LOWER(description) LIKE '%qovun%'

              OR LOWER(description) LIKE '%shirinlik%'
              OR LOWER(description) LIKE '%shokolad%'
              OR LOWER(description) LIKE '%pechenye%'
              OR LOWER(description) LIKE '%konfet%'
              OR LOWER(description) LIKE '%tort%'
              OR LOWER(description) LIKE '%muzqaymoq%'

              OR LOWER(description) LIKE '%kolbasa%'
              OR LOWER(description) LIKE '%sosiska%'
              OR LOWER(description) LIKE '%konserva%'
              OR LOWER(description) LIKE '%ichimlik%'
              OR LOWER(description) LIKE '%choy%'
          )

          -- "suv to'lovi" bozor emas
          AND LOWER(description) NOT LIKE '%suv to%'
    """)

    conn.commit()

    cur.close()
    conn.close()

    print("✅ ESKI BOZOR XARAJATLARI 🛒 BOZORGA O'TKAZILDI")


# =========================================================
# CATEGORY DETECTION
# =========================================================

def detect_category(text):

    text = text.lower().strip()

    # -----------------------------------------------------
    # UY-JOY
    # -----------------------------------------------------

    home_words = [
        "kommunal",
        "svet",
        "elektr",
        "elektr toki",
        "gaz to'lovi",
        "gaz to‘lovi",
        "gaz tolovi",
        "suv to'lovi",
        "suv to‘lovi",
        "suv tolovi",
        "ijara",
        "kvartira",
        "uy-joy",
        "uy joy",
        "uy uchun",
    ]

    if any(word in text for word in home_words):
        return "🏠 Uy-joy"

    # -----------------------------------------------------
    # OZIq-OVQAT
    # -----------------------------------------------------

    if re.search(r"\bovqat\b", text):
        return "🍽️ Oziq-ovqat"

    if re.search(r"\boziq-ovqat\b", text):
        return "🍽️ Oziq-ovqat"

    # -----------------------------------------------------
    # TRANSPORT
    # -----------------------------------------------------

    transport_words = [
        "benzin",
        "dizel",
        "yoqilg'i",
        "yoqilgi",
        "avtobus",
        "taksi",
        "metro",
        "mashina",
        "transport",
        "parking",
        "parkovka",
        "yo'l",
        "yol",
        "gaz",
    ]

    if any(word in text for word in transport_words):
        return "🚗 Transport"

    # -----------------------------------------------------
    # BOZOR
    # -----------------------------------------------------

    market_words = [
        "bozor",
        "do'kon",
        "dokon",
        "do‘kon",
        "do’kon",

        "go'sht",
        "gosht",
        "mol go'shti",
        "mol goshti",
        "qo'y go'shti",
        "qoy goshti",

        "tovuq",
        "baliq",

        "suv",
        "non",
        "sut",
        "qatiq",
        "pishloq",
        "tvorog",
        "qaymoq",
        "smetana",
        "tuxum",

        "guruch",
        "makaron",
        "un",
        "shakar",
        "tuz",
        "yog'",
        "yog‘",
        "moy",

        "kartoshka",
        "piyoz",
        "sabzi",
        "pomidor",
        "bodring",
        "karam",
        "qalampir",
        "baqlajon",
        "lavlagi",
        "sabzavot",

        "meva",
        "olma",
        "banan",
        "uzum",
        "apelsin",
        "mandarin",
        "limon",
        "shaftoli",
        "o'rik",
        "orik",
        "anor",
        "tarvuz",
        "qovun",

        "shirinlik",
        "shokolad",
        "pechenye",
        "konfet",
        "tort",
        "muzqaymoq",

        "kolbasa",
        "sosiska",
        "konserva",
        "ichimlik",
        "choy",
    ]

    if any(word in text for word in market_words):
        return "🛒 Bozor"

    # -----------------------------------------------------
    # TA'LIM
    # -----------------------------------------------------

    education_words = [
        "kontrakt",
        "universitet",
        "institut",
        "o'qish",
        "oqish",
        "ta'lim",
        "kurs",
        "kursga",
        "kitob",
        "dars",
        "repetitor",
    ]

    if any(word in text for word in education_words):
        return "📚 Ta'lim"

    # -----------------------------------------------------
    # KAFE
    # -----------------------------------------------------

    cafe_words = [
        "kafe",
        "cafe",
        "restoran",
        "restaurant",
        "oshxona",
        "choyxona",
        "coffee",
        "kofe",
    ]

    if any(word in text for word in cafe_words):
        return "☕ Kafe"

    # -----------------------------------------------------
    # SOG'LIQ
    # -----------------------------------------------------

    health_words = [
        "dori",
        "dorixona",
        "shifokor",
        "doktor",
        "kasalxona",
        "analiz",
        "davolanish",
        "apteka",
    ]

    if any(word in text for word in health_words):
        return "💊 Sog'liq"

    # -----------------------------------------------------
    # ALOQA
    # -----------------------------------------------------

    phone_words = [
        "telefon",
        "sim karta",
        "internet paket",
        "tarif",
        "aloqa",
        "mobil",
    ]

    if any(word in text for word in phone_words):
        return "📱 Aloqa"

    # -----------------------------------------------------
    # KREDIT
    # -----------------------------------------------------

    credit_words = [
        "kredit",
        "qarz",
        "bank to'lovi",
        "bank to‘lovi",
        "bank tolovi",
    ]

    if any(word in text for word in credit_words):
        return "💳 Kredit"

    # -----------------------------------------------------
    # XARIDLAR
    # -----------------------------------------------------

    shopping_words = [
        "kiyim",
        "oyoq kiyim",
        "telefon sotib",
        "texnika",
        "xarid",
        "sumka",
        "sovg'a",
        "sovga",
    ]

    if any(word in text for word in shopping_words):
        return "🛍 Xaridlar"

    return "📦 Boshqa"


# =========================================================
# ADD TRANSACTION
# =========================================================

def add_transaction(
    user_id,
    tx_type,
    amount,
    description,
    category
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions
        (user_id, type, amount, description, category)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        tx_type,
        amount,
        description,
        category
    ))

    conn.commit()

    cur.close()
    conn.close()


# =========================================================
# MENU
# =========================================================

def menu():

    return ReplyKeyboardMarkup(
        [
            ["💰 Kirim", "💸 Xarajat"],
            ["📊 Hisobot", "📜 Tarix"],
            ["🗑 O'chirish"],
        ],
        resize_keyboard=True
    )


# =========================================================
# MONTH HELPERS
# =========================================================

MONTH_NAMES = {
    1: "Yanvar",
    2: "Fevral",
    3: "Mart",
    4: "Aprel",
    5: "May",
    6: "Iyun",
    7: "Iyul",
    8: "Avgust",
    9: "Sentabr",
    10: "Oktabr",
    11: "Noyabr",
    12: "Dekabr",
}


def month_label(month_key):

    year, month = month_key.split("-")

    return f"{MONTH_NAMES[int(month)]} {year}"


def get_available_months(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT TO_CHAR(created_at, 'YYYY-MM') AS month_key
        FROM transactions
        WHERE user_id = %s
        ORDER BY month_key DESC
    """, (user_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    months = [row[0] for row in rows]

    current_month = datetime.now().strftime("%Y-%m")

    if current_month not in months:
        months.insert(0, current_month)

    return sorted(set(months), reverse=True)


def month_keyboard(mode, months):

    buttons = []

    for month_key in months:

        buttons.append(
            InlineKeyboardButton(
                month_label(month_key),
                callback_data=f"{mode}:{month_key}"
            )
        )

    rows = []

    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i + 2])

    rows.append([
        InlineKeyboardButton(
            "❌ Yopish",
            callback_data="close_months"
        )
    ])

    return InlineKeyboardMarkup(rows)


def month_action_keyboard(mode, month_key):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📅 Boshqa oy",
                callback_data=f"choose:{mode}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Yopish",
                callback_data="close_months"
            )
        ]
    ])


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
        "💸 Xarajatlarni ketma-ket kiriting.\n\n"
        "Masalan:\n"
        "50000 go'sht\n"
        "30000 benzin\n"
        "20000 ovqat\n\n"
        "Har bir xarajatni yangi qatordan yozing.\n\n"
        "Kategoriya avtomatik aniqlanadi."
    )


# =========================================================
# SAVE TRANSACTIONS
# =========================================================

async def save_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if mode not in ["income", "expense"]:
        return

    lines = text.splitlines()
    saved = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        match = re.match(r"^([\d\s,\.]+)\s+(.+)$", line)

        if not match:
            continue

        amount_text = match.group(1)
        description = match.group(2).strip()

        try:

            amount_text = (
                amount_text
                .replace(",", "")
                .replace(".", "")
                .replace(" ", "")
            )

            amount = float(amount_text)

        except ValueError:
            continue

        if mode == "income":

            category = "💰 Kirim"

            add_transaction(
                update.effective_user.id,
                "income",
                amount,
                description,
                category
            )

            saved.append(
                f"💰 +{amount:,.0f} so'm — {description}"
            )

        else:

            category = detect_category(description)

            add_transaction(
                update.effective_user.id,
                "expense",
                amount,
                description,
                category
            )

            saved.append(
                f"{category}\n"
                f"-{amount:,.0f} so'm — {description}"
            )

    if not saved:

        await update.message.reply_text(
            "❌ Xarajatni tushunmadim.\n\n"
            "Masalan:\n"
            "50000 go'sht\n"
            "30000 benzin\n"
            "20000 ovqat"
        )

        return

    result = "✅ Saqlandi!\n\n"

    for item in saved:
        result += item + "\n\n"

    result += f"📌 Jami: {len(saved)} ta yozuv"

    await update.message.reply_text(
        result,
        reply_markup=menu()
    )

    context.user_data.clear()


# =========================================================
# REPORT - MONTH SELECTOR
# =========================================================

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    months = get_available_months(uid)

    await update.message.reply_text(
        "📊 HISOBOT\n\n"
        "Qaysi oy hisobotini ko'rmoqchisiz?",
        reply_markup=month_keyboard(
            "report",
            months
        )
    )


# =========================================================
# REPORT - ONE MONTH
# =========================================================

async def show_month_report(
    query,
    user_id,
    month_key
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, amount, category
        FROM transactions
        WHERE user_id = %s
          AND TO_CHAR(created_at, 'YYYY-MM') = %s
        ORDER BY created_at ASC
    """, (
        user_id,
        month_key
    ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    income_total = 0
    expense_total = 0

    categories = defaultdict(float)

    for tx_type, amount, category in rows:

        amount = float(amount)

        if tx_type == "income":

            income_total += amount

        else:

            expense_total += amount
            categories[category] += amount

    balance = income_total - expense_total

    text = (
        f"📊 {month_label(month_key).upper()}\n\n"
        f"💰 Kirim: {income_total:,.0f} so'm\n"
        f"💸 Xarajat: {expense_total:,.0f} so'm\n"
        f"💵 Qoldiq: {balance:,.0f} so'm\n\n"
        "📋 KATEGORIYALAR\n"
    )

    if categories:

        for category, amount in sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        ):

            text += (
                f"{category}: "
                f"{amount:,.0f} so'm\n"
            )

    else:

        text += "Bu oyda xarajat yo'q.\n"

    await query.edit_message_text(
        text,
        reply_markup=month_action_keyboard(
            "report",
            month_key
        )
    )


# =========================================================
# HISTORY - MONTH SELECTOR
# =========================================================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    months = get_available_months(uid)

    await update.message.reply_text(
        "📜 TARIX\n\n"
        "Qaysi oy xarajatlarini ko'rmoqchisiz?",
        reply_markup=month_keyboard(
            "history",
            months
        )
    )


# =========================================================
# HISTORY - ONE MONTH
# =========================================================

async def show_month_history(
    query,
    user_id,
    month_key
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT amount, description, category, created_at
        FROM transactions
        WHERE user_id = %s
          AND type = 'expense'
          AND TO_CHAR(created_at, 'YYYY-MM') = %s
        ORDER BY category, created_at DESC
    """, (
        user_id,
        month_key
    ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:

        text = (
            f"📜 {month_label(month_key).upper()}\n\n"
            "Bu oyda xarajat yo'q."
        )

        await query.edit_message_text(
            text,
            reply_markup=month_action_keyboard(
                "history",
                month_key
            )
        )

        return

    grouped = defaultdict(list)

    for amount, description, category, created_at in rows:

        grouped[category].append(
            (
                float(amount),
                description,
                created_at
            )
        )

    text = (
        f"📜 XARAJATLAR — "
        f"{month_label(month_key).upper()}\n\n"
    )

    for category, items in grouped.items():

        category_total = sum(
            amount
            for amount, description, created_at in items
        )

        text += (
            f"{category}\n"
            "━━━━━━━━━━━━━━\n"
        )

        for amount, description, created_at in items:

            text += (
                f"• {amount:,.0f} so'm — {description}\n"
                f"  📅 {created_at.strftime('%Y-%m-%d %H:%M')}\n"
            )

        text += (
            f"Jami: {category_total:,.0f} so'm\n\n"
        )

    total = sum(
        amount
        for items in grouped.values()
        for amount, description, created_at in items
    )

    text += (
        "━━━━━━━━━━━━━━\n"
        f"💸 UMUMIY: {total:,.0f} so'm"
    )

    if len(text) > 3900:

        text = (
            text[:3900]
            + "\n\n"
            "… Tarix juda uzun bo'ldi."
        )

    await query.edit_message_text(
        text,
        reply_markup=month_action_keyboard(
            "history",
            month_key
        )
    )


# =========================================================
# DELETE LAST
# =========================================================

async def delete_last(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, type, amount, description
        FROM transactions
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (uid,))

    row = cur.fetchone()

    if not row:

        cur.close()
        conn.close()

        await update.message.reply_text(
            "🗑 O'chirish uchun yozuv yo'q.",
            reply_markup=menu()
        )

        return

    tx_id, tx_type, amount, description = row

    cur.execute(
        "DELETE FROM transactions WHERE id = %s",
        (tx_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    await update.message.reply_text(
        "✅ Oxirgi yozuv o'chirildi.\n\n"
        f"{float(amount):,.0f} so'm\n"
        f"{description}",
        reply_markup=menu()
    )


# =========================================================
# CALLBACKS
# =========================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    user_id = update.effective_user.id

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    if data == "close_months":

        await query.edit_message_text(
            "✅ Yopildi.\n\n"
            "Kerakli bo'limni menyudan tanlang."
        )

        return

    # -----------------------------------------------------
    # CHOOSE ANOTHER REPORT MONTH
    # -----------------------------------------------------

    if data == "choose:report":

        months = get_available_months(user_id)

        await query.edit_message_text(
            "📊 HISOBOT\n\n"
            "Qaysi oy hisobotini ko'rmoqchisiz?",
            reply_markup=month_keyboard(
                "report",
                months
            )
        )

        return

    # -----------------------------------------------------
    # CHOOSE ANOTHER HISTORY MONTH
    # -----------------------------------------------------

    if data == "choose:history":

        months = get_available_months(user_id)

        await query.edit_message_text(
            "📜 TARIX\n\n"
            "Qaysi oy xarajatlarini ko'rmoqchisiz?",
            reply_markup=month_keyboard(
                "history",
                months
            )
        )

        return

    # -----------------------------------------------------
    # REPORT MONTH
    # -----------------------------------------------------

    if data.startswith("report:"):

        month_key = data.split(":", 1)[1]

        if not re.fullmatch(
            r"\d{4}-\d{2}",
            month_key
        ):

            await query.edit_message_text(
                "❌ Oy formati noto'g'ri."
            )

            return

        await show_month_report(
            query,
            user_id,
            month_key
        )

        return

    # -----------------------------------------------------
    # HISTORY MONTH
    # -----------------------------------------------------

    if data.startswith("history:"):

        month_key = data.split(":", 1)[1]

        if not re.fullmatch(
            r"\d{4}-\d{2}",
            month_key
        ):

            await query.edit_message_text(
                "❌ Oy formati noto'g'ri."
            )

            return

        await show_month_history(
            query,
            user_id,
            month_key
        )

        return


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if text == "💰 Kirim":

        return await income(
            update,
            context
        )

    if text == "💸 Xarajat":

        return await expense(
            update,
            context
        )

    if text == "📊 Hisobot":

        return await report(
            update,
            context
        )

    if text == "📜 Tarix":

        return await history(
            update,
            context
        )

    if text == "🗑 O'chirish":

        return await delete_last(
            update,
            context
        )

    if context.user_data.get("mode") in [
        "income",
        "expense"
    ]:

        return await save_transactions(
            update,
            context
        )

    await update.message.reply_text(
        "Iltimos, menyudan tanlang yoki /start bosing.",
        reply_markup=menu()
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise ValueError(
            "BOT_TOKEN topilmadi!"
        )

    if not DATABASE_URL:

        raise ValueError(
            "DATABASE_URL topilmadi!"
        )

    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()

    init_db()

    print("✅ BOT ISHGA TUSHDI")

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
            callback_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    app.run_polling()


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()