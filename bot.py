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
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Token Render Environment Variable'dan olinadi
TOKEN = os.environ.get("BOT_TOKEN")

DATA_FILE = "data.json"

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


# =========================================================
# RENDER WEB SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Finance Bot is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Web server running on port {port}")

    server.serve_forever()


# =========================================================
# DATA
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# MAIN MENU
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
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "💵 Finance Bot\n\n"
        "Kerakli bo'limni tanlang.",
        reply_markup=menu()
    )


# =========================================================
# INCOME
# =========================================================

async def income(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data["mode"] = "income"

    await update.message.reply_text(
        "💰 KIRIM\n\n"
        "Summa va izoh yozing.\n\n"
        "Misol:\n"
        "5000000 Maosh\n\n"
        "Saqlash uchun yuboring."
    )


# =========================================================
# EXPENSE
# =========================================================

async def expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data["mode"] = "pick_category"

    keyboard = [
        [category]
        for category in CATEGORIES
    ]

    keyboard.append(["❌ Bekor qilish"])

    await update.message.reply_text(
        "💸 XARAJAT\n\n"
        "Kategoriyani tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# =========================================================
# EXPENSE INPUT
# =========================================================

async def save_transactions(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    mode = context.user_data.get("mode")

    # -----------------------------------------------------
    # CATEGORY SELECT
    # -----------------------------------------------------

    if mode == "pick_category":

        if text == "❌ Bekor qilish":

            context.user_data.clear()

            await update.message.reply_text(
                "Bekor qilindi.",
                reply_markup=menu()
            )

            return

        if text not in CATEGORIES:

            await update.message.reply_text(
                "Iltimos, kategoriyalardan birini tanlang."
            )

            return

        context.user_data["category"] = text
        context.user_data["mode"] = "expense"

        await update.message.reply_text(
            f"📂 {text}\n\n"
            "Endi xarajatlarni kiriting.\n\n"
            "Bir nechta xarajatni BIR XABARDA "
            "ham yuborishingiz mumkin:\n\n"
            "50000 non\n"
            "120000 supermarket\n"
            "35000 meva\n\n"
            "Yoki bittadan kiriting.\n\n"
            "Har bir qatorda:\n"
            "SUMMA IZOH",
            reply_markup=ReplyKeyboardMarkup(
                [["✅ Tugatish", "❌ Bekor qilish"]],
                resize_keyboard=True
            )
        )

        return

    # -----------------------------------------------------
    # FINISH EXPENSE MODE
    # -----------------------------------------------------

    if mode == "expense":

        if text == "✅ Tugatish":

            context.user_data.clear()

            await update.message.reply_text(
                "✅ Xarajat kiritish tugatildi.",
                reply_markup=menu()
            )

            return

        if text == "❌ Bekor qilish":

            context.user_data.clear()

            await update.message.reply_text(
                "❌ Bekor qilindi.",
                reply_markup=menu()
            )

            return

    # -----------------------------------------------------
    # INCOME / EXPENSE
    # -----------------------------------------------------

    if mode not in ["income", "expense"]:

        return

    # =====================================================
    # INCOME
    # =====================================================

    if mode == "income":

        parts = text.split(maxsplit=1)

        if len(parts) < 2:

            await update.message.reply_text(
                "❌ Format noto'g'ri.\n\n"
                "Masalan:\n"
                "5000000 Maosh"
            )

            return

        try:

            amount = float(
                parts[0]
                .replace(",", "")
                .replace(".", "")
                .replace(" ", "")
            )

        except ValueError:

            await update.message.reply_text(
                "❌ Summa noto'g'ri."
            )

            return

        description = parts[1]

        data = load_data()

        data.append(
            {
                "user_id": update.effective_user.id,
                "type": "income",
                "amount": amount,
                "description": description,
                "category": "💰 Kirim",
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }
        )

        save_data(data)

        context.user_data.clear()

        await update.message.reply_text(
            "💰 KIRIM SAQLANDI\n\n"
            f"{amount:,.0f} so'm\n"
            f"📝 {description}",
            reply_markup=menu()
        )

        return

    # =====================================================
    # EXPENSE
    # =====================================================

    lines = text.splitlines()

    valid_transactions = []
    errors = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        parts = line.split(maxsplit=1)

        if len(parts) < 2:

            errors.append(line)

            continue

        try:

            amount = float(
                parts[0]
                .replace(",", "")
                .replace(".", "")
                .replace(" ", "")
            )

        except ValueError:

            errors.append(line)

            continue

        description = parts[1]

        valid_transactions.append(
            {
                "user_id": update.effective_user.id,
                "type": "expense",
                "amount": amount,
                "description": description,
                "category": context.user_data["category"],
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }
        )

    # -----------------------------------------------------
    # NOTHING VALID
    # -----------------------------------------------------

    if not valid_transactions:

        await update.message.reply_text(
            "❌ Xarajatni tushuna olmadim.\n\n"
            "Masalan:\n"
            "50000 non\n"
            "120000 supermarket\n"
            "35000 meva"
        )

        return

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    data = load_data()

    data.extend(valid_transactions)

    save_data(data)

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    total = sum(
        item["amount"]
        for item in valid_transactions
    )

    response = (
        f"✅ {len(valid_transactions)} ta xarajat saqlandi!\n\n"
        f"📂 {context.user_data['category']}\n"
        f"💸 Jami: {total:,.0f} so'm\n\n"
    )

    for item in valid_transactions:

        response += (
            f"• {item['amount']:,.0f} so'm — "
            f"{item['description']}\n"
        )

    if errors:

        response += (
            "\n⚠️ Saqlanmagan qatorlar:\n"
        )

        for error in errors:

            response += f"• {error}\n"

    response += (
        "\nYana xarajat yuborishingiz mumkin "
        "yoki tugatish uchun:"
    )

    await update.message.reply_text(
        response,
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Tugatish", "❌ Bekor qilish"]],
            resize_keyboard=True
        )
    )


# =========================================================
# MONTHLY REPORT
# =========================================================

async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = load_data()

    user_id = update.effective_user.id

    month = datetime.now().strftime("%Y-%m")

    rows = [
        item
        for item in data
        if item["user_id"] == user_id
        and item["date"].startswith(month)
    ]

    income_total = sum(
        item["amount"]
        for item in rows
        if item["type"] == "income"
    )

    expense_total = sum(
        item["amount"]
        for item in rows
        if item["type"] == "expense"
    )

    balance = income_total - expense_total

    categories = defaultdict(float)

    for item in rows:

        if item["type"] == "expense":

            categories[item["category"]] += item["amount"]

    text = (
        "📊 OYLIK HISOBOT\n\n"
        f"📅 {month}\n\n"
        f"💰 Kirim: {income_total:,.0f} so'm\n"
        f"💸 Xarajat: {expense_total:,.0f} so'm\n"
        f"💵 Qoldiq: {balance:,.0f} so'm\n\n"
        "📋 KATEGORIYALAR\n"
    )

    if categories:

        top_category = max(
            categories,
            key=categories.get
        )

        for category, amount in sorted(
            categories.items(),
            key=lambda item: item[1],
            reverse=True
        ):

            text += (
                f"{category}: "
                f"{amount:,.0f} so'm\n"
            )

        text += (
            f"\n🏆 Eng ko'p: "
            f"{top_category}\n"
            f"{categories[top_category]:,.0f} so'm"
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

async def history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = [
        item
        for item in load_data()
        if item["user_id"] == update.effective_user.id
    ]

    data = data[-10:]

    if not data:

        await update.message.reply_text(
            "📜 Tarix bo'sh.",
            reply_markup=menu()
        )

        return

    text = "📜 OXIRGI 10 TA\n\n"

    for item in reversed(data):

        if item["type"] == "income":

            emoji = "💰"
            sign = "+"

        else:

            emoji = item["category"]
            sign = "-"

        text += (
            f"{emoji}\n"
            f"{sign}{item['amount']:,.0f} so'm\n"
            f"📝 {item['description']}\n"
            f"📅 {item['date']}\n\n"
        )

    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================================================
# DELETE LAST TRANSACTION
# =========================================================

async def delete_last(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = [
        item
        for item in load_data()
        if item["user_id"] == update.effective_user.id
    ]

    if not data:

        await update.message.reply_text(
            "🗑 O'chirish uchun yozuv yo'q.",
            reply_markup=menu()
        )

        return

    item = data[-1]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ha",
                    callback_data="yes"
                ),
                InlineKeyboardButton(
                    "❌ Yo'q",
                    callback_data="no"
                )
            ]
        ]
    )

    await update.message.reply_text(
        "🗑 Oxirgi yozuvni o'chirish?\n\n"
        f"{item['amount']:,.0f} so'm\n"
        f"📝 {item['description']}",
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

    if query.data == "no":

        await query.edit_message_text(
            "❌ Bekor qilindi."
        )

        return

    data = load_data()

    user_id = query.from_user.id

    indexes = [
        index
        for index, item in enumerate(data)
        if item["user_id"] == user_id
    ]

    if not indexes:

        await query.edit_message_text(
            "O'chirish uchun yozuv topilmadi."
        )

        return

    index = indexes[-1]

    item = data.pop(index)

    save_data(data)

    await query.edit_message_text(
        "✅ O'chirildi\n\n"
        f"{item['amount']:,.0f} so'm\n"
        f"{item['description']}"
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    # Main menu

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

    # Transaction input

    if context.user_data.get("mode") in [
        "income",
        "expense",
        "pick_category"
    ]:

        return await save_transactions(
            update,
            context
        )

    await update.message.reply_text(
        "/start bosing",
        reply_markup=menu()
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable topilmadi."
        )

    # Render HTTP server
    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    # Telegram bot
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print("BOT ISHGA TUSHDI")

    application.run_polling()


if __name__ == "__main__":

    main()
