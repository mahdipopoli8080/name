import asyncio
import sqlite3
import time
import requests
from telethon import TelegramClient, events, Button

# ==================== تنظیمات اصلی ====================
API_ID = 8477522  # شناسه عددی API تلگرام شما (از my.telegram.org)
API_HASH = "366c19cf69e02cad530261ad81212a85"  # هش API تلگرام شما
BOT_TOKEN = "8763658652:AAHl9-VhKk0BwiXvWaDxmfSE03lHYgu8VA0"  # توکن دریافتی از BotFather

ADMIN_ID = 5190717598  # آیدی عددی تلگرام ادمین
SMSBOWER_API_KEY = "d7FVPDHaenCSNq05X1lzSlpQ6Ud30kff"  # کلید API سایت smsbower
SMSBOWER_BASE_URL = "https://smsbower.app/api/"

bot = TelegramClient("shop_bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# وضعیت موقت ادمین برای ثبت مرحله‌ای
admin_states = {}

# ==================== مدیریت دیتابیس ====================
def init_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,
            name TEXT,
            flag TEXT,
            provider_ids TEXT,
            price REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id TEXT,
            phone TEXT,
            country_name TEXT,
            price REAL,
            status TEXT DEFAULT 'WAITING',
            created_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("shop.db")

def get_or_create_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id, balance) VALUES (?, 0.0)", (user_id,))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

def update_user_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ==================== ارتباط با API سایت SMSBower ====================
def api_buy_number(country_code, provider_ids=""):
    params = {
        "page": "client",
        "action": "getNumber",
        "key": SMSBOWER_API_KEY,
        "service": "tg",
        "country": country_code
    }
    if provider_ids:
        params["provider"] = provider_ids
    try:
        res = requests.get(SMSBOWER_BASE_URL, params=params, timeout=15).text.strip()
        if res.startswith("ACCESS_NUMBER"):
            parts = res.split(":")
            return {"status": True, "order_id": parts[1], "phone": parts[2]}
        return {"status": False, "error": res}
    except Exception as e:
        return {"status": False, "error": str(e)}

def api_get_status(order_id):
    params = {
        "page": "client",
        "action": "getStatus",
        "key": SMSBOWER_API_KEY,
        "id": order_id
    }
    try:
        return requests.get(SMSBOWER_BASE_URL, params=params, timeout=15).text.strip()
    except Exception:
        return "ERROR"

def api_set_status(order_id, status_code):
    params = {
        "page": "client",
        "action": "setStatus",
        "key": SMSBOWER_API_KEY,
        "id": order_id,
        "status": status_code
    }
    try:
        return requests.get(SMSBOWER_BASE_URL, params=params, timeout=15).text.strip()
    except Exception:
        return "ERROR"

