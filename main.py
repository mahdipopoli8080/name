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
SMSBOWER_ENDPOINT = 'https://smsbower.page/stubs/handler_api.php'

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

def get_country_count(service):
    conn = sqlite3.connect('sms_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM countries WHERE service = ?', (service,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

init_db()

client = TelegramClient('smsbower_bot_session', API_ID, API_HASH)
user_state = {}

# Flag mapping for common countries
COUNTRY_FLAGS = {
    '0': '🇷🇺', '1': '🇺🇦', '2': '🇰🇿', '3': '🇺🇿', '4': '🇵🇭',
    '5': '🇮🇩', '6': '🇮🇳', '7': '🇺🇸', '8': '🇬🇧', '9': '🇨🇳',
    '10': '🇧🇷', '11': '🇵🇰', '12': '🇳🇬', '13': '🇧🇩', '14': '🇪🇬',
    '15': '🇻🇳', '16': '🇲🇽', '17': '🇹🇷', '18': '🇩🇪', '19': '🇫🇷',
    '20': '🇮🇹', '21': '🇪🇸', '22': '🇰🇷', '23': '🇯🇵', '24': '🇨🇦',
    '25': '🇦🇺', '26': '🇸🇦', '27': '🇦🇪', '28': '🇮🇷', '29': '🇮🇶',
    '30': '🇹🇭', '31': '🇲🇾', '32': '🇸🇬', '33': '🇿🇦', '34': '🇰🇪',
    '35': '🇬🇭', '36': '🇨🇴', '37': '🇦🇷', '38': '🇨🇱', '39': '🇵🇪',
    '40': '🇵🇱', '41': '🇷🇴', '42': '🇨🇿', '43': '🇭🇺', '44': '🇸🇪',
    '45': '🇳🇴', '46': '🇩🇰', '47': '🇫🇮', '48': '🇮🇪', '49': '🇵🇹',
    '50': '🇬🇷', '51': '🇧🇬', '52': '🇭🇷', '53': '🇷🇸', '54': '🇺🇿',
    '55': '🇰🇬', '56': '🇹🇯', '57': '🇦🇲', '58': '🇬🇪', '59': '🇲🇩',
    '60': '🇧🇾', '61': '🇱🇹', '62': '🇱🇻', '63': '🇪🇪', '64': '🇰🇵',
    '65': '🇲🇲', '66': '🇰🇭', '67': '🇱🇦', '68': '🇳🇵', '69': '🇱🇰',
    '70': '🇦🇫', '71': '🇹🇳', '72': '🇩🇿', '73': '🇲🇦', '74': '🇱🇾',
    '75': '🇸🇩', '76': '🇪🇹', '77': '🇹🇿', '78': '🇺🇬', '79': '🇿🇲',
    '80': '🇿🇼', '81': '🇧🇼', '82': '🇲🇿', '83': '🇦🇴', '84': '🇨🇮',
    '85': '🇸🇳', '86': '🇲🇱', '87': '🇧🇫', '88': '🇳🇪', '89': '🇹🇩',
    '90': '🇨🇲', '91': '🇬🇶', '92': '🇬🇦', '93': '🇨🇬', '94': '🇨🇩',
    '95': '🇷🇼', '96': '🇧🇮', '97': '🇸🇸', '98': '🇪🇷', '99': '🇩🇯',
    '100': '🇸🇴', '101': '🇲🇬', '102': '🇲🇺', '103': '🇸🇨', '104': '🇨🇻',
    '105': '🇸🇹', '106': '🇬🇼', '107': '🇬🇲', '108': '🇱🇷', '109': '🇸🇱',
    '110': '🇬🇳', '111': '🇧🇮', '112': '🇲🇼', '113': '🇿🇲', '114': '🇲🇿',
    '115': '🇧🇼', '116': '🇳🇦', '117': '🇱🇸', '118': '🇸🇿', '119': '🇦🇩',
    '120': '🇲🇨', '121': '🇱🇮', '122': '🇸🇲', '123': '🇻🇦', '124': '🇲🇹',
    '125': '🇨🇾', '126': '🇮🇸', '127': '🇱🇺', '128': '🇧🇪', '129': '🇳🇱',
    '130': '🇦🇹', '131': '🇨🇭', '132': '🇱🇧', '133': '🇯🇴', '134': '🇸🇾',
    '135': '🇮🇱', '136': '🇵🇸', '137': '🇾🇪', '138': '🇴🇲', '139': '🇰🇼',
    '140': '🇧🇭', '141': '🇶🇦', '142': '🇦🇫', '143': '🇲🇻', '144': '🇧🇹',
    '145': '🇧🇳', '146': '🇹🇱', '147': '🇹🇻', '148': '🇰🇮', '149': '🇫🇯',
    '150': '🇵🇬', '151': '🇸🇧', '152': '🇻🇺', '153': '🇼🇸', '154': '🇹🇴',
    '155': '🇲🇭', '156': '🇵🇼', '157': '🇫🇲', '158': '🇳🇷', '159': '🇹🇻',
}

# Country name mapping
COUNTRY_NAMES = {
    '0': 'روسیه', '1': 'اوکراین', '2': 'قزاقستان', '4': 'فیلیپین',
    '5': 'اندونزی', '6': 'هند', '7': 'آمریکا', '8': 'انگلیس', '9': 'چین',
    '10': 'برزیل', '11': 'پاکستان', '12': 'نیجریه', '13': 'بنگلادش', '14': 'مصر',
    '15': 'ویتنام', '16': 'مکزیک', '17': 'ترکیه', '18': 'آلمان', '19': 'فرانسه',
    '20': 'ایتالیا', '21': 'اسپانیا', '22': 'کره جنوبی', '23': 'ژاپن', '24': 'کانادا',
    '25': 'استرالیا', '26': 'عربستان', '27': 'امارات', '28': 'ایران', '29': 'عراق',
    '30': 'تایلند', '31': 'مالزی', '32': 'سنگاپور', '33': 'آفریقای جنوبی', '34': 'کنیا',
    '35': 'غنا', '36': 'کلمبیا', '37': 'آرژانتین', '38': 'شیلی', '39': 'پرو',
    '40': 'لهستان', '41': 'رومانی', '42': 'چک', '43': 'مجارستان', '44': 'سوئد',
    '45': 'نروژ', '46': 'دانمارک', '47': 'فنلاند', '48': 'ایرلند', '49': 'پرتغال',
    '50': 'یونان', '51': 'بلغارستان', '52': 'کرواسی', '53': 'صربستان', '54': 'ازبکستان',
    '55': 'قرقیزستان', '56': 'تاجیکستان', '57': 'ارمنستان', '58': 'گرجستان', '59': 'مولداوی',
    '60': 'بلاروس', '61': 'لیتوانی', '62': 'لتونی', '63': 'استونی', '64': 'کره شمالی',
    '65': 'میانمار', '66': 'کامبوج', '67': 'لائوس', '68': 'نپال', '69': 'سری‌لانکا',
    '70': 'افغانستان', '71': 'تونس', '72': 'الجزایر', '73': 'مراکش', '74': 'لیبی',
    '75': 'سودان', '76': 'اتیوپی', '77': 'تانزانیا', '78': 'اوگاندا', '79': 'زامبیا',
    '80': 'زیمبابوه', '81': 'بوتسوانا', '82': 'موزامبیک', '83': 'آنگولا', '84': 'ساحل عاج',
    '85': 'سنگال', '86': 'مالی', '87': 'بورکینافاسو', '88': 'نیجر', '89': 'چاد',
    '90': 'کامرون', '91': 'گینه استوایی', '92': 'گابن', '93': 'کنگو', '94': 'کنگو (DRC)',
    '95': 'رواندا', '96': 'بوروندی', '97': 'سودان جنوبی', '98': 'اریتره', '99': 'جیبوتی',
    '100': 'سومالی', '101': 'ماداگاسکار', '102': 'موریس', '103': 'سیشل', '104': 'کابو ورده',
    '105': 'سائوتومه', '106': 'گینه بیسائو', '107': 'گامبیا', '108': 'لیبریا', '109': 'سیرالئون',
    '110': 'گینه', '111': 'بوروندی', '112': 'مالاوی', '113': 'زامبیا', '114': 'موزامبیک',
    '115': 'بوتسوانا', '116': 'نامیبیا', '117': 'لسوتو', '118': 'اسواتینی', '119': 'آندورا',
    '120': 'موناکو', '121': 'لیختن‌اشتاین', '122': 'سن مارینو', '123': 'واتیکان', '124': 'مالت',
    '125': 'قبرس', '126': 'ایسلند', '127': 'لوکزامبورگ', '128': 'بلژیک', '129': 'هلند',
    '130': 'اتریش', '131': 'سوئیس', '132': 'لبنان', '133': 'اردن', '134': 'سوریه',
    '135': 'اسرائیل', '136': 'فلسطین', '137': 'یمن', '138': 'عمان', '139': 'کویت',
    '140': 'بحرین', '141': 'قطر', '142': 'افغانستان', '143': 'مالدیو', '144': 'بوتان',
    '145': 'برونئی', '146': 'تیمور شرقی', '147': 'تووالو', '148': 'کیریباتی', '149': 'فیجی',
    '150': 'پاپوا گینه نو', '151': 'جزایر سلیمان', '152': 'وانواتو', '153': 'ساموا', '154': 'تونگا',
    '155': 'جزایر مارشال', '156': 'پالائو', '157': 'میکرونزی', '158': 'نائورو', '159': 'تووالو',
}

# ==================== API ====================
async def call_smsbower(action, **params):
    base_params = {'api_key': SMSBOWER_API_KEY, 'action': action}
    base_params.update(params)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SMSBOWER_ENDPOINT, params=base_params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                return await resp.text()
    except Exception as e:
        return f"ERROR:{e}"

async def fetch_prices_from_api(service=None):
    """Fetch prices from SMSBower API"""
    try:
        params = {'api_key': SMSBOWER_API_KEY, 'action': 'getPrices'}
        if service:
            params['service'] = service

        async with aiohttp.ClientSession() as session:
            async with session.get(SMSBOWER_ENDPOINT, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                return data
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return None

async def fetch_services_from_api():
    """Fetch services list from SMSBower API"""
    try:
        params = {'api_key': SMSBOWER_API_KEY, 'action': 'getServicesList'}
        async with aiohttp.ClientSession() as session:
            async with session.get(SMSBOWER_ENDPOINT, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                return data.get('services', [])
    except Exception as e:
        print(f"Error fetching services: {e}")
        return []

async def fetch_countries_from_api():
    """Fetch countries list from SMSBower API"""
    try:
        params = {'api_key': SMSBOWER_API_KEY, 'action': 'getCountriesList'}
        async with aiohttp.ClientSession() as session:
            async with session.get(SMSBOWER_ENDPOINT, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                return data
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []

async def sync_services():
    """Sync services from API to database"""
    services = await fetch_services_from_api()
    if services:
        for svc in services:
            code = svc.get('code', '')
            name = svc.get('name', code)
            add_service(code, name, '🔹')
        print(f"Synced {len(services)} services from API")

async def sync_countries_for_service(service_code):
    """Sync countries and prices for a specific service"""
    data = await fetch_prices_from_api(service_code)
    if data:
        for country_code, services in data.items():
            if service_code in services:
                info = services[service_code]
                cost = info.get('cost', 0)
                flag = COUNTRY_FLAGS.get(str(country_code), '🌍')
                name = COUNTRY_NAMES.get(str(country_code), f'Country {country_code}')
                sell_price = cost * (1 + SERVICE_MARGIN_PERCENT / 100)
                add_country(service_code, str(country_code), name, flag, cost, sell_price)
        print(f"Synced countries for {service_code}")

pending_receipts = {}

# ==================== USER HANDLERS ====================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    bal = get_balance(user_id)
    text = (
        f"👋 **به ربات خرید شماره مجازی خوش آمدید!**\n\n"
        f"🆔 شناسه شما: `{user_id}`\n"
        f"💰 موجودی: **{bal:.2f}$**\n\n"
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
    text = f"👤 **پروفایل**\n\n🆔 `{user_id}`\n💰 موجودی: **{bal:.2f}$**"
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"back_main")]])

@client.on(events.CallbackQuery(data=b"buy_menu"))
async def buy_menu(event):
    services = get_all_services()
    buttons = []
    row = []
    for code, name, icon in services:
        count = get_country_count(code)
        row.append(Button.inline(f"{icon} {name} ({count})", f"service:{code}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([Button.inline("🔙 بازگشت", b"back_main")])
    await event.edit("📱 **سرویس مورد نظر:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"service:")))
async def select_country(event):
    service_code = event.data.decode().split(':')[1]
    countries = get_all_countries(service_code)

    if not countries:
        await event.edit(
            f"⚠️ کشوری برای `{service_code.upper()}` نیست.\nاز ادمین بخواه اضافه کنه.",
            buttons=[[Button.inline("🔙 بازگشت", b"buy_menu")]]
        )
        return

    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        btn_data = f"buy:{service_code}:{c_code}:{sell_price}".encode()
        buttons.append([Button.inline(f"{flag} {c_name} - {sell_price:.2f}$", btn_data)])

    buttons.append([Button.inline("🔙 بازگشت", b"buy_menu")])
    await event.edit(f"🌐 **کشور برای ({service_code.upper()}):**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"buy:")))
async def process_buy(event):
    _, service, country, price = event.data.decode().split(':')
    price = float(price)
    user_id = event.sender_id

    bal = get_balance(user_id)
    if bal < price:
        await event.answer("❌ موجودی کافی نیست!", alert=True)
        return

    await event.edit("⏳ **دریافت شماره...**")
    res = await call_smsbower('getNumber', service=service, country=country)

    if 'ACCESS_NUMBER' in res:
        parts = res.split(':')
        order_id = parts[1]
        phone_number = parts[2]
        update_balance(user_id, -price)

        country_info = get_country_info(service, country)
        flag = country_info[1] if country_info else "📱"

        buttons = [
            [Button.inline("📩 دریافت کد", f"get_sms:{order_id}".encode())],
            [Button.inline("❌ لغو", f"cancel_order:{order_id}:{price}".encode())]
        ]
        text = (
            f"✅ **شماره تحویل شد!**\n\n"
            f"{flag} شماره: `+{phone_number}`\n"
            f"🆔 سفارش: `{order_id}`\n\n"
            f"کد رو وارد کن و دکمه **دریافت کد** رو بزن."
        )
        await event.edit(text, buttons=buttons)
    else:
        await event.edit(
            f"⚠️ شماره موجود نیست.",
            buttons=[
                [Button.inline("🔄 تلاش مجدد", f"buy:{service}:{country}:{price}".encode())],
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
        await event.edit(f"📩 **کد:** `{sms_code}`\n\n✅ تمام شد.")
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
            [Button.inline("✅ 5$", f"approve:{user_id}:5".encode()),
             Button.inline("✅ 10$", f"approve:{user_id}:10".encode())],
            [Button.inline("✅ 20$", f"approve:{user_id}:20".encode()),
             Button.inline("✅ 50$", f"approve:{user_id}:50".encode())],
            [Button.inline("❌ رد", f"reject:{user_id}".encode())]
        ]
        await client.send_message(ADMIN_ID, f"📥 **فیش جدید** | 👤 `{user_id}`", buttons=btn)
        await event.respond("✅ فیش ارسال شد. منتظر تایید.")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"approve:")))
async def approve(event):
    if event.sender_id != ADMIN_ID:
        return
    _, u_id, amt = event.data.decode().split(':')
    u_id, amt = int(u_id), float(amt)
    update_balance(u_id, amt)
    await client.send_message(u_id, f"✅ **شارژ!** {amt:.2f}$ اضافه شد.")
    await event.edit(f"✅ `{u_id}` تایید | {amt:.2f}$")

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
    total_countries = sum(get_country_count(c) for c, _, _ in services)

    text = (
        f"⚙️ **پنل ادمین**\n"
        f"────────────────\n"
        f"👥 کاربران: {total_users}\n"
        f"💰 کل موجودی: {total_balance:.2f}$\n"
        f"📱 سرویس‌ها: {len(services)}\n"
        f"🌍 کشورها: {total_countries}"
    )
    buttons = [
        [Button.inline("🌍 مدیریت کشورها", b"admin_countries"), Button.inline("📱 سرویس‌ها", b"admin_services")],
        [Button.inline("🔄 سینک خودکار از API", b"admin_auto_sync")],
        [Button.inline("🌐 قیمت‌های API", b"admin_fetch_api")],
        [Button.inline("👥 کاربران", b"admin_users"), Button.inline("📊 آمار", b"admin_stats")],
        [Button.inline("🔙 بازگشت", b"back_main")]
    ]
    await event.edit(text, buttons=buttons)

# --- Auto Sync from API ---
@client.on(events.CallbackQuery(data=b"admin_auto_sync"))
async def admin_auto_sync(event):
    if event.sender_id != ADMIN_ID:
        return
    await event.edit("⏳ **سینک خودکار از API...**")

    # Sync services
    await sync_services()

    # Sync prices for each service
    services = get_all_services()
    synced = 0
    for code, name, icon in services:
        data = await fetch_prices_from_api(code)
        if data:
            for country_code, svc_data in data.items():
                if code in svc_data:
                    info = svc_data[code]
                    cost = info.get('cost', 0)
                    if cost > 0:
                        flag = COUNTRY_FLAGS.get(str(country_code), '🌍')
                        cname = COUNTRY_NAMES.get(str(country_code), f'Country {country_code}')
                        sell_price = cost * (1 + SERVICE_MARGIN_PERCENT / 100)
                        add_country(code, str(country_code), cname, flag, cost, sell_price)
                        synced += 1

    await event.edit(
        f"✅ **سینک کامل شد!**\n\n"
        f"📱 سرویس‌ها: {len(services)}\n"
        f"🌍 کشورها: {synced}",
        buttons=[[Button.inline("⚙️ پنل ادمین", b"admin_panel")]]
    )

# --- Fetch API Prices ---
@client.on(events.CallbackQuery(data=b"admin_fetch_api"))
async def admin_fetch_api(event):
    if event.sender_id != ADMIN_ID:
        return
    await event.edit("⏳ **دریافت قیمت‌ها...**")

    services = get_all_services()
    text = "📊 **قیمت‌های SMSBower:**\n\n"
    total = 0

    for code, name, icon in services:
        data = await fetch_prices_from_api(code)
        if data:
            items = []
            for country_code, svc_data in data.items():
                if code in svc_data:
                    info = svc_data[code]
                    cost = info.get('cost', 0)
                    count = info.get('count', 0)
                    if cost > 0:
                        flag = COUNTRY_FLAGS.get(str(country_code), '🌍')
                        items.append(f"  {flag} {country_code}: ${cost} ({count})")
                        total += 1
            if items:
                text += f"**{name} ({code}):**\n"
                text += "\n".join(items[:5]) + "\n"
                if len(items) > 5:
                    text += f"  ... و {len(items)-5} کشور دیگر\n"
                text += "\n"

    if total > 0:
        text = f"📊 **{total} قیمت یافت شد**\n────────────────\n" + text
        if len(text) > 4000:
            text = text[:4000] + "\n..."
        await event.edit(text, buttons=[
            [Button.inline("🔄 سینک خودکار", b"admin_auto_sync")],
            [Button.inline("➕ اضافه دستی", b"admin_add_manual")],
            [Button.inline("🔙 بازگشت", b"admin_panel")]
        ])
    else:
        await event.edit("❌ خطا در دریافت قیمت‌ها", buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

# --- Manage Countries ---
@client.on(events.CallbackQuery(data=b"admin_countries"))
async def admin_countries(event):
    if event.sender_id != ADMIN_ID:
        return
    services = get_all_services()
    buttons = []
    for code, name, icon in services:
        count = get_country_count(code)
        buttons.append([Button.inline(f"{icon} {name} ({count} کشور)", f"admin_country_list:{code}".encode())])
    buttons.append([Button.inline("➕ اضافه کشور دستی", b"admin_add_manual")])
    buttons.append([Button.inline("🔄 سینک خودکار", b"admin_auto_sync")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_panel")])
    await event.edit("🌍 **مدیریت کشورها:**", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"admin_country_list:")))
async def admin_country_list(event):
    if event.sender_id != ADMIN_ID:
        return
    service = event.data.decode().split(':')[1]
    countries = get_all_countries(service)

    if not countries:
        await event.edit("⚠️ کشوری نیست.", buttons=[
            [Button.inline("➕ اضافه", b"admin_add_manual")],
            [Button.inline("🔄 سینک", b"admin_auto_sync")],
            [Button.inline("🔙 بازگشت", b"admin_countries")]
        ])
        return

    text = f"🌍 **{service.upper()}:**\n\n"
    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        text += f"{flag} {c_name} | API: ${api_price} | فروش: ${sell_price}\n"
        buttons.append([Button.inline(f"🗑️ {flag} {c_name}", f"admin_del_country:{service}:{c_code}".encode())])

    buttons.append([Button.inline("➕ اضافه", b"admin_add_manual")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_countries")])
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await event.edit(text, buttons=buttons)

# --- Add Country Manual ---
@client.on(events.CallbackQuery(data=b"admin_add_manual"))
async def admin_add_manual(event):
    if event.sender_id != ADMIN_ID:
        return
    user_state[event.sender_id] = {"step": "add_country_service", "data": {}}
    await event.edit(
        "➕ **اضافه کردن کشور**\n\n"
        "مرحله ۱: کد سرویس (مثلاً `tg`, `wa`, `ig`)",
        buttons=[[Button.inline("❌ انصراف", b"admin_countries")]]
    )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"admin_del_country:")))
async def admin_del_country(event):
    if event.sender_id != ADMIN_ID:
        return
    parts = event.data.decode().split(':')
    service = parts[1]
    country_code = parts[2]
    remove_country(service, country_code)
    await event.answer("✅ حذف شد!")
    # Refresh
    countries = get_all_countries(service)
    text = f"🌍 **{service.upper()}:**\n\n"
    buttons = []
    for c_code, c_name, flag, api_price, sell_price in countries:
        text += f"{flag} {c_name} | API: ${api_price} | فروش: ${sell_price}\n"
        buttons.append([Button.inline(f"🗑️ {flag} {c_name}", f"admin_del_country:{service}:{c_code}".encode())])
    buttons.append([Button.inline("➕ اضافه", b"admin_add_manual")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_countries")])
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await event.edit(text, buttons=buttons)

# --- Manage Services ---
@client.on(events.CallbackQuery(data=b"admin_services"))
async def admin_services(event):
    if event.sender_id != ADMIN_ID:
        return
    services = get_all_services()
    text = "📱 **سرویس‌ها:**\n\n"
    buttons = []
    for code, name, icon in services:
        count = get_country_count(code)
        text += f"{icon} {name} (`{code}`) - {count} کشور\n"
        buttons.append([Button.inline(f"🗑️ {name}", f"admin_del_service:{code}".encode())])
    buttons.append([Button.inline("➕ سرویس جدید", b"admin_add_service")])
    buttons.append([Button.inline("🔄 سینک از API", b"admin_auto_sync")])
    buttons.append([Button.inline("🔙 بازگشت", b"admin_panel")])
    await event.edit(text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"admin_add_service"))
async def admin_add_service(event):
    if event.sender_id != ADMIN_ID:
        return
    user_state[event.sender_id] = {"step": "add_service_code", "data": {}}
    await event.edit(
        "➕ **سرویس جدید**\n\nکد سرویس رو بفرست (مثلاً: `snap`)",
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

# --- Users & Stats ---
@client.on(events.CallbackQuery(data=b"admin_users"))
async def admin_users(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    text = "👥 **کاربران:**\n\n"
    for uid, bal in users:
        text += f"🆔 `{uid}` | 💰 {bal:.2f}$\n"
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

@client.on(events.CallbackQuery(data=b"admin_stats"))
async def admin_stats(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    services = get_all_services()
    total_users = len(users)
    total_balance = sum(b for _, b in users)
    total_countries = sum(get_country_count(c) for c, _, _ in services)

    text = (
        f"📊 **آمار**\n"
        f"────────────────\n"
        f"👥 کاربران: {total_users}\n"
        f"💰 موجودی: {total_balance:.2f}$\n"
        f"📱 سرویس‌ها: {len(services)}\n"
        f"🌍 کشورها: {total_countries}\n"
        f"────────────────\n"
        f"🤖 فعال ✅"
    )
    await event.edit(text, buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

# ==================== ADMIN TEXT INPUT ====================

@client.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and not e.text.startswith('/') and e.is_private))
async def admin_text_handler(event):
    user_id = event.sender_id
    state = user_state.get(user_id)
    if not state:
        return

    text = event.raw_text.strip()

    if isinstance(state, dict) and state.get("step") == "add_country_service":
        state["data"]["service"] = text
        state["step"] = "add_country_code"
        await event.respond(f"✅ سرویس: `{text}`\n\nمرحله ۲: کد کشور (مثلاً `7` = آمریکا)")
        return

    if isinstance(state, dict) and state.get("step") == "add_country_code":
        state["data"]["country_code"] = text
        state["step"] = "add_country_name"
        flag = COUNTRY_FLAGS.get(text, '🌍')
        cname = COUNTRY_NAMES.get(text, f'Country {text}')
        await event.respond(f"✅ {flag} {cname} (`{text}`)\n\nمرحله ۳: قیمت API ($)\nمثال: `0.11`")
        return

    if isinstance(state, dict) and state.get("step") == "add_country_name":
        state["data"]["api_price"] = float(text)
        state["step"] = "add_country_sell_price"
        await event.respond(f"✅ قیمت API: ${text}\n\nمرحله ۴: قیمت فروش ($)\nمثال: `0.20`")
        return

    if isinstance(state, dict) and state.get("step") == "add_country_sell_price":
        d = state["data"]
        sell_price = float(text)
        flag = COUNTRY_FLAGS.get(d["country_code"], '🌍')
        cname = COUNTRY_NAMES.get(d["country_code"], f'Country {d["country_code"]}')
        add_country(d["service"], d["country_code"], cname, flag, d["api_price"], sell_price)
        user_state.pop(user_id, None)
        await event.respond(
            f"✅ **اضافه شد!**\n\n{flag} {cname}\n💰 API: ${d['api_price']} | فروش: ${sell_price}",
            buttons=[[Button.inline("⚙️ پنل ادمین", b"admin_panel")]]
        )
        return

    if isinstance(state, dict) and state.get("step") == "add_service_code":
        state["data"]["code"] = text
        state["step"] = "add_service_name"
        await event.respond(f"✅ کد: `{text}`\n\nنام سرویس:")
        return

    if isinstance(state, dict) and state.get("step") == "add_service_name":
        state["data"]["name"] = text
        state["step"] = "add_service_icon"
        await event.respond(f"✅ نام: {text}\n\nایموجی:")
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

    # Auto sync on startup
    print("Auto-syncing services and prices...")
    await sync_services()

    # Sync prices for main services
    main_services = ['tg', 'wa', 'ig', 'go']
    for svc in main_services:
        data = await fetch_prices_from_api(svc)
        if data:
            for country_code, svc_data in data.items():
                if svc in svc_data:
                    info = svc_data[svc]
                    cost = info.get('cost', 0)
                    if cost > 0:
                        flag = COUNTRY_FLAGS.get(str(country_code), '🌍')
                        cname = COUNTRY_NAMES.get(str(country_code), f'Country {country_code}')
                        sell_price = cost * (1 + SERVICE_MARGIN_PERCENT / 100)
                        add_country(svc, str(country_code), cname, flag, cost, sell_price)
            print(f"  {svc}: synced")

    print("Auto-sync complete!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
