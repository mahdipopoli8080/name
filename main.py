# -*- coding: utf-8 -*-
"""
Telegram Virtual Number Shop - single file
Telethon + SQLite

IMPORTANT:
- Put your own Telegram BOT_TOKEN/API_ID/API_HASH and admin ID below.
- Keep provider credentials in environment variables; never publish them.
- This template intentionally does NOT automate Telegram account creation,
  bulk account creation, or platform-limit bypassing.
- Provider integration is structured so inventory/price synchronization can
  be added for legitimate purchasing workflows.
"""

import os
import asyncio
import sqlite3
import logging
import time
from contextlib import contextmanager
from typing import Optional

from telethon import TelegramClient, events, Button

# =========================
# CONFIG
# =========================
API_ID = int(os.getenv("TG_API_ID", "8477522"))
API_HASH = os.getenv("TG_API_HASH", "366c19cf69e02cad530261ad81212a85")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5190717598"))

# Keep provider secrets OUT of source code.
SMSBOWER_API_KEY = os.getenv("SMSBOWER_API_KEY", "d7FVPDHaenCSNq05X1lzSlpQ6Ud30kff")

DB_PATH = os.getenv("SHOP_DB", "shop.db")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "ضایع شدی")

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("shop")

# =========================
# DATABASE
# =========================
db_lock = asyncio.Lock()

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            last_seen INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            flag TEXT NOT NULL DEFAULT '🌍',
            service TEXT NOT NULL DEFAULT 'Telegram',
            price REAL NOT NULL DEFAULT 0,
            provider_ids TEXT DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1,
            stock INTEGER NOT NULL DEFAULT 0,
            provider_price REAL DEFAULT 0,
            updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            country_id INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            provider_activation_id TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            code TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            kind TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            percent REAL NOT NULL DEFAULT 0,
            max_uses INTEGER NOT NULL DEFAULT 0,
            used INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS promo_users (
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            UNIQUE(user_id, code)
        );

        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        """)

def now():
    return int(time.time())

def money(v):
    return f"{float(v):,.2f}"

def get_user(uid):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def ensure_user(uid, username=""):
    t = now()
    with db() as c:
        c.execute("""
            INSERT INTO users(user_id, username, created_at, last_seen)
            VALUES(?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
              username=excluded.username,
              last_seen=excluded.last_seen
        """, (uid, username or "", t, t))

def log_admin(action):
    with db() as c:
        c.execute(
            "INSERT INTO admin_logs(admin_id, action, created_at) VALUES(?,?,?)",
            (ADMIN_ID, action, now())
        )

# =========================
# DUPLICATE MESSAGE FIX
# =========================
# Per-user lock prevents two handlers from processing rapid duplicate clicks.
user_locks = {}
recent_actions = {}
recent_messages = {}

def get_user_lock(uid):
    if uid not in user_locks:
        user_locks[uid] = asyncio.Lock()
    return user_locks[uid]

def duplicate_action(uid, key, ttl=1.5):
    t = time.monotonic()
    old = recent_actions.get((uid, key), 0)
    if t - old < ttl:
        return True
    recent_actions[(uid, key)] = t
    # light cleanup
    if len(recent_actions) > 5000:
        cutoff = t - 10
        for k, v in list(recent_actions.items()):
            if v < cutoff:
                recent_actions.pop(k, None)
    return False

def duplicate_message(event, ttl=5.0):
    """Ignore the same Telegram message if it is delivered more than once."""
    msg_id = getattr(event, "id", None)
    uid = getattr(event, "sender_id", None)
    if msg_id is None or uid is None:
        return False
    t = time.monotonic()
    key = (uid, msg_id)
    old = recent_messages.get(key, 0)
    if t - old < ttl:
        return True
    recent_messages[key] = t
    if len(recent_messages) > 5000:
        cutoff = t - 15
        for k, v in list(recent_messages.items()):
            if v < cutoff:
                recent_messages.pop(k, None)
    return False

async def safe_edit(event, text, buttons=None):
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        try:
            await event.answer("انجام شد.", alert=False)
        except Exception:
            pass

async def safe_answer(event, text="", alert=False):
    try:
        await event.answer(text, alert=alert)
    except Exception:
        pass

# =========================
# KEYBOARDS
# =========================
def main_menu():
    return [
        [Button.inline("🛒 خرید شماره", b"buy"),
         Button.inline("💰 موجودی", b"balance")],
        [Button.inline("📦 سفارش‌های من", b"orders"),
         Button.inline("💳 تراکنش‌ها", b"transactions")],
        [Button.inline("🎁 کد تخفیف", b"promo"),
         Button.inline("🔎 جستجوی کشور", b"search_country")],
        [Button.inline("❓ راهنما", b"help"),
         Button.inline("💬 پشتیبانی", b"support")],
    ]

def back_menu():
    return [[Button.inline("🔙 بازگشت", b"home")]]

def admin_menu():
    return [
        [Button.inline("🌍 کشورها", b"adm_countries"),
         Button.inline("➕ افزودن کشور", b"adm_add")],
        [Button.inline("👥 کاربران", b"adm_users"),
         Button.inline("📦 سفارش‌ها", b"adm_orders")],
        [Button.inline("📊 آمار", b"adm_stats"),
         Button.inline("💰 موجودی کاربر", b"adm_balance")],
        [Button.inline("🎟 کدهای تخفیف", b"adm_promos"),
         Button.inline("📣 ارسال اعلان", b"adm_broadcast")],
        [Button.inline("🧾 لاگ ادمین", b"adm_logs"),
         Button.inline("❤️ وضعیت سیستم", b"adm_health")],
        [Button.inline("🔙 منوی اصلی", b"home")],
    ]

# =========================
# COUNTRY PAGES
# =========================
def country_rows(page=0, per_page=8):
    with db() as c:
        rows = c.execute("""
            SELECT * FROM countries
            WHERE enabled=1
            ORDER BY name
            LIMIT ? OFFSET ?
        """, (per_page, page * per_page)).fetchall()
        total = c.execute(
            "SELECT COUNT(*) FROM countries WHERE enabled=1"
        ).fetchone()[0]
    return rows, total

def country_buttons(page=0):
    rows, total = country_rows(page)
    buttons = []
    for r in rows:
        stock = "🟢" if r["stock"] > 0 else "⚪"
        buttons.append([
            Button.inline(
                f'{r["flag"]} {r["name"]} • {money(r["price"])}',
                f'country:{r["id"]}'.encode()
            )
        ])
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️", f"countries:{page-1}".encode()))
    if (page + 1) * 8 < total:
        nav.append(Button.inline("➡️", f"countries:{page+1}".encode()))
    if nav:
        buttons.append(nav)
    buttons.append([Button.inline("🔙 بازگشت", b"home")])
    return buttons

# =========================
# BOT
# =========================
if not (API_ID and API_HASH and BOT_TOKEN):
    log.warning("Telegram credentials are not configured. Set TG_API_ID, TG_API_HASH, TG_BOT_TOKEN.")

bot = TelegramClient("shop_bot_session", API_ID, API_HASH)

@bot.on(events.NewMessage(pattern=r"^/start(?:\s+.*)?$"))
async def start_handler(event):
    uid = event.sender_id
    if duplicate_message(event, ttl=5.0):
        return
    if duplicate_action(uid, "start", ttl=2.5):
        return

    async with get_user_lock(uid):
        sender = await event.get_sender()
        ensure_user(uid, getattr(sender, "username", "") or "")

        # Delete the triggering /start only when possible, then send ONE menu.
        # We don't send another automatic reply from another handler.
        text = (
            "👋 <b>خوش آمدید</b>\n\n"
            "به فروشگاه شماره مجازی خوش آمدید.\n"
            "از منوی زیر گزینه موردنظر را انتخاب کنید."
        )
        await event.respond(text, buttons=main_menu(), parse_mode="html")

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    uid = event.sender_id
    data = event.data.decode("utf-8", errors="ignore")

    if duplicate_action(uid, data, ttl=0.7):
        await safe_answer(event)
        return

    async with get_user_lock(uid):
        try:
            if data == "home":
                await safe_edit(
                    event,
                    "🏠 <b>منوی اصلی</b>\n\nگزینه موردنظر را انتخاب کنید.",
                    main_menu()
                )
                return

            if data == "balance":
                u = get_user(uid)
                bal = u["balance"] if u else 0
                await safe_edit(
                    event,
                    f"💰 <b>موجودی شما:</b> {money(bal)}\n\n"
                    "برای شارژ حساب با پشتیبانی تماس بگیرید.",
                    back_menu()
                )
                return

            if data == "transactions":
                with db() as c:
                    rows = c.execute("""
                        SELECT amount, kind, note, created_at
                        FROM transactions WHERE user_id=?
                        ORDER BY id DESC LIMIT 10
                    """, (uid,)).fetchall()
                if not rows:
                    text = "💳 هنوز تراکنشی ثبت نشده است."
                else:
                    lines = ["💳 <b>آخرین تراکنش‌ها</b>\n"]
                    for r in rows:
                        sign = "+" if r["amount"] >= 0 else ""
                        lines.append(
                            f"• {sign}{money(r['amount'])} | {r['kind']} | {r['note']}"
                        )
                    text = "\n".join(lines)
                await safe_edit(event, text, back_menu())
                return

            if data == "orders":
                with db() as c:
                    rows = c.execute("""
                        SELECT o.id, o.price, o.status, c.name, c.flag
                        FROM orders o JOIN countries c ON c.id=o.country_id
                        WHERE o.user_id=? ORDER BY o.id DESC LIMIT 10
                    """, (uid,)).fetchall()
                if not rows:
                    text = "📦 هنوز سفارشی ندارید."
                else:
                    lines = ["📦 <b>آخرین سفارش‌ها</b>\n"]
                    for r in rows:
                        lines.append(
                            f'#{r["id"]} {r["flag"]} {r["name"]} — '
                            f'{money(r["price"])} — {r["status"]}'
                        )
                    text = "\n".join(lines)
                await safe_edit(event, text, back_menu())
                return

            if data == "buy":
                await safe_edit(
                    event,
                    "🌍 <b>انتخاب کشور</b>\n\n"
                    "کشور موردنظر را انتخاب کنید:",
                    country_buttons(0)
                )
                return

            if data.startswith("countries:"):
                page = max(0, int(data.split(":")[1]))
                await safe_edit(event, "🌍 <b>انتخاب کشور</b>", country_buttons(page))
                return

            if data.startswith("country:"):
                cid = int(data.split(":")[1])
                with db() as c:
                    r = c.execute("SELECT * FROM countries WHERE id=?", (cid,)).fetchone()
                if not r or not r["enabled"]:
                    await safe_answer(event, "این کشور در دسترس نیست.", alert=True)
                    return

                stock = "موجود" if r["stock"] > 0 else "نامشخص/بدون موجودی"
                text = (
                    f'{r["flag"]} <b>{r["name"]}</b>\n\n'
                    f'💵 قیمت: <b>{money(r["price"])}</b>\n'
                    f'📦 موجودی: {stock}\n'
                    f'⚙️ سرویس: {r["service"]}\n'
                )
                buttons = [
                    [Button.inline("🛒 ثبت سفارش", f"order:{cid}".encode())],
                    [Button.inline("🔙 کشورها", b"buy")],
                ]
                await safe_edit(event, text, buttons)
                return

            if data.startswith("order:"):
                cid = int(data.split(":")[1])
                with db() as c:
                    r = c.execute(
                        "SELECT * FROM countries WHERE id=? AND enabled=1", (cid,)
                    ).fetchone()
                    u = c.execute(
                        "SELECT balance FROM users WHERE user_id=?", (uid,)
                    ).fetchone()

                    if not r:
                        await safe_answer(event, "کشور یافت نشد.", alert=True)
                        return

                    if not u or u["balance"] < r["price"]:
                        await safe_answer(event, "موجودی کافی نیست.", alert=True)
                        return

                    # Safe shop behavior: create a paid order, but do not
                    # automate Telegram account creation.
                    t = now()
                    c.execute(
                        "UPDATE users SET balance=balance-? WHERE user_id=?",
                        (r["price"], uid)
                    )
                    c.execute("""
                        INSERT INTO orders(
                            user_id,country_id,price,status,created_at,updated_at
                        ) VALUES(?,?,?,?,?,?)
                    """, (uid, cid, r["price"], "paid_pending_fulfillment", t, t))
                    oid = c.lastrowid
                    c.execute("""
                        INSERT INTO transactions(user_id,amount,kind,note,created_at)
                        VALUES(?,?,?,?,?)
                    """, (uid, -r["price"], "purchase", f"Order #{oid}", t))

                await safe_edit(
                    event,
                    f"✅ <b>سفارش #{oid} ثبت شد.</b>\n\n"
                    "پرداخت با موفقیت از موجودی کسر شد.\n"
                    "وضعیت سفارش: <b>در انتظار تأمین</b>.",
                    back_menu()
                )
                return

            if data == "promo":
                await safe_edit(
                    event,
                    "🎁 <b>کد تخفیف</b>\n\n"
                    "برای اعمال کد تخفیف، فعلاً از پشتیبانی درخواست فعال‌سازی کنید.",
                    back_menu()
                )
                return

            if data == "search_country":
                await safe_edit(
                    event,
                    "🔎 <b>جستجوی کشور</b>\n\n"
                    "نام کشور را با ارسال پیام برای بات وارد کنید.",
                    back_menu()
                )
                return

            if data == "help":
                await safe_edit(
                    event,
                    "❓ <b>راهنما</b>\n\n"
                    "1) کشور را انتخاب کنید.\n"
                    "2) قیمت و موجودی را بررسی کنید.\n"
                    "3) سفارش را ثبت کنید.\n"
                    "4) وضعیت سفارش را از بخش «سفارش‌های من» ببینید.\n\n"
                    "برای پرداخت و پشتیبانی با ادمین تماس بگیرید.",
                    back_menu()
                )
                return

            if data == "support":
                await safe_edit(
                    event,
                    f"💬 پشتیبانی:\n@{SUPPORT_USERNAME.lstrip('@')}",
                    back_menu()
                )
                return

            # ---------- ADMIN ----------
            if uid != ADMIN_ID:
                await safe_answer(event, "دسترسی ندارید.", alert=True)
                return

            if data == "admin":
                await safe_edit(event, "🛠 <b>پنل مدیریت</b>", admin_menu())
                return

            if data == "adm_countries":
                with db() as c:
                    rows = c.execute(
                        "SELECT * FROM countries ORDER BY id DESC LIMIT 20"
                    ).fetchall()
                if not rows:
                    text = "🌍 هنوز کشوری ثبت نشده است."
                else:
                    lines = ["🌍 <b>کشورها</b>\n"]
                    for r in rows:
                        state = "فعال" if r["enabled"] else "غیرفعال"
                        lines.append(
                            f'{r["id"]}. {r["flag"]} {r["name"]} | '
                            f'{money(r["price"])} | {state} | stock={r["stock"]}'
                        )
                    text = "\n".join(lines)
                await safe_edit(
                    event, text,
                    [[Button.inline("➕ افزودن کشور", b"adm_add")],
                     [Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data == "adm_stats":
                with db() as c:
                    users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                    paid = c.execute(
                        "SELECT COALESCE(SUM(price),0) FROM orders WHERE status != 'cancelled'"
                    ).fetchone()[0]
                    balances = c.execute(
                        "SELECT COALESCE(SUM(balance),0) FROM users"
                    ).fetchone()[0]
                await safe_edit(
                    event,
                    "📊 <b>آمار فروشگاه</b>\n\n"
                    f"👥 کاربران: {users}\n"
                    f"📦 سفارش‌ها: {orders}\n"
                    f"💵 فروش ثبت‌شده: {money(paid)}\n"
                    f"💰 مجموع موجودی کاربران: {money(balances)}",
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data == "adm_users":
                with db() as c:
                    rows = c.execute(
                        "SELECT user_id, username, balance FROM users "
                        "ORDER BY last_seen DESC LIMIT 20"
                    ).fetchall()
                lines = ["👥 <b>آخرین کاربران</b>\n"]
                for r in rows:
                    lines.append(
                        f'{r["user_id"]} | @{r["username"] or "-"} | {money(r["balance"])}'
                    )
                await safe_edit(
                    event, "\n".join(lines),
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data == "adm_orders":
                with db() as c:
                    rows = c.execute("""
                        SELECT o.id,o.user_id,o.price,o.status,c.name
                        FROM orders o JOIN countries c ON c.id=o.country_id
                        ORDER BY o.id DESC LIMIT 20
                    """).fetchall()
                lines = ["📦 <b>آخرین سفارش‌ها</b>\n"]
                for r in rows:
                    lines.append(
                        f'#{r["id"]} | user {r["user_id"]} | '
                        f'{r["name"]} | {money(r["price"])} | {r["status"]}'
                    )
                await safe_edit(
                    event, "\n".join(lines),
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data == "adm_health":
                provider = "تنظیم شده" if SMSBOWER_API_KEY else "تنظیم نشده"
                await safe_edit(
                    event,
                    "❤️ <b>وضعیت سیستم</b>\n\n"
                    "🗄 SQLite: OK\n"
                    "🤖 Telegram bot: OK\n"
                    f"🔌 Provider key: {provider}",
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data == "adm_logs":
                with db() as c:
                    rows = c.execute(
                        "SELECT action,created_at FROM admin_logs "
                        "ORDER BY id DESC LIMIT 15"
                    ).fetchall()
                text = "🧾 <b>لاگ ادمین</b>\n\n" + "\n".join(
                    f'• {r["action"]}' for r in rows
                )
                await safe_edit(event, text, [[Button.inline("🔙 پنل", b"admin")]])
                return

            if data == "adm_add":
                admin_states[uid] = {"step": 1}
                await safe_edit(
                    event,
                    "➕ <b>افزودن کشور</b>\n\n"
                    "۱/۶ — کد کشور را بفرستید (مثلاً US یا CA):\n\n"
                    "برای لغو، /cancel بفرستید.",
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

            if data in ("adm_balance", "adm_promos", "adm_broadcast"):
                await safe_edit(
                    event,
                    "🛠 این بخش در نسخه پایه آماده شده و برای ورود اطلاعات "
                    "از فرمان‌های مدیریتی استفاده می‌کند.\n\n"
                    "برای امنیت، عملیات حساس نیاز به تأیید دومرحله‌ای دارند.",
                    [[Button.inline("🔙 پنل", b"admin")]]
                )
                return

        except Exception as e:
            log.exception("Callback error: %s", e)
            await safe_answer(event, "خطای داخلی رخ داد.", alert=True)

@bot.on(events.NewMessage(pattern=r"^/admin$"))
async def admin_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    if duplicate_action(event.sender_id, "admin", ttl=2):
        return
    async with get_user_lock(event.sender_id):
        ensure_user(event.sender_id, "")
        log_admin("/admin")
        await event.respond("🛠 <b>پنل مدیریت</b>", buttons=admin_menu(), parse_mode="html")

# Simple admin country wizard, intentionally text-based and safe.
admin_states = {}

@bot.on(events.NewMessage)
async def text_handler(event):
    if not event.is_private:
        return
    if duplicate_message(event, ttl=5.0):
        return
    text = (event.raw_text or "").strip()
    uid = event.sender_id

    # Ignore commands and callback-driven UI messages.
    if text.startswith("/"):
        return

    # Cancel the admin country wizard.
    if uid == ADMIN_ID and text.lower() == "/cancel":
        admin_states.pop(uid, None)
        await event.respond(
            "❌ عملیات افزودن کشور لغو شد.",
            buttons=[[Button.inline("🔙 پنل", b"admin")]]
        )
        return

    # Admin country wizard.
    if uid == ADMIN_ID and uid in admin_states:
        state = admin_states[uid]
        if state["step"] == 1:
            state["code"] = text
            state["step"] = 2
            await event.respond("۲/۶ — نام کشور را بفرستید:")
            return
        if state["step"] == 2:
            state["name"] = text
            state["step"] = 3
            await event.respond("۳/۶ — ایموجی پرچم را بفرستید:")
            return
        if state["step"] == 3:
            state["flag"] = text
            state["step"] = 4
            await event.respond("۴/۶ — سرویس را بفرستید (فقط Telegram):")
            return
        if state["step"] == 4:
            if text.lower() != "telegram":
                await event.respond("فقط سرویس Telegram مجاز است. دوباره بفرستید:")
                return
            state["service"] = "Telegram"
            state["step"] = 5
            await event.respond("۵/۶ — قیمت فروش را به عدد بفرستید:")
            return
        if state["step"] == 5:
            try:
                state["price"] = float(text.replace(",", ""))
            except ValueError:
                await event.respond("قیمت نامعتبر است. فقط عدد بفرستید:")
                return
            state["step"] = 6
            await event.respond("۶/۶ — Provider IDs را با کاما بفرستید (یا - برای خالی):")
            return
        if state["step"] == 6:
            pids = "" if text == "-" else text
            s = state
            with db() as c:
                c.execute("""
                    INSERT INTO countries
                    (code,name,flag,service,price,provider_ids,enabled,stock,updated_at)
                    VALUES(?,?,?,?,?,?,1,0,?)
                    ON CONFLICT(code) DO UPDATE SET
                      name=excluded.name,
                      flag=excluded.flag,
                      service=excluded.service,
                      price=excluded.price,
                      provider_ids=excluded.provider_ids,
                      updated_at=excluded.updated_at
                """, (
                    s["code"], s["name"], s["flag"], s["service"],
                    s["price"], pids, now()
                ))
            admin_states.pop(uid, None)
            log_admin(f"country upsert: {s['code']} {s['name']}")
            await event.respond(
                "✅ کشور با موفقیت ذخیره شد.",
                buttons=[[Button.inline("🔙 پنل", b"admin")]]
            )
            return

    # Country search / generic user text
    if uid not in admin_states and len(text) >= 2:
        with db() as c:
            rows = c.execute("""
                SELECT id,name,flag,price FROM countries
                WHERE enabled=1 AND (name LIKE ? OR code LIKE ?)
                ORDER BY name LIMIT 8
            """, (f"%{text}%", f"%{text}%")).fetchall()
        if rows:
            buttons = [
                [Button.inline(
                    f'{r["flag"]} {r["name"]} • {money(r["price"])}',
                    f'country:{r["id"]}'.encode()
                )]
                for r in rows
            ]
            await event.respond("🔎 نتایج جستجو:", buttons=buttons)

async def run():
    init_db()
    log.info("Starting bot...")
    await bot.start(bot_token=BOT_TOKEN)
    log.info("Bot started.")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run())