# ==================== کلیدهای شیشه‌ای ====================
def get_main_buttons(user_id):
    buttons = [
        [Button.inline("🛒 خرید شماره تلگرام", b"buy_tg"), Button.inline("👤 حساب کاربری", b"my_account")],
        [Button.inline("📋 سفارش‌های فعال", b"active_orders")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ پنل مدیریت", b"admin_panel")])
    return buttons

def get_admin_buttons():
    return [
        [Button.inline("➕ افزودن کشور", b"adm_add_c"), Button.inline("📋 لیست / حذف کشورها", b"adm_list_c")],
        [Button.inline("➕ افزایش موجودی", b"adm_add_b"), Button.inline("➖ کسر موجودی", b"adm_sub_b")],
        [Button.inline("🔙 بازگشت به منوی اصلی", b"back_main")]
    ]

# ==================== دستور Start ====================
@bot.on(events.NewMessage(pattern=r"^/start$"))
async def start_handler(event):
    user_id = event.sender_id
    user = await event.get_sender()
    first_name = user.first_name if user else "کاربر"
    bal = get_or_create_user(user_id)
    
    text = (
        f"👋 <b>سلام {first_name} خوش آمدید!</b>\n\n"
        f"💳 موجودی شما: <code>${bal:.2f}</code>\n"
        f"⚡ سرویس فعال: <b>تلگرام (Telegram)</b>\n\n"
        "جهت خرید یا مدیریت حساب، گزینه‌های زیر را انتخاب کنید:"
    )
    await event.respond(text, parse_mode="html", buttons=get_main_buttons(user_id))

# ==================== رویدادهای دکمه‌ها (Callback Queries) ====================
@bot.on(events.CallbackQuery)
async def callback_router(event):
    data = event.data.decode("utf-8")
    user_id = event.sender_id

    # منوی اصلی
    if data == "back_main":
        bal = get_or_create_user(user_id)
        text = (
            f"👋 <b>منوی اصلی</b>\n\n"
            f"💳 موجودی شما: <code>${bal:.2f}</code>\n"
            f"⚡ سرویس فعال: <b>تلگرام (Telegram)</b>"
        )
        await event.edit(text, parse_mode="html", buttons=get_main_buttons(user_id))

    # پروفایل حساب
    elif data == "my_account":
        bal = get_or_create_user(user_id)
        text = (
            f"👤 <b>حساب کاربری</b>\n\n"
            f"🆔 شناسه کاربری: <code>{user_id}</code>\n"
            f"💰 موجودی کیف‌پول: <code>${bal:.2f}</code>\n\n"
            "جهت شارژ حساب با ادمین در ارتباط باشید."
        )
        await event.edit(text, parse_mode="html", buttons=[[Button.inline("🔙 بازگشت", b"back_main")]])

    # لیست کشورهای خرید
    elif data == "buy_tg":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, flag, price FROM countries ORDER BY id ASC")
        countries = cur.fetchall()
        conn.close()

        if not countries:
            await event.answer("❌ در حال حاضر کشوری تعریف نشده است.", alert=True)
            return

        buttons = []
        for cid, name, flag, price in countries:
            buttons.append([Button.inline(f"{flag} {name} (${price:.2f})", f"buy_c_{cid}".encode())])
        buttons.append([Button.inline("🔙 منوی اصلی", b"back_main")])

        await event.edit("🌍 <b>کشور مورد نظر را انتخاب کنید:</b>", parse_mode="html", buttons=buttons)

    # تایید و استعلام خرید شماره
    elif data.startswith("buy_c_"):
        country_id = data.split("_")[2]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT country_code, name, flag, provider_ids, price FROM countries WHERE id = ?", (country_id,))
        c_row = cur.fetchone()
        
        if not c_row:
            conn.close()
            await event.answer("کشور یافت نشد.", alert=True)
            return

        c_code, name, flag, provider_ids, price = c_row
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = cur.fetchone()[0]
        conn.close()

        if bal < price:
            await event.answer(f"❌ موجودی ناکافی است!\nقیمت: ${price:.2f}\nموجودی: ${bal:.2f}", alert=True)
            return

        await event.answer("⏳ در حال سفارش شماره...")
        res = api_buy_number(c_code, provider_ids)
        
        if not res["status"]:
            await event.respond(f"❌ خطا در دریافت شماره از سایت:\n<code>{res.get('error', 'Unknown')}</code>", parse_mode="html")
            return

        order_id = res["order_id"]
        phone = res["phone"]

        update_user_balance(user_id, -price)
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders (user_id, order_id, phone, country_name, price, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'WAITING', ?)
        """, (user_id, order_id, phone, name, price, int(time.time())))
        conn.commit()
        conn.close()

        buttons = [
            [Button.inline("🔄 دریافت کد SMS", f"chk_sms_{order_id}".encode()), Button.inline("❌ لغو سفارش", f"cnc_ord_{order_id}".encode())],
            [Button.inline("🔙 منوی اصلی", b"back_main")]
        ]
        text = (
            f"✅ <b>شماره با موفقیت دریافت شد!</b>\n\n"
            f"🏴 کشور: {flag} {name}\n"
            f"📱 شماره: <code>+{phone}</code>\n"
            f"💵 قیمت: <code>${price:.2f}</code>\n"
            f"🆔 کد سفارش: <code>{order_id}</code>\n\n"
            "شماره را در تلگرام وارد کرده و پس از ارسال پیامک، دکمه <b>«دریافت کد SMS»</b> را بزنید."
        )
        await event.edit(text, parse_mode="html", buttons=buttons)

    # بررسی پیامک فعال‌سازی
    elif data.startswith("chk_sms_"):
        order_id = data.split("_")[2]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status, phone FROM orders WHERE order_id = ?", (order_id,))
        order = cur.fetchone()
        conn.close()

        if not order:
            await event.answer("سفارش یافت نشد.", alert=True)
            return

        status = api_get_status(order_id)
        if status.startswith("STATUS_OK"):
            sms_code = status.split(":")[1]
            api_set_status(order_id, 6)
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
            conn.commit()
            conn.close()

            await event.respond(
                f"🎉 <b>کد تایید تلگرام دریافت شد:</b>\n\n"
                f"📱 شماره: <code>+{order[1]}</code>\n"
                f"🔑 کد ورود: <code>{sms_code}</code>",
                parse_mode="html"
            )
            await event.answer("کد دریافت شد!")
        elif status == "STATUS_WAIT_CODE":
            await event.answer("⏳ هنوز کدی دریافت نشده است.", alert=True)
        elif status == "STATUS_CANCEL":
            await event.answer("این سفارش لغو یا منقضی شده است.", alert=True)
        else:
            await event.answer(f"وضعیت: {status}", alert=True)

    # لغو سفارش و برگشت وجه
    elif data.startswith("cnc_ord_"):
        order_id = data.split("_")[2]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT price, status FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        order = cur.fetchone()

        if not order or order[1] != "WAITING":
            conn.close()
            await event.answer("امکان لغو این سفارش وجود ندارد.", alert=True)
            return

        price = order[0]
        res = api_set_status(order_id, 8)
        if res in ["ACCESS_CANCEL", "ACCESS_READY"]:
            cur.execute("UPDATE orders SET status = 'CANCELLED' WHERE order_id = ?", (order_id,))
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, user_id))
            conn.commit()
            conn.close()
            await event.answer(f"✅ سفارش لغو شد و ${price:.2f} به حساب بازگشت.", alert=True)
            bal = get_or_create_user(user_id)
            await event.edit(f"👋 منوی اصلی\n💳 موجودی: <code>${bal:.2f}</code>", parse_mode="html", buttons=get_main_buttons(user_id))
        else:
            conn.close()
            await event.answer(f"❌ عدم امکان لغو: {res}", alert=True)

    # لیست سفارش‌های فعال
    elif data == "active_orders":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT order_id, phone, country_name FROM orders WHERE user_id = ? AND status = 'WAITING'", (user_id,))
        orders = cur.fetchall()
        conn.close()

        if not orders:
            await event.answer("هیچ سفارش فعالی ندارید.", alert=True)
            return

        buttons = []
        for oid, phone, cname in orders:
            buttons.append([Button.inline(f"📱 +{phone} ({cname})", f"chk_sms_{oid}".encode())])
            buttons.append([Button.inline(f"❌ لغو {oid}", f"cnc_ord_{oid}".encode())])
        buttons.append([Button.inline("🔙 منوی اصلی", b"back_main")])
        await event.edit("📋 <b>سفارش‌های فعال:</b>", parse_mode="html", buttons=buttons)

    # ==================== بخش ادمین ====================
    elif data == "admin_panel" and user_id == ADMIN_ID:
        await event.edit("⚙️ <b>پنل مدیریت ربات:</b>", parse_mode="html", buttons=get_admin_buttons())

    elif data == "adm_add_c" and user_id == ADMIN_ID:
        admin_states[user_id] = {"step": 1, "data": {}}
        await event.respond("<b>Step 1:</b> کد کشور را ارسال کنید:\n(مثال: <code>0</code> برای روسیه، <code>7</code> برای آمریکا)", parse_mode="html")
        await event.answer()

    elif data == "adm_list_c" and user_id == ADMIN_ID:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, flag, country_code, price FROM countries")
        rows = cur.fetchall()
        conn.close()

        if not rows:
            await event.answer("کشوری ثبت نشده است.", alert=True)
            return

        buttons = []
        for cid, name, flag, code, price in rows:
            buttons.append([Button.inline(f"🗑 حذف {flag} {name} (کد {code}) - ${price:.2f}", f"del_c_{cid}".encode())])
        buttons.append([Button.inline("🔙 بازگشت به پنل", b"admin_panel")])
        await event.edit("جهت حذف، روی کشور مورد نظر بزنید:", buttons=buttons)

    elif data.startswith("del_c_") and user_id == ADMIN_ID:
        cid = data.split("_")[2]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM countries WHERE id = ?", (cid,))
        conn.commit()
        conn.close()
        await event.answer("کشور حذف شد.")
        # بازخوانی منو
        await callback_router(event)

    elif data in ["adm_add_b", "adm_sub_b"] and user_id == ADMIN_ID:
        is_add = (data == "adm_add_b")
        action = "افزایش" if is_add else "کسر"
        admin_states[user_id] = {"step": "balance", "is_add": is_add}
        await event.respond(f"جهت <b>{action} موجودی</b> پیام را ارسال کنید:\n<code>آیدی_کاربر مبلغ</code>\nمثال: <code>123456789 2.5</code>", parse_mode="html")
        await event.answer()

# ==================== دریافت ورودی‌های متنی ادمین ====================
@bot.on(events.NewMessage)
async def message_input_handler(event):
    user_id = event.sender_id
    if user_id != ADMIN_ID or user_id not in admin_states:
        return

    text = event.raw_text.strip()
    state = admin_states[user_id]
    step = state.get("step")

    # مراحل ثبت کشور
    if step == 1:
        state["data"]["code"] = text
        state["step"] = 2
        await event.respond("<b>Step 2:</b> نام کشور را ارسال کنید:\n(مثال: <code>Russia</code>)", parse_mode="html")

    elif step == 2:
        state["data"]["name"] = text
        state["step"] = 3
        await event.respond("<b>Step 3:</b> ایموجی پرچم را ارسال کنید:\n(مثال: 🇷🇺)", parse_mode="html")

    elif step == 3:
        state["data"]["flag"] = text
        state["step"] = 4
        await event.respond("<b>Step 4:</b> شناسه ارائه‌دهنده (Provider IDs) را وارد کنید:\n(در صورت عدم نیاز <code>0</code> ارسال کنید)", parse_mode="html")

    elif step == 4:
        state["data"]["provider"] = "" if text == "0" else text
        state["step"] = 5
        await event.respond("<b>Step 5:</b> قیمت فروش دلاری را ارسال کنید:\n(مثال: <code>0.50</code>)", parse_mode="html")

    elif step == 5:
        try:
            price = float(text)
            d = state["data"]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO countries (country_code, name, flag, provider_ids, price)
                VALUES (?, ?, ?, ?, ?)
            """, (d["code"], d["name"], d["flag"], d["provider"], price))
            conn.commit()
            conn.close()

            del admin_states[user_id]
            await event.respond(
                f"✅ <b>کشور ثبت شد:</b>\n{d['flag']} {d['name']} | کد: <code>{d['code']}</code> | قیمت: <code>${price:.2f}</code>",
                parse_mode="html",
                buttons=get_admin_buttons()
            )
        except ValueError:
            await event.respond("❌ فرمت قیمت نامعتبر است. عدد دلاری ارسال کنید:")

    # شارژ / کسر موجودی
    elif step == "balance":
        try:
            parts = text.split()
            target_uid = int(parts[0])
            amount = float(parts[1])
            is_add = state["is_add"]
            if not is_add:
                amount = -amount

            get_or_create_user(target_uid)
            update_user_balance(target_uid, amount)
            del admin_states[user_id]

            await event.respond(f"✅ موجودی کاربر <code>{target_uid}</code> به‌روز شد.", parse_mode="html", buttons=get_admin_buttons())
            try:
                sign = "+" if is_add else "-"
                await bot.send_message(target_uid, f"💳 حساب شما به مقدار <code>{sign}${abs(amount):.2f}</code> شارژ/تغییر یافت.", parse_mode="html")
            except Exception:
                pass
        except Exception:
            await event.respond("❌ فرمت نامعتبر است. مثال: <code>123456789 2.5</code>", parse_mode="html")

# ==================== اجرای ربات ====================
if __name__ == "__main__":
    print("Bot is running with Telethon...")
    bot.run_until_disconnected()
