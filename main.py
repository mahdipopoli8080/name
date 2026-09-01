import sqlite3
import time
import requests
import telebot
from telebot import types

# ==================== تنظیمات اصلی ====================
BOT_TOKEN = "8766659658:AAGjRIsXi_4wzsa9P5ua6Izk6CTvDNK_OeY"  # توکن ربات تلگرام
ADMIN_ID = 5190717598  # آیدی عددی تلگرام ادمین اصلی
SMSBOWER_API_KEY = "d7FVPDHaenCSNq05X1lzSlpQ6Ud30kff"  # کلید API سایت smsbower
SMSBOWER_BASE_URL = "https://smsbower.app/api/"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== مدیریت دیتابیس ====================
def init_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    # جدول کاربران
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    """)
    # جدول کشورها
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
    # جدول سفارش‌ها
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

# ==================== توابع API سایت SMSBower ====================
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
        # نمونه پاسخ موفق: ACCESS_NUMBER:123456:79991234567
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
        res = requests.get(SMSBOWER_BASE_URL, params=params, timeout=15).text.strip()
        # STATUS_WAIT_CODE, STATUS_OK:12345, STATUS_CANCEL
        return res
    except Exception:
        return "ERROR"

def api_set_status(order_id, status_code):
    """
    status_code: 8 (کنسل / لغو), 6 (تکمیل فعال‌سازی)
    """
    params = {
        "page": "client",
        "action": "setStatus",
        "key": SMSBOWER_API_KEY,
        "id": order_id,
        "status": status_code
    }
    try:
        res = requests.get(SMSBOWER_BASE_URL, params=params, timeout=15).text.strip()
        return res
    except Exception:
        return "ERROR"

# ==================== کیبوردهای شیشه‌ای ====================
def main_menu_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🛒 خرید شماره تلگرام", callback_data="buy_tg"),
        types.InlineKeyboardButton("👤 حساب کاربری", callback_data="my_account")
    )
    kb.add(types.InlineKeyboardButton("📋 سفارش‌های فعال", callback_data="active_orders"))
    if user_id == ADMIN_ID:
        kb.add(types.InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="admin_panel"))
    return kb

def admin_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ افزودن کشور", callback_data="admin_add_country"),
        types.InlineKeyboardButton("📋 لیست / حذف کشورها", callback_data="admin_list_countries")
    )
    kb.add(
        types.InlineKeyboardButton("➕ افزایش موجودی", callback_data="admin_add_bal"),
        types.InlineKeyboardButton("➖ کسر موجودی", callback_data="admin_sub_bal")
    )
    kb.add(types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main"))
    return kb

# ==================== هندلر استارت ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    bal = get_or_create_user(user_id)
    text = (
        f"👋 <b>سلام {message.from_user.first_name} خوش آمدید!</b>\n\n"
        f"💳 موجودی شما: <code>${bal:.2f}</code>\n"
        f"⚡ سرویس فعال: <b>تلگرام (Telegram)</b>\n\n"
        "جهت خرید شماره یا مدیریت حساب از دکمه‌های زیر استفاده کنید:"
    )
    bot.send_message(user_id, text, reply_markup=main_menu_keyboard(user_id))

# ==================== بخش خرید کاربر ====================
@bot.callback_query_handler(func=lambda call: call.data == "buy_tg")
def handle_buy_tg(call):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, country_code, name, flag, price FROM countries ORDER BY id ASC")
    countries = cur.fetchall()
    conn.close()

    if not countries:
        bot.answer_callback_query(call.id, "❌ در حال حاضر کشوری برای خرید موجود نیست.", show_alert=True)
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for cid, c_code, name, flag, price in countries:
        btn_text = f"{flag} {name} (${price:.2f})"
        kb.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_c_{cid}"))
    kb.add(types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main"))

    bot.edit_message_text(
        "🌍 <b>کشور مورد نظر خود را جهت خرید شماره تلگرام انتخاب کنید:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_c_"))
def handle_confirm_buy(call):
    country_db_id = call.data.split("_")[2]
    user_id = call.from_user.id
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT country_code, name, flag, provider_ids, price FROM countries WHERE id = ?", (country_db_id,))
    country = cur.fetchone()
    if not country:
        conn.close()
        bot.answer_callback_query(call.id, "کشور نامعتبر است.")
        return

    c_code, name, flag, provider_ids, price = country
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cur.fetchone()[0]
    conn.close()

    if balance < price:
        bot.answer_callback_query(call.id, f"❌ موجودی ناکافی است!\nقیمت: ${price:.2f}\nموجودی: ${balance:.2f}", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ در حال دریافت شماره از سرور...")
    res = api_buy_number(c_code, provider_ids)
    
    if not res["status"]:
        bot.send_message(user_id, f"❌ خطا در دریافت شماره:\n<code>{res.get('error', 'Unknown')}</code>")
        return

    order_id = res["order_id"]
    phone = res["phone"]

    # کسر موجودی و ثبت سفارش
    update_user_balance(user_id, -price)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, order_id, phone, country_name, price, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'WAITING', ?)
    """, (user_id, order_id, phone, name, price, int(time.time())))
    conn.commit()
    conn.close()

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔄 دریافت کد SMS", callback_data=f"check_sms_{order_id}"),
        types.InlineKeyboardButton("❌ لغو سفارش", callback_data=f"cancel_ord_{order_id}")
    )
    kb.add(types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main"))

    text = (
        f"✅ <b>شماره با موفقیت تحویل داده شد!</b>\n\n"
        f"🏴 کشور: {flag} {name}\n"
        f"📱 شماره: <code>+{phone}</code>\n"
        f"💵 مبلغ: <code>${price:.2f}</code>\n"
        f"🆔 شناسه سفارش: <code>{order_id}</code>\n\n"
        "⚠️ شماره را در تلگرام وارد کنید و پس از ارسال پیامک، دکمه <b>«دریافت کد SMS»</b> را بزنید."
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

# ==================== بررسی وضعیت و لغو سفارش ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_sms_"))
def handle_check_sms(call):
    order_id = call.data.split("_")[2]
    user_id = call.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status, phone FROM orders WHERE order_id = ?", (order_id,))
    order = cur.fetchone()
    conn.close()

    if not order:
        bot.answer_callback_query(call.id, "سفارش پیدا نشد.")
        return

    status = api_get_status(order_id)

    if status.startswith("STATUS_OK"):
        sms_code = status.split(":")[1]
        api_set_status(order_id, 6)  # تایید نهایی
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()

        bot.send_message(
            user_id,
            f"🎉 <b>کد تایید تلگرام دریافت شد:</b>\n\n"
            f"📱 شماره: <code>+{order[1]}</code>\n"
            f"🔑 کد تایید: <code>{sms_code}</code>"
        )
        bot.answer_callback_query(call.id, "کد دریافت شد!")
    elif status == "STATUS_WAIT_CODE":
        bot.answer_callback_query(call.id, "⏳ هنوز کدی دریافت نشده است. چند لحظه بعد تلاش کنید.", show_alert=True)
    elif status == "STATUS_CANCEL":
        bot.answer_callback_query(call.id, "این سفارش منقضی یا لغو شده است.", show_alert=True)
    else:
        bot.answer_callback_query(call.id, f"وضعیت: {status}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_ord_"))
def handle_cancel_order(call):
    order_id = call.data.split("_")[2]
    user_id = call.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT price, status FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id))
    order = cur.fetchone()

    if not order or order[1] != "WAITING":
        conn.close()
        bot.answer_callback_query(call.id, "امکان لغو این سفارش وجود ندارد.", show_alert=True)
        return

    price = order[0]
    api_res = api_set_status(order_id, 8)  # درخواست لغو از سرور

    if api_res in ["ACCESS_CANCEL", "ACCESS_READY"]:
        cur.execute("UPDATE orders SET status = 'CANCELLED' WHERE order_id = ?", (order_id,))
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, user_id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"✅ سفارش لغو شد و مبلغ ${price:.2f} بازگشت داده شد.", show_alert=True)
        cmd_start(call.message)
    else:
        conn.close()
        bot.answer_callback_query(call.id, f"❌ امکان لغو وجود ندارد: {api_res}", show_alert=True)

