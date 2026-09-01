# bot.py
# Python 3.10+
# pip install telethon

import asyncio
import sqlite3
from datetime import datetime
from telethon import TelegramClient, events, Button

# =========================================================
# CONFIG
# =========================================================

API_ID = 8477522
API_HASH = "366c19cf69e02cad530261ad81212a85"
BOT_TOKEN = "8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek"

# SMSBower API Key
SMSBOWER_API_KEY = "d7FVPDHaenCSNq05X1lzSlpQ6Ud30kff"

ADMIN_ID = 123456789

DB_NAME = "shop.db"

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(DB_NAME, check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    balance REAL DEFAULT 0,
    created_at TEXT NOT NULL
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    flag TEXT NOT NULL,
    service TEXT DEFAULT 'telegram',
    sell_price REAL NOT NULL,
    provider_ids TEXT NOT NULL,
    enabled INTEGER DEFAULT 1
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    price REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    phone TEXT,
    activation_id TEXT,
    sms_code TEXT,
    created_at TEXT NOT NULL
)
""")

db.commit()


# =========================================================
# HELPERS
# =========================================================

def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_user(tg_id):
    user = db.execute(
        "SELECT * FROM users WHERE telegram_id=?",
        (tg_id,)
    ).fetchone()

    if not user:
        db.execute(
            "INSERT INTO users (telegram_id, created_at) VALUES (?, ?)",
            (tg_id, now())
        )
        db.commit()

        user = db.execute(
            "SELECT * FROM users WHERE telegram_id=?",
            (tg_id,)
        ).fetchone()

    return user


def get_country(country_id):
    return db.execute(
        "SELECT * FROM countries WHERE id=?",
        (country_id,)
    ).fetchone()


def is_admin(event):
    return event.sender_id == ADMIN_ID


# =========================================================
# TELEGRAM
# =========================================================

bot = TelegramClient(
    "virtual_number_shop",
    API_ID,
    API_HASH
)


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():
    return [
        [
            Button.inline("🌍 خرید شماره", b"countries"),
            Button.inline("💰 موجودی", b"balance")
        ],
        [
            Button.inline("📦 سفارش‌های من", b"orders"),
            Button.inline("📖 راهنما", b"help")
        ],
        [
            Button.inline("🆘 پشتیبانی", b"support")
        ]
    ]


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):

    get_user(event.sender_id)

    text = """
🤖 **فروشگاه شماره مجازی**

به فروشگاه خوش آمدید.

🌍 خرید شماره
💰 مشاهده موجودی
📦 سفارش‌های من
🆘 پشتیبانی
"""

    await event.respond(
        text,
        buttons=main_menu()
    )


# =========================================================
# BALANCE
# =========================================================

@bot.on(events.CallbackQuery(data=b"balance"))
async def balance(event):

    user = get_user(event.sender_id)

    await event.edit(
        f"""
💰 **موجودی حساب**

موجودی فعلی:

`{user['balance']:.2f}` USDT
""",
        buttons=[
            [Button.inline("🔙 بازگشت", b"home")]
        ]
    )


# =========================================================
# COUNTRIES
# =========================================================

@bot.on(events.CallbackQuery(data=b"countries"))
async def countries(event):

    rows = db.execute("""
        SELECT * FROM countries
        WHERE enabled=1 AND service='telegram'
        ORDER BY id ASC
    """).fetchall()

    if not rows:
        await event.edit(
            "❌ در حال حاضر کشوری برای فروش اضافه نشده است.",
            buttons=[
                [Button.inline("🔙 بازگشت", b"home")]
            ]
        )
        return

    buttons = []

    for country in rows:

        buttons.append([
            Button.inline(
                f"{country['flag']} {country['name']} • {country['sell_price']:.2f} USDT",
                f"country:{country['id']}".encode()
            )
        ])

    buttons.append([
        Button.inline("🔙 بازگشت", b"home")
    ])

    await event.edit(
        "🌍 **انتخاب کشور**\n\nکشور موردنظر را انتخاب کنید:",
        buttons=buttons
    )


# =========================================================
# COUNTRY DETAILS
# =========================================================

@bot.on(events.CallbackQuery(pattern=b"country:(\\d+)"))
async def country_details(event):

    country_id = int(event.pattern_match.group(1))

    country = get_country(country_id)

    if not country:
        await event.answer(
            "کشور پیدا نشد.",
            alert=True
        )
        return

    await event.edit(
        f"""
{country['flag']} **{country['name']}**

