import asyncio
import random
import time
import json
import os
from telethon import TelegramClient, events, Button
from pyrogram import Client as PyroClient
import requests

# ===========================
# تنظیمات اولیه (از متغیرهای محیطی)
# ===========================
API_ID = int(os.getenv('API_ID', 8477522))
API_HASH = os.getenv('API_HASH', '366c19cf69e02cad530261ad81212a85')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8832756816:AAG2x7shLzKBmhAddJxizQfMxx7cXSk1Tpg')

# ===========================
# نام‌های رندوم جهانی
# ===========================
FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 
    'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara',
    'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah',
    'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra',
    'Donald', 'Donna', 'Steven', 'Carol', 'Paul', 'Ruth',
    'Andrew', 'Sharon', 'Joshua', 'Michelle', 'Kenneth', 'Laura',
    'Kevin', 'Sarah', 'Brian', 'Kimberly', 'George', 'Deborah',
    'Timothy', 'Linda', 'Ronald', 'Virginia', 'Edward', 'Martha',
    'Jason', 'Amanda', 'Jeffrey', 'Melissa', 'Ryan', 'Amy',
    'Jacob', 'Angela', 'Gary', 'Kathleen', 'Nicholas', 'Christina',
    'Eric', 'Debra', 'Jonathan', 'Rachel', 'Stephen', 'Carolyn',
    'Larry', 'Janet', 'Justin', 'Catherine', 'Scott', 'Maria',
    'Brandon', 'Heather', 'Benjamin', 'Diane', 'Samuel', 'Rebecca',
    'Gregory', 'Teresa', 'Frank', 'Julie', 'Alexander', 'Christine',
    'Raymond', 'Kathy', 'Patrick', 'Laura', 'Jack', 'Samantha',
    'Dennis', 'Joan', 'Jerry', 'Evelyn', 'Tyler', 'Judith',
    'Aaron', 'Megan', 'Jose', 'Cheryl', 'Nathan', 'Andrea',
    'Adam', 'Hannah', 'Henry', 'Jacqueline', 'Zachary', 'Gloria',
    'Tiffany', 'Doris', 'Kyle', 'Sara', 'Amelia', 'Harper',
    'Ethan', 'Ella', 'Noah', 'Avery', 'Liam', 'Abigail',
    'Mason', 'Emily', 'Logan', 'Ella', 'Lucas', 'Madison',
    'Jackson', 'Scarlett', 'Aiden', 'Victoria', 'Oliver', 'Aria',
    'Carter', 'Grace', 'Jayden', 'Chloe', 'Gabriel', 'Camila',
    'Hans', 'Greta', 'Klaus', 'Ingrid', 'Lars', 'Astrid',
    'Erik', 'Freya', 'Bjorn', 'Sigrid', 'Magnus', 'Hilda',
    'Sven', 'Britta', 'Olaf', 'Elsa', 'Pierre', 'Marie',
    'Jean', 'Claire', 'Philippe', 'Sophie', 'Andre', 'Camille',
    'Antonio', 'Lucia', 'Marco', 'Elena', 'Paolo', 'Francesca',
    'Giovanni', 'Alessandra', 'Carlos', 'Isabella', 'Javier', 'Valentina',
    'Miguel', 'Catalina', 'Santiago', 'Gabriela', 'William', 'Charlotte',
    'Henry', 'Amelia', 'George', 'Olivia', 'Edward', 'Emma',
    'Alexander', 'Sophia', 'James', 'Isabella', 'Charles', 'Mia',
    'Thomas', 'Evelyn', 'Heinrich', 'Ursula', 'Gunther', 'Helga',
    'Dieter', 'Inga', 'Wolfgang', 'Gisela', 'Dimitri', 'Anastasia',
    'Vladimir', 'Tatiana', 'Alexei', 'Natalia', 'Ivan', 'Olga',
    'Liam', 'Siobhan', 'Aidan', 'Caitlin', 'Conor', 'Niamh',
    'Finn', 'Maeve', 'Yuki', 'Haruki', 'Hana', 'Sora',
    'Kaito', 'Mei', 'Ren', 'Yuna', 'Wei', 'Li',
    'Jian', 'Mei', 'Chen', 'Yu', 'Lin', 'Xia',
    'Ji-hoon', 'Min-jun', 'Seo-yun', 'Ji-woo', 'Eun-ji', 'Ha-jun',
    'Yu-na', 'Seo-jun', 'Ahmed', 'Fatima', 'Mohammed', 'Aisha',
    'Hassan', 'Zara', 'Omar', 'Layla', 'Ali', 'Sara',
    'Ibrahim', 'Nadia', 'Adam', 'Hala', 'Youssef', 'Samira',
    'Rajan', 'Priya', 'Arjun', 'Ananya', 'Ravi', 'Ishita',
    'Vikram', 'Sneha', 'Chang', 'Jing', 'Qiang', 'Fang',
    'Shu', 'Ling', 'Wang', 'Yue', 'Amina', 'Kwame',
    'Zuri', 'Kofi', 'Ayo', 'Amara', 'Chidi', 'Nia',
    'Kwasi', 'Abena', 'Tunde', 'Adeola', 'Simba', 'Nelson',
    'Winnie', 'Trevor', 'Zanele', 'Sipho', 'Thandi', 'Lungile',
    'Mandla', 'Makena', 'Zawadi', 'Mosi', 'Kaya', 'Jelani',
    'Tuni', 'Kwanza', 'Eshe', 'Luis', 'Maria', 'Jose',
    'Ana', 'Juan', 'Carmen', 'Jorge', 'Luisa', 'Francisco',
    'Rosa', 'Antonio', 'Mercedes', 'Manuel', 'Teresa', 'Rafael',
    'Blanca', 'Carlos', 'Sofia', 'Pedro', 'Valeria', 'Mario',
    'Isabella', 'Miguel', 'Renata', 'Emilio', 'Lucia', 'Hector',
    'Catalina', 'Raul', 'Paloma', 'Arturo', 'Fernanda'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
    'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez',
    'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore',
    'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
    'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott',
    'Torres', 'Nguyen', 'Hill', 'Flores', 'Green', 'Adams',
    'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Turner', 'Phillips', 'Evans', 'Collins',
    'Edwards', 'Stewart', 'Morris', 'Murphy', 'Cook', 'Rogers',
    'Morgan', 'Peterson', 'Cooper', 'Reed', 'Muller', 'Schmidt',
    'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker',
    'Hoffmann', 'Schaefer', 'Koch', 'Bauer', 'Richter', 'Klein',
    'Wolf', 'Schroder', 'Neumann', 'Schwarz', 'Zimmermann', 'Kruger',
    'Lang', 'Kaiser', 'Huber', 'Schulze', 'Silva', 'Santos',
    'Rodrigues', 'Ferreira', 'Almeida', 'Costa', 'Oliveira', 'Pereira',
    'Lopes', 'Martins', 'Fernandes', 'Santana', 'Dias', 'Nunes',
    'Soares', 'Vieira', 'Molina', 'Ramos', 'Diaz', 'Vargas',
    'Castillo', 'Morales', 'Gutierrez', 'Ortiz', 'Wang', 'Li',
    'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhou',
    'Wu', 'Xu', 'Sun', 'Ma', 'Zhu', 'Hu',
    'Guo', 'Lin', 'He', 'Gao', 'Luo', 'Zheng',
    'Liang', 'Xie', 'Song', 'Tang', 'Kim', 'Lee',
    'Park', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon',
    'Chang', 'Lim', 'Shin', 'Ryu', 'Noh', 'Seo',
    'Kwak', 'Nam', 'Yamamoto', 'Tanaka', 'Suzuki', 'Takahashi',
    'Watanabe', 'Ito', 'Nakamura', 'Kobayashi', 'Sato', 'Kato',
    'Yoshida', 'Yamada', 'Sasaki', 'Ishikawa', 'Matsumoto', 'Inoue',
    'Ahmed', 'Ali', 'Hassan', 'Mohammed', 'Hussein', 'Ibrahim',
    'Aliyev', 'Khan', 'Ndlovu', 'Moyo', 'Khumalo', 'Dlamini',
    'Ngcobo', 'Dube', 'Zulu', 'Mthembu', 'Adebayo', 'Okafor',
    'Eze', 'Nwosu', 'Ogunleye', 'Adeyemi', 'Olatunji', 'Akinlade',
    'Asante', 'Mensah', 'Appiah', 'Owusu', 'Addo', 'Tetteh',
    'Boateng', 'Agyemang', 'Garcia', 'Lopez', 'Martinez', 'Sanchez',
    'Perez', 'Gomez', 'Rodriguez', 'Fernandez', 'Gonzalez', 'Diaz',
    'Martinez', 'Santiago', 'Lozano', 'Aguilar', 'Ortega', 'Vargas',
    'Castillo', 'Mendoza', 'Flores', 'Navarro', 'Morales', 'Cabrera',
    'Jimenez', 'Campos', 'Ivanov', 'Petrov', 'Sidorov', 'Kuznetsov',
    'Smirnov', 'Popov', 'Sokolov', 'Kozlov', 'Novikov', 'Morozov',
    'Volkov', 'Petrov', 'Vasiliev', 'Zaitsev', 'Mikhailov', 'Tikhonov',
    'Kowalski', 'Nowak', 'Wisniewski', 'Kowalczyk', 'Lewandowski', 'Szymanski',
    'Wozniak', 'Dabrowski', 'Johansson', 'Andersson', 'Karlsson', 'Nilsson',
    'Eriksson', 'Larsson', 'Olsson', 'Persson', 'Svensson', 'Gustafsson',
    'Jonsson', 'Pettersson', 'Bengtsson', 'Halvorsen', 'Christensen', 'Larsen',
    'Hansen', 'Pedersen', 'Andersen', 'Jensen', 'Nielsen', 'Sorensen',
    'Jorgensen', 'Petersen', 'Yilmaz', 'Demir', 'Kaya', 'Celik',
    'Arslan', 'Gunes', 'Yildiz', 'Ozturk', 'Aydin', 'Acar',
    'Korkmaz', 'Polat', 'Can', 'Kaplan', 'Ozer', 'Koc',
    'Kara', 'Gul', 'Sahin', 'Uzun', 'Dogan', 'Kaya',
    'Yavuz', 'Koyuncu'
]

