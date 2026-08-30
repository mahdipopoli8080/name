import asyncio
import sqlite3
import aiohttp
from telethon import TelegramClient, events, Button

# ==================== CONFIGURATION ====================
API_ID = 8477522               # Telegram API ID
API_HASH = '366c19cf69e02cad530261ad81212a85'     # Telegram API Hash
BOT_TOKEN = '8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek'   # Bot Token from @BotFather

SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_ENDPOINT = 'https://smsbower.app/stubs/handler_api.php'

ADMIN_ID = 5190717598           # شناسه عددی ادمین Telegram
SERVICE_MARGIN_PERCENT = 0    # درصد سود شما روی قیمت‌های اصلی SMSBower (مثلاً ۲۰٪)
# =======================================================

# Database Initialization
def init_db():
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
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

init_db()

client = TelegramClient('smsbower_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# API Request Helper for SMSBower
async def call_smsbower(action, **params):
    base_params = {'api_key': SMSBOWER_API_KEY, 'action': action}
    base_params.update(params)
    async with aiohttp.ClientSession() as session:
        async with session.get(SMSBOWER_ENDPOINT, params=base_params) as resp:
            return await resp.text()

pending_receipts = {}

# --- Bot Event Handlers ---

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    bal = get_balance(user_id)
    text = (
        f"👋 **به ربات خرید شماره مجازی خوش آمدید!**\n\n"
        f"🆔 شناسه شما: `{user_id}`\n"
        f"💰 موجودی کیف‌‌پول: **{bal:,.0f} تومان**\n\n"
        f"از منوی زیر جهت خرید شماره یا شارژ حساب استفاده کنید:"
    )
    buttons = [
        [Button.inline("📱 خرید شماره مجازی", b"buy_menu")],
        [Button.inline("💳 شارژ حساب (پرداخت دستی)", b"deposit_manual"), Button.inline("👤 حساب کاربری", b"profile")]
    ]
    await event.respond(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"profile"))
async def profile_handler(event):
    user_id = event.sender_id
    bal = get_balance(user_id)
    text = f"👤 **پروفایل کاربری**\n\n🆔 شناسه کاربری: `{user_id}`\n💰 موجودی: **{bal:,.0f} تومان**"
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"back_main")]])

@client.on(events.CallbackQuery(data=b"buy_menu"))
async def buy_menu(event):
    # منوی انتخاب برنامه / سرویس
    buttons = [
        [Button.inline("🔹 تلگرام (Telegram)", b"service:tg"), Button.inline("🔹 واتساپ (WhatsApp)", b"service:wa")],
        [Button.inline("🔹 اینستاگرام (Instagram)", b"service:ig"), Button.inline("🔹 گوگل / جی‌میل", b"service:go")],
        [Button.inline("🔙 بازگشت", b"back_main")]
    ]
    await event.edit("📱 **لطفاً سرویس مورد نظر خود را انتخاب کنید:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"service:")))
async def select_country(event):
    service_code = event.data.decode().split(':')[1]
    
    # دریافت موجودی و قیمت از SMSBower
    res = await call_smsbower('getPrices', service=service_code)
    
    # لیست نمونه کشورها (0: روسیه، 1: اوکراین، 2: قزاقستان و ...)
    # برحسب نیاز می‌توانید کد کشورها را گسترش دهید
    countries = [
        ("🇷🇺 روسیه", "0", 35000),
        ("🇺🇦 اوکراین", "1", 30000),
        ("🇰🇿 قزاقستان", "2", 25000),
        ("🇵🇭 فیلیپین", "4", 20000)
    ]
    
    buttons = []
    for name, c_id, default_price in countries:
        # اعمال درصد سود به قیمت
        final_price = default_price * (1 + SERVICE_MARGIN_PERCENT / 100)
        btn_data = f"buy:{service_code}:{c_id}:{int(final_price)}".encode()
        buttons.append([Button.inline(f"{name} - {final_price:,.0f} تومان", btn_data)])
        
    buttons.append([Button.inline("🔙 بازگشت", b"buy_menu")])
    await event.edit(f"🌐 **کشور مورد نظر را برای سرویس ({service_code.upper()}) انتخاب کنید:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"buy:")))
async def process_buy(event):
    _, service, country, price = event.data.decode().split(':')
    price = float(price)
    user_id = event.sender_id
    
    bal = get_balance(user_id)
    if bal < price:
        await event.answer("❌ موجودی کیف‌پول شما کافی نیست! لطفاً حساب خود را شارژ کنید.", alert=True)
        return

    # درخواست شماره از API
    res = await call_smsbower('getNumber', service=service, country=country)
    
    if 'ACCESS_NUMBER' in res:
        # ساختار پاسخ: ACCESS_NUMBER:ID:NUMBER
        parts = res.split(':')
        order_id = parts[1]
        phone_number = parts[2]
        
        # کسر از دیتابیس
        update_balance(user_id, -price)
        
        buttons = [
            [Button.inline("📩 دریافت کد پیامک", f"get_sms:{order_id}".encode())],
            [Button.inline("❌ لغو سفارش و استرداد وجه", f"cancel_order:{order_id}:{price}".encode())]
        ]
        
        text = (
            f"✅ **شماره با موفقیت تحویل داده شد!**\n\n"
            f"📱 شماره: `+{phone_number}`\n"
            f"🆔 شناسه سفارش: `{order_id}`\n\n"
            f"کد را وارد کرده و پس از ارسال، دکمه **دریافت کد پیامک** را بزنید."
        )
        await event.edit(text, buttons=buttons)
    else:
        await event.answer("⚠️ شماره‌ای برای این کشور/سرویس موجود نیست. مجدداً تلاش کنید.", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"get_sms:")))
