import asyncio
import random
import string
import time
import json
import os
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from pyrogram import Client as PyroClient
from datetime import datetime, timedelta
import requests

# ===========================
# تنظیمات اولیه (از شما گرفته می‌شود)
# ===========================
API_ID = 8477522          # از my.telegram.org
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8832756816:AAG2x7shLzKBmhAddJxizQfMxx7cXSk1Tpg'  # از @BotFather

# ===========================
# ۱. دکمه شیشه‌ای ارسال شماره
# ===========================
from telethon import Button

async def start_button(event):
    await event.respond(
        "لطفاً شماره تلفن خود را به همراه کد کشور وارد کنید:",
        buttons=[[Button.request_phone("📱 ارسال شماره", resize=True)]]
    )

# ===========================
# ۲. دریافت شماره و لاگین به اکانت اصلی
# ===========================
async def phone_handler(event):
    phone = event.message.phone
    client = TelegramClient('session_main', API_ID, API_HASH)
    await client.start(phone=phone)
    # ذخیره جلسه برای استفاده بعدی
    with open('main_session.json', 'w') as f:
        json.dump({'phone': phone, 'session': client.session.save()}, f)
    await event.respond("✅ وارد اکانت اصلی شدید. اکنون ربات برای شما اکانت‌های جدید می‌سازد.")

# ===========================
# ۳. شبیه‌سازی دستگاه‌های متعدد برای جلوگیری از فریز
# ===========================
def get_random_device():
    devices = [
        {'model': 'iPhone 14 Pro', 'system': 'iOS 16.5', 'lang': 'en'},
        {'model': 'Samsung Galaxy S23', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Google Pixel 7', 'system': 'Android 14', 'lang': 'en'},
        {'model': 'Xiaomi 13 Pro', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'OnePlus 11', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'iPhone 15 Pro Max', 'system': 'iOS 17.0', 'lang': 'en'},
    ]
    return random.choice(devices)

# ===========================
# ۴. دریافت پروکسی رایگان از سایت‌ها (لیست زنده)
# ===========================
def get_free_proxies():
    # نمونه از proxy-list.download
    try:
        r = requests.get('https://www.proxy-list.download/api/v1/get?type=http', timeout=5)
        proxies = r.text.split('\r\n')
        return [f'http://{p}' for p in proxies if p]
    except:
        return ['http://185.217.116.220:8080', 'http://45.77.91.75:8080']  # fallback

# ===========================
# ۵. ایجاد اکانت جدید با اطلاعات رندوم
# ===========================
def random_profile():
    first = random.choice(['Alex', 'Maria', 'John', 'Sara', 'Mike', 'Elena', 'David', 'Anna', 'Chris', 'Laura'])
    last = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'])
    username = f"{first.lower()}{random.randint(1000,9999)}"
    year = random.randint(1980, 2005)
    month = random.randint(1,12)
    day = random.randint(1,28)
    bio = "tgdnabot استارت کن 🔥"
    return {
        'first_name': first,
        'last_name': last,
        'username': username,
        'birthday': f"{year}-{month:02d}-{day:02d}",
        'bio': bio
    }

async def create_account(phone_number, proxy):
    # شبیه‌سازی دستگاه تصادفی
    device = get_random_device()
    client = PyroClient(
        f"session_{phone_number}",
        api_id=API_ID,
        api_hash=API_HASH,
        proxy=proxy,
        device_model=device['model'],
        system_version=device['system'],
        lang_code=device['lang']
    )
    await client.start()
    
    # دریافت کد از شماره (شما باید کد را از طریق اکانت اصلی دریافت کنید)
    # در اینجا فرض می‌کنیم کد به صورت دستی یا خودکار دریافت می‌شود
    code = input(f"کد تأیید برای {phone_number} را وارد کنید: ")
    await client.sign_in(phone_number, code)
    
    # تنظیم پروفایل رندوم
    profile = random_profile()
    await client.set_profile(
        first_name=profile['first_name'],
        last_name=profile['last_name'],
        bio=profile['bio']
    )
    # تنظیم یوزرنیم (در صورت موجود بودن)
    try:
        await client.set_username(profile['username'])
    except:
        pass
    
    # استارت بات tgdnabot
    await client.send_message('tgdnabot', '/start')
    
    # خروج از اکانت
    await client.log_out()
    return profile

# ===========================
# ۶. تابع اصلی اجرا (دستور شما)
# ===========================
async def main():
    # ۱. دریافت شماره از کاربر
    bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await start_button(event)
    
    @bot.on(events.Message)
    async def handle(event):
        if event.message.phone:
            await phone_handler(event)
        elif event.raw_text.startswith('ساخت اکانت'):
            # ۲. دریافت پروکسی رایگان
            proxies = get_free_proxies()
            # ۳. ایجاد چند دستگاه شبیه‌سازی شده
            for i in range(5):  # تعداد اکانت‌های مورد نظر
                proxy = random.choice(proxies)
                phone = f"+{random.randint(1,99)}{random.randint(100000000,999999999)}"
                profile = await create_account(phone, proxy)
                await event.respond(f"✅ اکانت ساخته شد:\n{profile}")
                time.sleep(2)  # جلوگیری از فریز
    
    print("ربات در حال اجرا است...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())