📱 سرویس: Telegram

💵 قیمت:
`{country['sell_price']:.2f}` USDT

🔹 Providerها:
`{country['provider_ids']}`

برای ادامه روی خرید بزنید.
""",
        buttons=[
            [
                Button.inline(
                    "🛒 خرید شماره",
                    f"buy:{country_id}".encode()
                )
            ],
            [
                Button.inline("🔙 کشورها", b"countries")
            ]
        ]
    )


# =========================================================
# BUY
# =========================================================

@bot.on(events.CallbackQuery(pattern=b"buy:(\\d+)"))
async def buy(event):

    country_id = int(event.pattern_match.group(1))

    country = get_country(country_id)

    if not country:
        await event.answer(
            "کشور پیدا نشد.",
            alert=True
        )
        return

    user = get_user(event.sender_id)

    price = float(country["sell_price"])

    if user["balance"] < price:

        await event.edit(
            f"""
❌ **موجودی کافی نیست**

قیمت:
`{price:.2f}` USDT

موجودی شما:
`{user['balance']:.2f}` USDT
""",
            buttons=[
                [Button.inline("💰 موجودی", b"balance")],
                [Button.inline("🔙 بازگشت", b"countries")]
            ]
        )
        return

    # ثبت سفارش
    cursor = db.execute("""
        INSERT INTO orders
        (telegram_id, country_id, price, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        event.sender_id,
        country_id,
        price,
        "pending",
        now()
    ))

    db.execute(
        "UPDATE users SET balance=balance-? WHERE telegram_id=?",
        (price, event.sender_id)
    )

    db.commit()

    order_id = cursor.lastrowid

    await event.edit(
        f"""
✅ **سفارش ثبت شد**

🧾 شماره سفارش:
`#{order_id}`

🌍 کشور:
{country['flag']} {country['name']}

💵 مبلغ:
`{price:.2f}` USDT

⏳ وضعیت:
در انتظار پردازش
""",
        buttons=[
            [
                Button.inline(
                    "📦 مشاهده سفارش",
                    f"order:{order_id}".encode()
                )
            ],
            [
                Button.inline("🏠 منوی اصلی", b"home")
            ]
        ]
    )


# =========================================================
# ORDERS
# =========================================================

@bot.on(events.CallbackQuery(data=b"orders"))
async def orders(event):

    rows = db.execute("""
        SELECT
            orders.*,
            countries.name,
            countries.flag
        FROM orders
        JOIN countries
        ON countries.id=orders.country_id
        WHERE orders.telegram_id=?
        ORDER BY orders.id DESC
        LIMIT 20
    """, (event.sender_id,)).fetchall()

    if not rows:

        await event.edit(
            "📦 هنوز سفارشی ثبت نکرده‌اید.",
            buttons=[
                [Button.inline("🔙 بازگشت", b"home")]
            ]
        )
        return

    text = "📦 **سفارش‌های شما**\n\n"

    for order in rows:

        text += (
            f"🧾 #{order['id']}\n"
            f"{order['flag']} {order['name']}\n"
            f"💵 {order['price']:.2f} USDT\n"
            f"📌 {order['status']}\n\n"
        )

    await event.edit(
        text,
        buttons=[
            [Button.inline("🔙 بازگشت", b"home")]
        ]
    )


# =========================================================
# SINGLE ORDER
# =========================================================

@bot.on(events.CallbackQuery(pattern=b"order:(\\d+)"))
async def order_details(event):

    order_id = int(event.pattern_match.group(1))

    order = db.execute("""
        SELECT
            orders.*,
            countries.name,
            countries.flag
        FROM orders
        JOIN countries
        ON countries.id=orders.country_id
        WHERE orders.id=? AND orders.telegram_id=?
    """, (
        order_id,
        event.sender_id
    )).fetchone()

    if not order:

        await event.answer(
            "سفارش پیدا نشد.",
            alert=True
        )
        return

    await event.edit(
        f"""
📦 **جزئیات سفارش**

🧾 شماره:
`#{order['id']}`

🌍 کشور:
{order['flag']} {order['name']}

💵 قیمت:
`{order['price']:.2f}` USDT

📌 وضعیت:
`{order['status']}`

🕐 تاریخ:
`{order['created_at']}`
""",
        buttons=[
            [Button.inline("🔙 سفارش‌ها", b"orders")]
        ]
    )


