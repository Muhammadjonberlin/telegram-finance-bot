import os
import re
import psycopg2
from datetime import datetime
from collections import defaultdict

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# DATABASE
# =========================

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
    cur.close()
    conn.close()


def add_transaction(user_id, tx_type, amount, description, category):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions
        (user_id, type, amount, description, category)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, tx_type, amount, description, category))

    conn.commit()
    cur.close()
    conn.close()


# =========================
# CATEGORIES
# =========================

CATEGORIES = {
    "food": "🍔 Oziq-ovqat",
    "transport": "🚗 Transport",
    "home": "🏠 Uy-joy",
    "shopping": "🛍 Xaridlar",
    "cafe": "☕ Kafe",
    "health": "💊 Sog'liq",
    "phone": "📱 Aloqa",
    "education": "📚 Ta'lim",
    "credit": "💳 Kredit",
    "other": "📦 Boshqa",
}


def detect_category(text):
    """
    Xarajat matniga qarab kategoriyani avtomatik aniqlaydi.
    """

    text = text.lower()

    # Oziq-ovqat
    food_words = [
        "ovqat",
        "go'sht",
        "gosht",
        "suv",
        "sabzavot",
        "meva",
        "non",
        "sut",
        "pishloq",
        "tuxum",
        "guruch",
        "kartoshka",
        "pomidor",
        "bodring",
        "shirinlik",
        "shokolad",
        "kolbasa",
        "mahsulot",
        "oziq",
        "ichimlik",
    ]

    # Transport
    transport_words = [
        "gas",
        "gaz",
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
    ]

    # Uy-joy
    home_words = [
        "kommunal",
        "svet",
        "elektr",
        "elektr toki",
        "gaz to'lovi",
        "gaz to‘lovi",
        "suv to'lovi",
        "suv to‘lovi",
        "ijara",
        "kvartira",
        "uy",
        "internet",
        "uy-joy",
        "uy joy",
    ]

    # Ta'lim
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

    # Kafe
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

    # Sog'liq
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

    # Aloqa
    phone_words = [
        "telefon",
        "sim karta",
        "internet paket",
        "tarif",
        "aloqa",
        "mobil",
    ]

    # Kredit
    credit_words = [
        "kredit",
        "qarz",
        "bank to'lovi",
        "bank to‘lovi",
    ]

    # Xaridlar
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

    if any(word in text for word in food_words):
        return CATEGORIES["food"]

    if any(word in text for word in transport_words):
        return CATEGORIES["transport"]

    if any(word in text for word in home_words):
        return CATEGORIES["home"]

    if any(word in text for word in education_words):
        return CATEGORIES["education"]

    if any(word in text for word in cafe_words):
        return CATEGORIES["cafe"]

    if any(word in text for word in health_words):
        return CATEGORIES["health"]

    if any(word in text for word in phone_words):
        return CATEGORIES["phone"]

    if any(word in text for word in credit_words):
        return CATEGORIES["credit"]

    if any(word in text for word in shopping_words):
        return CATEGORIES["shopping"]

    return CATEGORIES["other"]


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
        "Masalan:\n"
        "5000000 Maosh"
    )


# =========================
# EXPENSE
# =========================

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


# =========================
# SAVE MULTIPLE EXPENSES
# =========================

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

        # Summa + izoh
        match = re.match(
            r"^([\d\s,\.]+)\s+(.+)$",
            line
        )

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


# =========================
# REPORT
# =========================

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, amount, category
        FROM transactions
        WHERE user_id = %s
        AND DATE_TRUNC('month', created_at)
            = DATE_TRUNC('month', CURRENT_DATE)
    """, (uid,))

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

    month = datetime.now().strftime("%Y-%m")

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
            key=lambda x: x[1],
            reverse=True
        ):
            text += f"{category}: {amount:,.0f} so'm\n"

        top = max(categories, key=categories.get)

        text += (
            f"\n🏆 Eng ko'p xarajat:\n"
            f"{top} — {categories[top]:,.0f} so'm"
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

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, amount, description, category, created_at
        FROM transactions
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 10
    """, (uid,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:

        await update.message.reply_text(
            "📜 Tarix bo'sh.",
            reply_markup=menu()
        )

        return

    text = "📜 OXIRGI 10 TA\n\n"

    for tx_type, amount, description, category, created_at in rows:

        if tx_type == "income":
            sign = "+"
            icon = "💰"
        else:
            sign = "-"
            icon = category

        text += (
            f"{icon}\n"
            f"{sign}{float(amount):,.0f} so'm\n"
            f"📝 {description}\n"
            f"📅 {created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        )

    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================
# DELETE LAST
# =========================

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
        f"✅ Oxirgi yozuv o'chirildi.\n\n"
        f"{float(amount):,.0f} so'm\n"
        f"{description}",
        reply_markup=menu()
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
        "Iltimos, menyudan tanlang yoki /start bosing.",
        reply_markup=menu()
    )


# =========================
# START BOT
# =========================

def main():

    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL topilmadi!")

    init_db()

    print("BOT ISHGA TUSHDI")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