# ===========================
# دکمه شیشه‌ای ارسال شماره
# ===========================
async def start_button(event):
    await event.respond(
        "📱 لطفاً شماره تلفن خود را با کد کشور وارد کنید:",
        buttons=[[Button.request_phone("📲 ارسال شماره", resize=True)]]
    )

# ===========================
# دریافت شماره و لاگین
# ===========================
async def phone_handler(event):
    phone = event.message.phone
    client = TelegramClient('session_main', API_ID, API_HASH)
    await client.start(phone=phone)
    with open('main_session.json', 'w') as f:
        json.dump({'phone': phone, 'session': client.session.save()}, f)
    await event.respond("✅ وارد اکانت اصلی شدید. ربات آماده ساخت اکانت‌های جدید است.")
    await event.respond("🔹 برای شروع ساخت اکانت، دستور `ساخت اکانت` را ارسال کنید.")

# ===========================
# شبیه‌سازی دستگاه
# ===========================
def get_random_device():
    devices = [
        {'model': 'iPhone 14 Pro', 'system': 'iOS 16.5', 'lang': 'en'},
        {'model': 'iPhone 15 Pro Max', 'system': 'iOS 17.0', 'lang': 'en'},
        {'model': 'Samsung Galaxy S23 Ultra', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Samsung Galaxy S24', 'system': 'Android 14', 'lang': 'en'},
        {'model': 'Google Pixel 8 Pro', 'system': 'Android 14', 'lang': 'en'},
        {'model': 'Google Pixel 7', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Xiaomi 13 Pro', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Xiaomi 14', 'system': 'Android 14', 'lang': 'en'},
        {'model': 'OnePlus 12', 'system': 'Android 14', 'lang': 'en'},
        {'model': 'OnePlus 11', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Huawei P60 Pro', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Sony Xperia 1 V', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Motorola Edge 40', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Nothing Phone 2', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Oppo Find X6 Pro', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Vivo X90 Pro', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Realme GT 3', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'Nokia X30', 'system': 'Android 13', 'lang': 'en'},
        {'model': 'MacBook Pro 2023', 'system': 'macOS 13.4', 'lang': 'en'},
        {'model': 'MacBook Air M2', 'system': 'macOS 14.0', 'lang': 'en'},
        {'model': 'iPad Pro 2023', 'system': 'iOS 17.0', 'lang': 'en'},
        {'model': 'Windows 11 PC', 'system': 'Windows 11', 'lang': 'en'},
        {'model': 'Windows 10 PC', 'system': 'Windows 10', 'lang': 'en'},
        {'model': 'Linux Ubuntu', 'system': 'Ubuntu 22.04', 'lang': 'en'},
        {'model': 'Chromebook', 'system': 'ChromeOS 118', 'lang': 'en'},
    ]
    return random.choice(devices)

# ===========================
# دریافت پروکسی
# ===========================
def get_free_proxies():
    proxies = []
    try:
        sources = [
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://www.sslproxies.org/?list=1',
            'https://www.us-proxy.org/?list=1',
            'https://www.socks-proxy.net/?list=1',
        ]
        for source in sources:
            try:
                r = requests.get(source, timeout=3)
                if r.status_code == 200:
                    lines = r.text.split('\r\n') if '\r\n' in r.text else r.text.split('\n')
                    for p in lines:
                        if ':' in p and len(p.split(':')) == 2:
                            proxies.append(f'http://{p}')
                    if proxies:
                        break
            except:
                continue
    except:
        pass
    
    if not proxies:
        proxies = [
            'http://185.217.116.220:8080',
            'http://45.77.91.75:8080',
            'http://159.253.145.252:8080',
            'http://51.89.255.69:80',
            'http://92.118.45.200:80',
            'http://80.209.255.27:80',
            'http://5.189.141.35:80',
            'http://188.132.215.71:80',
            'http://46.209.14.165:80',
            'http://82.96.44.80:80',
        ]
    return proxies

# ===========================
# ایجاد اکانت جدید
# ===========================
def random_profile():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    
    username_variations = [
        f"{first.lower()}{random.randint(100,9999)}",
        f"{first.lower()}{last.lower()}{random.randint(10,999)}",
        f"{last.lower()}{random.randint(1000,9999)}",
        f"{first.lower()}_{random.randint(100,999)}",
        f"{random.choice(['cool','real','super','mega','ultra','pro','love','heart','sweet'])}{first.lower()}{random.randint(10,99)}",
        f"{first.lower()}{random.choice(['_','.','-'])}{random.randint(100,999)}",
        f"{random.choice(['the','mr','ms','dr','love'])}{first.lower()}{random.randint(10,99)}",
        f"love_{first.lower()}{random.randint(10,99)}",
        f"heart_{first.lower()}{random.randint(10,99)}",
        f"sweet_{first.lower()}{random.randint(10,99)}",
    ]
    username = random.choice(username_variations)
    
    year = random.randint(1950, 2010)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    birthday = f"{year}-{month:02d}-{day:02d}"
    
    romantic_bios = [
        "عشق یعنی تو ❤️",
        "تنها تو کافی هستی 💕",
        "عشق من، زندگی من 🌹",
        "با تو کامل‌ام 💫",
        "تو رویای منی 🌙",
        "عاشقتم تا ابد 💖",
        "قلبم مال توست 💝",
        "تو بهترین اتفاق زندگی‌ام بودی 🌺",
        "عشق واقعی فقط یک بار اتفاق می‌افتد 💞",
        "با تو دنیا قشنگ‌تره 🌍",
        "تو خورشید منی ☀️",
        "هر روز عاشق‌تر می‌شوم 💗",
        "تو همیشه در قلبمی 💓",
        "عشق من، همه چیز من 🌹",
        "دوستت دارم بی‌نهایت ♾️",
        "تو تنها آرزوی منی ✨",
        "عشق یعنی نگاه تو 💘",
        "با تو حس خاصی دارم 🌸",
        "تو مال منی و من مال تو 💑",
        "عشق بی‌پایان به تو 💕",
        "همیشه عاشقتم 💖",
        "تو زیباترین اتفاقی 🦋",
        "عشق من همیشگیه 🌹",
        "با تو آرامشم 💆‍♂️",
        "تو دنیای منی 🌎",
        "فقط تو، فقط عشق 💕",
        "بهترین حس دنیا عشق توست 💞",
        "عاشقتم بدون هیچ دلیلی ❤️",
        "تو نگاه منی 👀",
        "تنها تو برای من کافی هستی 💝",
        "عشق یعنی بودن در کنار تو 🌹",
        "با تو هر لحظه قشنگه 💕",
        "تو تکه گمشده منی 🧩",
        "عاشقتم از ته قلب 💖",
        "تو همیشه در خاطراتمی 💭",
        "عشق تو روح منه 🌸",
        "با تو بهشت رو حس می‌کنم 🌹",
        "تو تنها عشق منی 💓",
        "هر روز عاشق‌تر از دیروز 💗",
        "عشق من، زندگی من، همه چیز من 💕",
        "با تو بودن بهترین حس دنیاست 💖",
        "عشق یعنی تو و من 💑",
        "تو قلب منی و من قلب تو ❤️",
        "هر ثانیه با تو عشق است 💕",
        "تنها تو می‌تونی منو کامل کنی 🌹",
        "عشق تو انرژی منه 🌟",
        "با تو هیچوقت تنها نیستم 💞",
        "تو رویاهای منی و من رویاهای تو 🌙",
        "عشق یعنی بودن در کنار هم 💝",
        "تو معنای واقعی عشقی ❤️",
        "دوستت دارم، همین و بس 💕",
        "با تو زندگی رنگین‌کمانه 🌈",
        "تو فرشته منی 😇",
        "عشق تو بزرگترین نعمت زندگی‌مه 🙏",
        "هر روز با تو زیباترین روزه 🌸",
        "tgdnabot استارت کن 🔥",
        "✨ tgdnabot رو شروع کن",
        "🚀 tgdnabot فعال کن",
        "💫 با tgdnabot شروع کن",
        "⚡ tgdnabot رو روشن کن",
        "🌟 tgdnabot استارت کن",
        "🔥 tgdnabot رو بزن",
        "💪 tgdnabot شروع کن",
        "🎯 tgdnabot کلیک کن",
        "🌈 tgdnabot رو امتحان کن",
        "🎮 tgdnabot بازی کن",
        "📱 tgdnabot باز کن",
        "🤖 tgdnabot اجرا کن",
        "💡 tgdnabot روشن کن",
        "⭐ tgdnabot ستاره کن",
    ]
    
    bio = random.choice(romantic_bios)
    
    return {
        'first_name': first,
        'last_name': last,
        'username': username,
        'birthday': birthday,
        'bio': bio,
        'full_name': f"{first} {last}"
    }

async def create_account(phone_number, proxy):
    device = get_random_device()
    client = PyroClient(
        f"session_{phone_number}",
        api_id=API_ID,
        api_hash=API_HASH,
        proxy={'http': proxy, 'https': proxy} if proxy else None,
        device_model=device['model'],
        system_version=device['system'],
        lang_code=device['lang']
    )
    await client.start()
    
    # در محیط واقعی، کد از طریق اکانت اصلی دریافت می‌شود
    code = input(f"📱 کد تأیید برای {phone_number} را وارد کنید: ")
    await client.sign_in(phone_number, code)
    
    profile = random_profile()
    
    try:
        await client.set_profile(
            first_name=profile['first_name'],
            last_name=profile['last_name'],
            bio=profile['bio']
        )
    except:
        pass
    
    try:
        await client.set_username(profile['username'])
    except:
        try:
            alt_username = f"{random.choice(['cool','real','super'])}{random.randint(1000,99999)}"
            await client.set_username(alt_username)
            profile['username'] = alt_username
        except:
            pass
    
    try:
        await client.send_message('tgdnabot', '/start')
    except:
        pass
    
    await client.log_out()
    return profile

# ===========================
# تابع اصلی (تصحیح‌شده)
# ===========================
async def main():
    # ✅ تصحیح: اضافه کردن await
    bot = await TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await start_button(event)
    
    @bot.on(events.Message)
    async def handle(event):
        if hasattr(event.message, 'phone') and event.message.phone:
            await phone_handler(event)
        
        elif event.raw_text.startswith('ساخت اکانت'):
            await event.respond("🔄 در حال دریافت پروکسی و ساخت اکانت‌های جدید...")
            
            proxies = get_free_proxies()
            if not proxies:
                await event.respond("⚠️ هیچ پروکسی موجود نیست! از پروکسی‌های پیش‌فرض استفاده می‌شود.")
                proxies = ['http://185.217.116.220:8080', 'http://45.77.91.75:8080']
            
            count = 5
            await event.respond(f"📊 شروع ساخت {count} اکانت جدید...")
            
            results = []
            for i in range(count):
                proxy = random.choice(proxies)
                phone = f"+{random.randint(1,99)}{random.randint(100000000,999999999)}"
                
                await event.respond(f"🔹 اکانت {i+1}/{count}: در حال ساخت شماره {phone}")
                
                try:
                    profile = await create_account(phone, proxy)
                    results.append(f"✅ {profile['full_name']} (@{profile['username']}) - {profile['birthday']}")
                    await event.respond(f"✅ اکانت {i+1} ساخته شد:\n{profile['full_name']}\n@{profile['username']}\n{profile['bio']}")
                except Exception as e:
                    results.append(f"❌ {phone}: خطا - {str(e)[:50]}")
                    await event.respond(f"❌ اکانت {i+1} با خطا مواجه شد: {str(e)[:50]}")
                
                time.sleep(random.randint(2, 5))
            
            await event.respond("✅ **عملیات ساخت اکانت به پایان رسید!**")
            await event.respond("\n".join(results))
    
    print("🤖 ربات در حال اجرا است...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