# ==================== اطلاعات حساب و سفارش‌های فعال ====================
@bot.callback_query_handler(func=lambda call: call.data == "my_account")
def handle_my_account(call):
    user_id = call.from_user.id
    bal = get_or_create_user(user_id)
    text = (
        f"👤 <b>حساب کاربری</b>\n\n"
        f"🆔 شناسه: <code>{user_id}</code>\n"
        f"💰 موجودی: <code>${bal:.2f}</code>\n\n"
        "جهت افزایش موجودی با پشتیبانی/ادمین در ارتباط باشید."
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "active_orders")
def handle_active_orders(call):
    user_id = call.from_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT order_id, phone, country_name, price FROM orders WHERE user_id = ? AND status = 'WAITING'", (user_id,))
    orders = cur.fetchall()
    conn.close()

    if not orders:
        bot.answer_callback_query(call.id, "هیچ سفارش فعالی ندارید.", show_alert=True)
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for oid, phone, cname, price in orders:
        kb.add(
            types.InlineKeyboardButton(f"📱 +{phone} ({cname})", callback_data=f"check_sms_{oid}"),
            types.InlineKeyboardButton(f"❌ لغو سفارش {oid}", callback_data=f"cancel_ord_{oid}")
        )
    kb.add(types.InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_main"))

    bot.edit_message_text("📋 <b>سفارش‌های فعال شما:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back_to_main(call):
    user_id = call.from_user.id
    bal = get_or_create_user(user_id)
    text = (
        f"👋 <b>منوی اصلی</b>\n\n"
        f"💳 موجودی شما: <code>${bal:.2f}</code>\n"
        f"⚡ سرویس فعال: <b>تلگرام (Telegram)</b>"
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_keyboard(user_id))

# ==================== پنل ادمین ====================
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def handle_admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.edit_message_text("⚙️ <b>پنل مدیریت ربات:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=admin_menu_keyboard())

# --- مراحل افزودن گام‌به‌گام کشور ---
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_country")
def admin_start_add_country(call):
    if call.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(call.message.chat.id, "<b>Step 1:</b> لطفاً کد کشور را در API وارد کنید:\n(مثال: <code>0</code> برای روسیه، <code>7</code> برای آمریکا)")
    bot.register_next_step_handler(msg, process_step_country_code)

def process_step_country_code(message):
    code = message.text.strip()
    data = {"code": code}
    msg = bot.send_message(message.chat.id, "<b>Step 2:</b> نام کشور را به انگلیسی یا فارسی وارد کنید:\n(مثال: <code>Russia</code> یا <code>روسیه</code>)")
    bot.register_next_step_handler(msg, process_step_country_name, data)

def process_step_country_name(message, data):
    data["name"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "<b>Step 3:</b> ایموجی پرچم کشور را ارسال کنید:\n(مثال: 🇷🇺)")
    bot.register_next_step_handler(msg, process_step_country_flag, data)

def process_step_country_flag(message, data):
    data["flag"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "<b>Step 4:</b> شناسه ارائه‌دهنده (Provider IDs) را وارد کنید:\n(اگر مهم نیست <code>0</code> یا خالی بگذارید)")
    bot.register_next_step_handler(msg, process_step_country_provider, data)

def process_step_country_provider(message, data):
    prov = message.text.strip()
    data["provider_ids"] = "" if prov == "0" else prov
    msg = bot.send_message(message.chat.id, "<b>Step 5:</b> قیمت فروش دلاری را وارد کنید:\n(مثال: <code>0.50</code>)")
    bot.register_next_step_handler(msg, process_step_country_price, data)

def process_step_country_price(message, data):
    try:
        price = float(message.text.strip())
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO countries (country_code, name, flag, provider_ids, price)
            VALUES (?, ?, ?, ?, ?)
        """, (data["code"], data["name"], data["flag"], data["provider_ids"], price))
        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ <b>کشور با موفقیت ثبت شد!</b>\n\n"
            f"🌍 کشور: {data['flag']} {data['name']}\n"
            f"🔢 کد API: <code>{data['code']}</code>\n"
            f"💵 قیمت فروش: <code>${price:.2f}</code>",
            reply_markup=admin_menu_keyboard()
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ فرمت قیمت نامعتبر بود. لطفاً دوباره تلاش کنید.", reply_markup=admin_menu_keyboard())

# --- مدیریت لیست و حذف کشورها ---
@bot.callback_query_handler(func=lambda call: call.data == "admin_list_countries")
def admin_list_countries(call):
    if call.from_user.id != ADMIN_ID:
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, flag, country_code, price FROM countries")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        bot.answer_callback_query(call.id, "هیچ کشوری تعریف نشده است.", show_alert=True)
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for cid, name, flag, code, price in rows:
        kb.add(types.InlineKeyboardButton(f"🗑 حذف {flag} {name} (کد {code}) - ${price:.2f}", callback_data=f"del_c_{cid}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel"))

    bot.edit_message_text("برای حذف، روی کشور مورد نظر کلیک کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_c_"))
def admin_delete_country(call):
    if call.from_user.id != ADMIN_ID:
        return
    cid = call.data.split("_")[2]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM countries WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "کشور با موفقیت حذف شد.")
    admin_list_countries(call)

# --- افزایش و کسر موجودی کاربر توسط ادمین ---
@bot.callback_query_handler(func=lambda call: call.data in ["admin_add_bal", "admin_sub_bal"])
def admin_balance_change(call):
    if call.from_user.id != ADMIN_ID:
        return
    action = "افزایش" if call.data == "admin_add_bal" else "کسر"
    is_add = (call.data == "admin_add_bal")
    msg = bot.send_message(
        call.message.chat.id,
        f"جهت <b>{action} موجودی</b>، اطلاعات را با فرمت زیر ارسال کنید:\n\n"
        f"<code>آیدی_کاربر مبلغ_دلاری</code>\n"
        f"مثال: <code>123456789 2.5</code>"
    )
    bot.register_next_step_handler(msg, process_balance_update, is_add)

def process_balance_update(message, is_add):
    try:
        parts = message.text.strip().split()
        target_uid = int(parts[0])
        amount = float(parts[1])
        if not is_add:
            amount = -amount

        get_or_create_user(target_uid)
        update_user_balance(target_uid, amount)

        # اطلاع به ادمین و کاربر
        bot.send_message(message.chat.id, f"✅ موجودی کاربر <code>{target_uid}</code> با موفقیت به‌روزرسانی شد.", reply_markup=admin_menu_keyboard())
        try:
            sign = "+" if is_add else "-"
            bot.send_message(target_uid, f"💳 حساب شما به مقدار <code>{sign}${abs(amount):.2f}</code> شارژ/تغییر یافت.")
        except Exception:
            pass
    except Exception:
        bot.send_message(message.chat.id, "❌ ورودی نامعتبر است. فرمت صحیح: <code>آیدی مبلغ</code>", reply_markup=admin_menu_keyboard())

# ==================== اجرای ربات ====================
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
  