async def check_sms(event):
    order_id = event.data.decode().split(':')[1]
    res = await call_smsbower('getStatus', id=order_id)
    
    if 'STATUS_OK' in res:
        sms_code = res.split(':')[1]
        # اعلام اتمام موفقیت‌آمیز سفارش به SMSBower
        await call_smsbower('setStatus', id=order_id, status='6')
        
        await event.edit(
            f"📩 **کد تایید دریافت شد:**\n\n"
            f"🔑 کد: `{sms_code}`\n\n"
            f"تراکنش با موفقیت به پایان رسید."
        )
    elif 'STATUS_WAIT_CODE' in res:
        await event.answer("⏳ هنوز پیامکی دریافت نشده است. لطفاً چند ثانیه دیگر بزنید.", alert=True)
    elif 'STATUS_CANCEL' in res:
        await event.answer("❌ این سفارش منقضی یا لغو شده است.", alert=True)
    else:
        await event.answer(f"پاسخ سیستم: {res}", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cancel_order:")))
async def cancel_order(event):
    _, order_id, price = event.data.decode().split(':')
    price = float(price)
    user_id = event.sender_id
    
    # ارسال وضعیت لغو به SMSBower (Status 8 = Cancel)
    res = await call_smsbower('setStatus', id=order_id, status='8')
    
    if 'ACCESS_CANCEL' in res or 'ACCESS_OK' in res:
        # عودت وجه به حساب کاربر
        update_balance(user_id, price)
        await event.edit("✅ **سرفارش لغو شد و مبلغ به کیف‌پول شما بازگشت.**")
    else:
        await event.answer("❌ امکان لغو این سفارش وجود ندارد (ممکن است کد ارسال شده باشد).", alert=True)

# --- سیستم پرداختی دستی ---

@client.on(events.CallbackQuery(data=b"deposit_manual"))
async def deposit_manual(event):
    pending_receipts[event.sender_id] = True
    text = (
        "💳 **شارژ کارت به کارت (پرداخت دستی)**\n\n"
        "مبلغ دلخواه را به شماره کارت زیر واریز نمایید:\n\n"
        "💳 شماره کارت: `6037-0000-0000-0000`\n"
        "👤 به نام: مدیر سیستم\n\n"
        "📌 پس از واریز، **تصویر فیش یا شماره پیگیری** را همینجا ارسال کنید."
    )
    await event.edit(text, buttons=[[Button.inline("❌ انصراف", b"back_main")]])

@client.on(events.NewMessage)
async def receipt_handler(event):
    user_id = event.sender_id
    if user_id in pending_receipts and not event.text.startswith('/'):
        del pending_receipts[user_id]
        
        # فوروارد فیش برای ادمین جهت تایید
        await event.forward_to(ADMIN_ID)
        
        btn = [
            [Button.inline("✅ تایید (۵۰,۰۰۰ تومان)", f"approve:{user_id}:50000".encode()),
             Button.inline("✅ تایید (۱۰۰,۰۰۰ تومان)", f"approve:{user_id}:100000".encode())],
            [Button.inline("❌ رد فیش", f"reject:{user_id}".encode())]
        ]
        await client.send_message(ADMIN_ID, f"📥 **فیش واریزی جدید**\n👤 کاربر: `{user_id}`", buttons=btn)
        await event.respond("✅ فیش شما ارسال شد. پس از بررسی ادمین، حساب شما شارژ می‌شود.")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"approve:")))
async def approve(event):
    if event.sender_id != ADMIN_ID: return
    _, u_id, amt = event.data.decode().split(':')
    u_id, amt = int(u_id), float(amt)
    
    update_balance(u_id, amt)
    await client.send_message(u_id, f"✅ **شارژ موفق!**\nمبلغ {amt:,.0f} تومان به حساب شما اضافه شد.")
    await event.edit(f"✅ واریزی کاربر `{u_id}` تایید شد.")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"reject:")))
async def reject(event):
    if event.sender_id != ADMIN_ID: return
    u_id = int(event.data.decode().split(':')[1])
    await client.send_message(u_id, "❌ **فیش واریزی شما توسط ادمین رد شد.**")
    await event.edit(f"❌ درخواست کاربر `{u_id}` رد شد.")

@client.on(events.CallbackQuery(data=b"back_main"))
async def back_main(event):
    await start_handler(event)

print("Bot is up and running...")
client.run_until_disconnected()