# =========================================================
# HELP
# =========================================================

@bot.on(events.CallbackQuery(data=b"help"))
async def help_page(event):

    await event.edit(
        """
📖 **راهنما**

1️⃣ ابتدا کشور موردنظر را انتخاب کنید.

2️⃣ قیمت را بررسی کنید.

3️⃣ روی 🛒 خرید شماره بزنید.

4️⃣ سفارش در سیستم ثبت می‌شود.

⚠️ بخش تأمین و تحویل شماره در این نسخه
به‌صورت placeholder قرار داده شده است.
""",
        buttons=[
            [Button.inline("🔙 بازگشت", b"home")]
        ]
    )


# =========================================================
# SUPPORT
# =========================================================

@bot.on(events.CallbackQuery(data=b"support"))
async def support(event):

    await event.edit(
        """
🆘 **پشتیبانی**

برای ارتباط با پشتیبانی پیام خود را ارسال کنید.

شناسه کاربری شما:

`%s`
""" % event.sender_id,
        buttons=[
            [Button.inline("🔙 بازگشت", b"home")]
        ]
    )


# =========================================================
# HOME
# =========================================================

@bot.on(events.CallbackQuery(data=b"home"))
async def home(event):

    await event.edit(
        """
🤖 **فروشگاه شماره مجازی**

یکی از گزینه‌های زیر را انتخاب کنید:
""",
        buttons=main_menu()
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@bot.on(events.NewMessage(pattern="/admin"))
async def admin(event):

    if not is_admin(event):
        return

    await event.respond(
        """
👑 **پنل مدیریت**

مدیریت فروشگاه:
""",
        buttons=[
            [
                Button.inline("➕ Add Country", b"admin:addcountry")
            ],
            [
                Button.inline("🌍 Countries", b"admin:countries")
            ],
            [
                Button.inline("📦 Orders", b"admin:orders")
            ],
            [
                Button.inline("👥 Users", b"admin:users")
            ],
            [
                Button.inline("📊 Statistics", b"admin:stats")
            ]
        ]
    )


# =========================================================
# ADD COUNTRY
# =========================================================

admin_states = {}


@bot.on(events.CallbackQuery(data=b"admin:addcountry"))
async def add_country_start(event):

    if not is_admin(event):
        return

    admin_states[event.sender_id] = {
        "step": 1
    }

    await event.respond(
        """
➕ **Add Country**

Step 1: کد کشور را ارسال کنید.

مثال:
`7`
"""
    )


@bot.on(events.NewMessage)
async def admin_country_wizard(event):

    if event.sender_id != ADMIN_ID:
        return

    state = admin_states.get(event.sender_id)

    if not state:
        return

    # دستورات ادمین را اینجا پردازش نکن
    if event.raw_text.startswith("/"):
        return

    step = state["step"]

    # -----------------------------------------
    # STEP 1
    # -----------------------------------------

    if step == 1:

        state["code"] = event.raw_text.strip()
        state["step"] = 2

        await event.respond(
            """
Step 2: نام کشور را ارسال کنید.

مثال:
`Russia`
"""
        )

    # -----------------------------------------
    # STEP 2
    # -----------------------------------------

    elif step == 2:

        state["name"] = event.raw_text.strip()
        state["step"] = 3

        await event.respond(
            """
Step 3: ایموجی پرچم را ارسال کنید.

مثال:
`🇷🇺`
"""
        )

    # -----------------------------------------
    # STEP 3
    # -----------------------------------------

    elif step == 3:

        state["flag"] = event.raw_text.strip()
        state["step"] = 4

        await event.respond(
            """
Step 4: سرویس

در این فروشگاه فقط Telegram فعال است.

بنویسید:
`Telegram`
"""
        )

    # -----------------------------------------
    # STEP 4
    # -----------------------------------------

    elif step == 4:

        service = event.raw_text.strip().lower()

        if service != "telegram":

            await event.respond(
                "❌ فقط سرویس Telegram مجاز است."
            )
            return

        state["service"] = "telegram"
        state["step"] = 5

        await event.respond(
            """
Step 5: قیمت فروش را ارسال کنید.

مثال:
`0.50`
"""
        )

    # -----------------------------------------
    # STEP 5
    # -----------------------------------------

    elif step == 5:

        try:
            price = float(event.raw_text.strip())

            if price <= 0:
                raise ValueError

        except ValueError:

            await event.respond(
                "❌ قیمت نامعتبر است."
            )
            return

        state["price"] = price
        state["step"] = 6

        await event.respond(
            """
Step 6: Provider IDs را ارسال کنید.

چند Provider را با کاما جدا کنید.

مثال:
`3170,4120,2211`
"""
        )

    # -----------------------------------------
    # STEP 6
    # -----------------------------------------

    elif step == 6:

        providers = event.raw_text.strip()

        if not providers:

            await event.respond(
                "❌ Provider ID نمی‌تواند خالی باشد."
            )
            return

        db.execute("""
            INSERT INTO countries
            (code, name, flag, service, sell_price, provider_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            state["code"],
            state["name"],
            state["flag"],
            state["service"],
            state["price"],
            providers
        ))

        db.commit()

        del admin_states[event.sender_id]

        await event.respond(
            f"""
✅ **کشور با موفقیت اضافه شد**

🌍 {state['flag']} {state['name']}

🔢 Code:
`{state['code']}`

📱 Service:
Telegram

💵 Price:
`{state['price']:.2f}` USDT

🔹 Providers:
`{providers}`
"""
        )


# =========================================================
# ADMIN COUNTRIES
# =========================================================

@bot.on(events.CallbackQuery(data=b"admin:countries"))
async def admin_countries(event):

    if not is_admin(event):
        return

    rows = db.execute(
        "SELECT * FROM countries ORDER BY id ASC"
    ).fetchall()

    if not rows:

        await event.edit(
            "🌍 هیچ کشوری اضافه نشده است."
        )
        return

    text = "🌍 **Countries**\n\n"

    for c in rows:

        status = "🟢" if c["enabled"] else "🔴"

        text += (
            f"{status} {c['flag']} {c['name']}\n"
            f"Code: `{c['code']}`\n"
            f"Price: `{c['sell_price']:.2f}`\n"
            f"Providers: `{c['provider_ids']}`\n\n"
        )

    await event.edit(text)


# =========================================================
# ADMIN USERS
# =========================================================

@bot.on(events.CallbackQuery(data=b"admin:users"))
async def admin_users(event):

    if not is_admin(event):
        return

    total = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    await event.edit(
        f"""
👥 **Users**

تعداد کاربران:
`{total}`
"""
    )


# =========================================================
# ADMIN ORDERS
# =========================================================

@bot.on(events.CallbackQuery(data=b"admin:orders"))
async def admin_orders(event):

    if not is_admin(event):
        return

    total = db.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    pending = db.execute(
        "SELECT COUNT(*) FROM orders WHERE status='pending'"
    ).fetchone()[0]

    completed = db.execute(
        "SELECT COUNT(*) FROM orders WHERE status='completed'"
    ).fetchone()[0]

    await event.edit(
        f"""
📦 **Orders**

کل سفارش‌ها:
`{total}`

⏳ Pending:
`{pending}`

✅ Completed:
`{completed}`
"""
    )


# =========================================================
# ADMIN STATISTICS
# =========================================================

@bot.on(events.CallbackQuery(data=b"admin:stats"))
async def admin_stats(event):

    if not is_admin(event):
        return

    users = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    orders = db.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    revenue = db.execute(
        "SELECT COALESCE(SUM(price),0) FROM orders"
    ).fetchone()[0]

    await event.edit(
        f"""
📊 **Statistics**

👥 Users:
`{users}`

📦 Orders:
`{orders}`

💰 Total sales:
`{revenue:.2f}` USDT
"""
    )


# =========================================================
# RUN
# =========================================================

async def main():

    print("Bot starting...")

    await bot.start(
        bot_token=BOT_TOKEN
    )

    print("Bot is running.")

    await bot.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
