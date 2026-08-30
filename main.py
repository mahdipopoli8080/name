import asyncio
import sqlite3
import json
import aiohttp
from telethon import TelegramClient, events, Button

# ==================== CONFIGURATION ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek'

SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_ENDPOINT = 'https://smsbower.app/stubs/handler_api.php'

ADMIN_ID = 5190717598
SERVICE_MARGIN_PERCENT = 0
# =======================================================

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            country_code TEXT NOT NULL,
            country_name TEXT NOT NULL,
            flag TEXT NOT NULL,
            api_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            UNIQUE(service, country_code)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL
        )
    ''')
    # Default services
    default_services = [
        ('tg', 'تلگرام', '🔹'),
        ('wa', 'واتساپ', '🔹'),
        ('ig', 'اینستاگرام', '🔹'),
        ('go', 'گوگل', '🔹'),
        ('fb', 'فیسبوک', '🔹'),
        ('tw', 'توییتر', '🔹'),
        ('vi', 'وی‌چت', '🔹'),
    ]
    for code, name, icon in default_services:
        cursor.execute('INSERT OR IGNORE INTO services (code, name, icon) VALUES (?, ?, ?)', (code, name, icon))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, 0.0)', (user_id,))
        conn.commit()
        conn.close()
        return 0.0
    conn.close()
    return row[0]

def update_balance(user_id, amount):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_all_countries(service):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT country_code, country_name, flag, api_price, sell_price FROM countries WHERE service = ?', (service,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_services():
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code, name, icon FROM services')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_country(service, country_code, country_name, flag, api_price, sell_price):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO countries (service, country_code, country_name, flag, api_price, sell_price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (service, country_code, country_name, flag, api_price, sell_price))
    conn.commit()
    conn.close()

def remove_country(service, country_code):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM countries WHERE service = ? AND country_code = ?', (service, country_code))
    conn.commit()
    conn.close()

def get_country_info(service, country_code):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT country_name, flag, api_price, sell_price FROM countries WHERE service = ? AND country_code = ?', (service, country_code))
    row = cursor.fetchone()
    conn.close()
    return row

def add_service(code, name, icon):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO services (code, name, icon) VALUES (?, ?, ?)', (code, name, icon))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, balance FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()

client = TelegramClient('smsbower_bot_session', API_ID, API_HASH)

# State tracking
user_state = {}

# API Request Helper
async def call_smsbower(action, **params):
    base_params = {'api_key': SMSBOWER_API_KEY, 'action': action}
    base_params.update(params)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SMSBOWER_ENDPOINT, params=base_params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                return await resp.text()
    except Exception as e:
        return f"ERROR:{e}"

pending_receipts = {}

# ==================== USER HANDLERS ====================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    bal = get_balance(user_id)
    text = (
        f"👋 **به ربات خرید شماره مجازی خوش آمدید!**\n\n"
        f"🆔 شناسه شما: `{user_id}`\n"
        f"💰 موجودی کیف‌پول: **{bal:.2f} $**\n\n"
        f"از منوی زیر استفاده کنید:"
    )
    buttons = [
        [Button.inline("📱 خرید شماره مجازی", b"buy_menu")],
        [Button.inline("💳 شارژ حساب", b"deposit_manual"), Button.inline("👤 حساب کاربری", b"profile")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ پنل ادمین", b"admin_panel")])
    await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"profile"))
async def profile_handler(event):
    user_id = event.sender_id
    bal = get_balance(user_id)
    text = f"👤 **پروفایل کاربری**\n\n🆔 شناسه کاربری: `{user_id}`\n💰 موجودی: **{bal:.2f} $**"
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"back_main")]])

@client.on(events.CallbackQuery(data=b"buy_menu"))
async def buy_menu(event):
    services = get_all_services()
    buttons = []
    row = []
    for code, name, icon in services:
        row.append(Button.inline(f"{icon} {name}", f"service:{code}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([Button.inline("🔙 بازگشت", b"back_main")])
    await event.edit("📱 **لطفاً سرویس مورد نظر خود را انتخاب کنید:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"service:")))
async def select_country(event):
    service_code = event.data.decode().split(':')[1]
    countries = get_all_countries(service_code)

    if not countries:
        await event.edit(
            f"⚠️ هنوز کشوری برای سرویس `{service_code.upper()}` اضافه نشده است.\n\n"
            f"از ادمین بخواهید کشور اضافه کند.",
            buttons=[[Button.inline("🔙 بازگشت", b"buy_menu")]]
        )
        return

    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        btn_data = f"buy:{service_code}:{c_code}:{int(sell_price)}".encode()
        buttons.append([Button.inline(f"{flag} {c_name} - {sell_price:.2f} $", btn_data)])

    buttons.append([Button.inline("🔙 بازگشت", b"buy_menu")])
    await event.edit(f"🌐 **کشور مورد نظر را برای ({service_code.upper()}) انتخاب کنید:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"buy:")))
async def process_buy(event):
    _, service, country, price = event.data.decode().split(':')
    price = float(price)
    user_id = event.sender_id

    bal = get_balance(user_id)
    if bal < price:
        await event.answer("❌ موجودی کافی نیست!", alert=True)
        return

    await event.edit("⏳ **در حال دریافت شماره...**")

    res = await call_smsbower('getNumber', service=service, country=country)

    if 'ACCESS_NUMBER' in res:
        parts = res.split(':')
        order_id = parts[1]
        phone_number = parts[2]
        update_balance(user_id, -price)

        country_info = get_country_info(service, country)
        flag = country_info[1] if country_info else "📱"

        buttons = [
            [Button.inline("📩 دریافت کد پیامک", f"get_sms:{order_id}".encode())],
            [Button.inline("❌ لغو سفارش", f"cancel_order:{order_id}:{price}".encode())]
        ]
        text = (
            f"✅ **شماره تحویل داده شد!**\n\n"
            f"{flag} شماره: `+{phone_number}`\n"
            f"🆔 سفارش: `{order_id}`\n\n"
            f"کد رو وارد کن و دکمه **دریافت کد** رو بزن."
        )
        await event.edit(text, buttons=buttons)
    else:
        await event.edit(
            f"⚠️ شماره‌ای موجود نیست.",
            buttons=[
                [Button.inline("🔄 تلاش مجدد", f"buy:{service}:{country}:{int(price)}".encode())],
                [Button.inline("🔙 بازگشت", b"buy_menu")]
            ]
        )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"get_sms:")))
async def check_sms(event):
    order_id = event.data.decode().split(':')[1]
    res = await call_smsbower('getStatus', id=order_id)

    if 'STATUS_OK' in res:
        sms_code = res.split(':')[1]
        await call_smsbower('setStatus', id=order_id, status='6')
        await event.edit(
            f"📩 **کد تایید!**\n\n"
            f"🔑 کد: `{sms_code}`\n\n"
            f"✅ تمام شد."
        )
    elif 'STATUS_WAIT_CODE' in res:
        await event.answer("⏳ هنوز پیامک نیومده...", alert=True)
    elif 'STATUS_CANCEL' in res:
        await event.answer("❌ سفارش لغو شده.", alert=True)
    else:
        await event.answer(f"{res}", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cancel_order:")))
async def cancel_order(event):
    _, order_id, price = event.data.decode().split(':')
    price = float(price)
    user_id = event.sender_id
    res = await call_smsbower('setStatus', id=order_id, status='8')

    if 'ACCESS_CANCEL' in res or 'ACCESS_OK' in res:
        update_balance(user_id, price)
        await event.edit("✅ **لغو شد. مبلغ برگشت.**")
    else:
        await event.answer("❌ امکان لغو نیست.", alert=True)

# ==================== DEPOSIT ====================

@client.on(events.CallbackQuery(data=b"deposit_manual"))
async def deposit_manual(event):
    pending_receipts[event.sender_id] = True
    await event.edit(
        "💳 **کارت به کارت**\n\n"
        "💳 شماره کارت: `6037-0000-0000-0000`\n"
        "👤 به نام: مدیر سیستم\n\n"
        "📌 فیش رو همینجا بفرست.",
        buttons=[[Button.inline("❌ انصراف", b"back_main")]]
    )

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and e.is_private))
async def receipt_handler(event):
    user_id = event.sender_id
    if user_id in pending_receipts:
        del pending_receipts[user_id]
        if event.photo or event.document:
            await event.forward_to(ADMIN_ID)
        else:
            await client.send_message(ADMIN_ID, f"📝 از `{user_id}`:\n\n{event.text}")

        btn = [
            [Button.inline("✅ 50$", f"approve:{user_id}:50".encode()),
             Button.inline("✅ 100$", f"approve:{user_id}:100".encode())],
            [Button.inline("❌ رد", f"reject:{user_id}".encode())]
        ]
        await client.send_message(ADMIN_ID, f"📥 **فیش جدید** | 👤 `{user_id}`", buttons=btn)
        await event.respond("✅ فیش ارسال شد. منتظر تایید ادمین.")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"approve:")))
async def approve(event):
    if event.sender_id != ADMIN_ID:
        return
    _, u_id, amt = event.data.decode().split(':')
    u_id, amt = int(u_id), float(amt)
    update_balance(u_id, amt)
    await client.send_message(u_id, f"✅ **شارژ!** {amt:.2f} $ اضافه شد.")
    await event.edit(f"✅ `{u_id}` تایید شد | {amt:.2f} $")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"reject:")))
async def reject(event):
    if event.sender_id != ADMIN_ID:
        return
    u_id = int(event.data.decode().split(':')[1])
    await client.send_message(u_id, "❌ **فیش رد شد.**")
    await event.edit(f"❌ `{u_id}` رد شد")

@client.on(events.CallbackQuery(data=b"back_main"))
async def back_main(event):
    await start_handler(event)

# ==================== ADMIN PANEL ====================

@client.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    services = get_all_services()
    total_users = len(users)
    total_balance = sum(b for _, b in users)

    text = (
        f"⚙️ **پنل ادمین**\n"
        f"────────────────\n"
        f"👥 کاربران: {total_users}\n"
        f"💰 کل موجودی: {total_balance:.2f} $\n"
        f"📱 سرویس‌ها: {len(services)}"
    )
    buttons = [
        [Button.inline("🌍 مدیریت کشورها", b"admin_countries"), Button.inline("📱 مدیریت سرویس‌ها", b"admin_services")],
        [Button.inline("🌐 دریافت قیمت از API", b"admin_fetch_api")],
        [Button.inline("👥 لیست کاربران", b"admin_users")],
        [Button.inline("📊 آمار کامل", b"admin_stats")],
        [Button.inline("🔙 بازگشت", b"back_main")]
    ]
    await event.edit(text, buttons=buttons)

# --- Fetch API Prices ---
@client.on(events.CallbackQuery(data=b"admin_fetch_api"))
async def admin_fetch_api(event):
    if event.sender_id != ADMIN_ID:
        return
    await event.edit("⏳ **در حال دریافت قیمت‌ها از API...**")

    services = get_all_services()
    all_text = ""
    count = 0

    for code, name, icon in services:
        res = await call_smsbower('getPrices', service=code)
        if 'ACCESSPrices' in res:
            # Parse: ACCESSPrices:CODE:COUNTRY:PRICE,...
            parts = res.split(':')
            if len(parts) > 1:
                country_data = parts[1]
                items = country_data.split(',')
                text_lines = []
                for item in items:
                    parts2 = item.split('-')
                    if len(parts2) == 2:
                        c_id, c_price = parts2
                        count += 1
                        text_lines.append(f"  {c_id}: {c_price}")
                all_text += f"\n**{name} ({code}):**\n" + "\n".join(text_lines) + "\n"

    if all_text:
        # Split if too long
        header = f"📊 **قیمت‌های SMSBower** ({count} مورد)\n────────────────\n"
        full = header + all_text
        if len(full) > 4000:
            full = full[:4000] + "\n..."
        await event.edit(full, buttons=[
            [Button.inline("➕ اضافه کشور از API", b"admin_add_from_api")],
            [Button.inline("🔙 بازگشت", b"admin_panel")]
        ])
    else:
        await event.edit("❌ خطا در دریافت قیمت‌ها", buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

# --- Add Country from API ---
@client.on(events.CallbackQuery(data=b"admin_add_from_api"))
async def admin_add_from_api(event):
    if event.sender_id != ADMIN_ID:
        return
    user_state[event.sender_id] = "admin_add_country_code"
    await event.edit(
        "➕ **اضافه کردن کشور**\n\n"
        "کد سرویس رو بفرست (مثلاً: `tg`)\n"
        "بعدش کد کشور و قیمت فروش.",
        buttons=[[Button.inline("❌ انصراف", b"admin_panel")]]
    )

# --- Manage Countries ---
@client.on(events.CallbackQuery(data=b"admin_countries"))
async def admin_countries(event):
    if event.sender_id != ADMIN_ID:
        return
    services = get_all_services()
    buttons = []
    for code, name, icon in services:
        countries = get_all_countries(code)
        count = len(countries)
        buttons.append([Button.inline(f"{icon} {name} ({count} کشور)", f"admin_country_list:{code}".encode())])
    buttons.append([Button.inline("➕ اضافه کشور دستی", b"admin_add_manual")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_panel")])
    await event.edit("🌍 **مدیریت کشورها**\n\nروی سرویس کلیک کن:", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"admin_country_list:")))
async def admin_country_list(event):
    if event.sender_id != ADMIN_ID:
        return
    service = event.data.decode().split(':')[1]
    countries = get_all_countries(service)

    if not countries:
        await event.edit("⚠️ کشوری نیست.", buttons=[
            [Button.inline("➕ اضافه", b"admin_add_manual")],
            [Button.inline("🔙 بازگشت", b"admin_countries")]
        ])
        return

    text = f"🌍 **لیست کشورها ({service.upper()}):**\n\n"
    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        text += f"{flag} {c_name} | API: {api_price} | فروش: {sell_price}\n"
        buttons.append([Button.inline(f"🗑️ حذف {flag} {c_name}", f"admin_del_country:{service}:{c_code}".encode())])

    buttons.append([Button.inline("➕ اضافه کشور", b"admin_add_manual")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_countries")])
    await event.edit(text, buttons=buttons)

# --- Add Country Manually ---
@client.on(events.CallbackQuery(data=b"admin_add_manual"))
async def admin_add_manual(event):
    if event.sender_id != ADMIN_ID:
        return
    user_state[event.sender_id] = {"step": "add_country_service", "data": {}}
    await event.edit(
        "➕ **اضافه کردن کشور (دستی)**\n\n"
        "مرحله ۱: کد سرویس رو بفرست\n"
        "مثال: `tg`, `wa`, `ig`, `go`",
        buttons=[[Button.inline("❌ انصراف", b"admin_countries")]]
    )

# --- Remove Country ---
@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"admin_del_country:")))
async def admin_del_country(event):
    if event.sender_id != ADMIN_ID:
        return
    parts = event.data.decode().split(':')
    service = parts[1]
    country_code = parts[2]
    remove_country(service, country_code)
    await event.answer("✅ حذف شد!", alert=True)
    # Refresh list
    countries = get_all_countries(service)
    text = f"🌍 **لیست کشورها ({service.upper()}):**\n\n"
    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        text += f"{flag} {c_name} | API: {api_price} | فروش: {sell_price}\n"
        buttons.append([Button.inline(f"🗑️ {flag} {c_name}", f"admin_del_country:{service}:{c_code}".encode())])
    buttons.append([Button.inline("➕ اضافه", b"admin_add_manual")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_countries")])
    await event.edit(text, buttons=buttons)

# --- Manage Services ---
@client.on(events.CallbackQuery(data=b"admin_services"))
async def admin_services(event):
    if event.sender_id != ADMIN_ID:
        return
    services = get_all_services()
    text = "📱 **سرویس‌های فعال:**\n\n"
    buttons = []
    for code, name, icon in services:
        text += f"{icon} {name} (`{code}`)\n"
        buttons.append([Button.inline(f"🗑️ حذف {name}", f"admin_del_service:{code}".encode())])
    buttons.append([Button.inline("➕ اضافه سرویس", b"admin_add_service")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_panel")])
    await event.edit(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"admin_add_service"))
async def admin_add_service(event):
    if event.sender_id != ADMIN_ID:
        return
    user_state[event.sender_id] = {"step": "add_service_code", "data": {}}
    await event.edit(
        "➕ **اضافه کردن سرویس**\n\n"
        "کد سرویس رو بفرست (مثلاً: `snap`)",
        buttons=[[Button.inline("❌ انصراف", b"admin_services")]]
    )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"admin_del_service:")))
async def admin_del_service(event):
    if event.sender_id != ADMIN_ID:
        return
    code = event.data.decode().split(':')[1]
    conn = sqlite3.connect('sms_bot.db')
    conn.cursor().execute('DELETE FROM services WHERE code = ?', (code,))
    conn.commit()
    conn.close()
    await event.answer("✅ حذف شد!")
    await admin_services(event)

# --- Users List ---
@client.on(events.CallbackQuery(data=b"admin_users"))
async def admin_users(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    text = "👥 **لیست کاربران:**\n\n"
    for uid, bal in users:
        text += f"🆔 `{uid}` | 💰 {bal:.2f} $\n"
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

# --- Stats ---
@client.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    services = get_all_services()
    total_users = len(users)
    total_balance = sum(b for _, b in users)
    countries_count = 0
    for code, _, _ in services:
        countries_count += len(get_all_countries(code))

    text = (
        f"📊 **آمار کامل**\n"
        f"────────────────\n"
        f"👥 کل کاربران: {total_users}\n"
        f"💰 کل موجودی: {total_balance:.2f} $\n"
        f"📱 سرویس‌ها: {len(services)}\n"
        f"🌍 کشورها: {countries_count}\n"
        f"────────────────\n"
        f"🤖 وضعیت: فعال ✅"
    )
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

# ==================== ADMIN TEXT INPUT HANDLER ====================

@client.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and not e.text.startswith('/') and e.is_private))
async def admin_text_handler(event):
    user_id = event.sender_id
    state = user_state.get(user_id)

    if not state:
        return

    text = event.raw_text.strip()

    # --- Add Country Manual Flow ---
    if isinstance(state, dict) and state.get("step") == "add_country_service":
        state["data"]["service"] = text
        state["step"] = "add_country_code"
        await event.respond(
            f"✅ سرویس: `{text}`\n\n"
            f"مرحله ۲: کد کشور رو بفرست\n"
            f"مثال: `0` (روسیه), `1` (اوکراین)"
        )
        return

    if isinstance(state, dict) and state.get("step") == "add_country_code":
        state["data"]["country_code"] = text
        state["step"] = "add_country_name"
        await event.respond(
            f"✅ کد کشور: `{text}`\n\n"
            f"مرحله ۳: نام کشور و پرچم\n"
            f"مثال: `🇷🇺 روسیه`"
        )
        return

    if isinstance(state, dict) and state.get("step") == "add_country_name":
        state["data"]["country_name"] = text
        state["step"] = "add_country_api_price"
        await event.respond(
            f"✅ نام: {text}\n\n"
            f"مرحله ۴: قیمت API ($)\n"
            f"مثال: `15000`"
        )
        return

    if isinstance(state, dict) and state.get("step") == "add_country_api_price":
        state["data"]["api_price"] = float(text)
        state["step"] = "add_country_sell_price"
        await event.respond(
            f"✅ قیمت API: {text}\n\n"
            f"مرحله ۵: قیمت فروش ($)\n"
            f"مثال: `25000`"
        )
        return

    if isinstance(state, dict) and state.get("step") == "add_country_sell_price":
        d = state["data"]
        sell_price = float(text)
        add_country(d["service"], d["country_code"], d["country_name"], d["country_name"], d["api_price"], sell_price)
        user_state.pop(user_id, None)
        await event.respond(
            f"✅ **کشور اضافه شد!**\n\n"
            f"🌍 {d['country_name']}\n"
            f"💰 API: {d['api_price']:.2f} | فروش: {sell_price:.2f} $",
            buttons=[[Button.inline("⚙️ پنل ادمین", b"admin_panel")]]
        )
        return

    # --- Add Service Flow ---
    if isinstance(state, dict) and state.get("step") == "add_service_code":
        state["data"]["code"] = text
        state["step"] = "add_service_name"
        await event.respond(f"✅ کد: `{text}`\n\nنام سرویس رو بفرست:")
        return

    if isinstance(state, dict) and state.get("step") == "add_service_name":
        state["data"]["name"] = text
        state["step"] = "add_service_icon"
        await event.respond(f"✅ نام: {text}\n\nایموجی سرویس رو بفرست:")
        return

    if isinstance(state, dict) and state.get("step") == "add_service_icon":
        d = state["data"]
        add_service(d["code"], d["name"], text)
        user_state.pop(user_id, None)
        await event.respond(
            f"✅ **سرویس اضافه شد!**\n\n{text} {d['name']} (`{d['code']}`)",
            buttons=[[Button.inline("⚙️ پنل ادمین", b"admin_panel")]]
        )
        return

# ==================== RUN ====================
async def main():
    print("Bot is up and running...")
    await client.start(bot_token=BOT_TOKEN)
    print("Bot connected to Telegram!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

