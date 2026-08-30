import asyncio
import sqlite3
import aiohttp
from telethon import TelegramClient, events, Button

# ==================== CONFIG ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek'
SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_ENDPOINT = 'https://smsbower.page/stubs/handler_api.php'
ADMIN_ID = 5190717598
SERVICE_CODE = 'tg'
# ================================================

COUNTRY_FLAGS = {
    '0':'🇷🇺','1':'🇺🇦','2':'🇰🇿','4':'🇵🇭','5':'🇮🇩','6':'🇮🇳','7':'🇺🇸',
    '8':'🇬🇧','9':'🇨🇳','10':'🇧🇷','11':'🇵🇰','12':'🇳🇬','13':'🇧🇩','14':'🇪🇬','15':'🇻🇳',
    '16':'🇲🇽','17':'🇹🇷','18':'🇩🇪','19':'🇫🇷','20':'🇮🇹','21':'🇪🇸','22':'🇰🇷','23':'🇯🇵',
    '24':'🇨🇦','25':'🇦🇺','26':'🇸🇦','27':'🇦🇪','28':'🇮🇷','29':'🇮🇶','30':'🇹🇭','31':'🇲🇾',
    '32':'🇸🇬','33':'🇿🇦','34':'🇰🇪','35':'🇬🇭','36':'🇨🇴','37':'🇦🇷','38':'🇨🇱','39':'🇵🇪',
    '40':'🇵🇱','41':'🇷🇴','42':'🇨🇿','43':'🇭🇺','44':'🇸🇪','45':'🇳🇴','46':'🇩🇰','47':'🇫🇮',
    '48':'🇮🇪','49':'🇵🇹','50':'🇬🇷','51':'🇧🇬','52':'🇭🇷','53':'🇷🇸','55':'🇰🇬',
    '56':'🇹🇯','57':'🇦🇲','58':'🇬🇪','59':'🇲🇩','60':'🇧🇾','61':'🇱🇹','62':'🇱🇻','63':'🇪🇪',
    '64':'🇲🇲','65':'🇰🇭','66':'🇱🇦','67':'🇳🇵','68':'🇱🇰','69':'🇦🇫','70':'🇹🇳','71':'🇩🇿',
    '72':'🇲🇦','73':'🇱🇾','74':'🇸🇩','75':'🇪🇹','76':'🇹🇿','77':'🇺🇬','78':'🇿🇲','79':'🇿🇼',
    '80':'🇧🇼','81':'🇲🇿','82':'🇦🇴','83':'🇨🇮','84':'🇸🇳','85':'🇲🇱','86':'🇧🇫','87':'🇳🇪',
    '88':'🇹🇩','89':'🇨🇲','90':'🇬🇳','91':'🇬🇲','92':'🇱🇷','93':'🇸🇱','95':'🇷🇼',
    '96':'🇸🇸','97':'🇪🇷','98':'🇩🇯','99':'🇸🇴','100':'🇲🇬','101':'🇲🇺','103':'🇨🇻',
    '107':'🇦🇩','108':'🇲🇨','109':'🇱🇮','110':'🇸🇲','111':'🇲🇹','112':'🇨🇾','113':'🇮🇸',
    '114':'🇱🇺','115':'🇧🇪','116':'🇳🇱','117':'🇦🇹','118':'🇨🇭','119':'🇱🇧','120':'🇯🇴',
    '121':'🇸🇾','122':'🇮🇱','124':'🇾🇪','125':'🇴🇲','126':'🇰🇼','127':'🇧🇭','128':'🇶🇦',
    '129':'🇲🇻',
}
COUNTRY_NAMES = {
    '0':'Russia','1':'Ukraine','2':'Kazakhstan','4':'Philippines','5':'Indonesia',
    '6':'India','7':'USA','8':'UK','9':'China','10':'Brazil','11':'Pakistan','12':'Nigeria',
    '13':'Bangladesh','14':'Egypt','15':'Vietnam','16':'Mexico','17':'Turkey','18':'Germany',
    '19':'France','20':'Italy','21':'Spain','22':'South Korea','23':'Japan','24':'Canada',
    '25':'Australia','26':'Saudi Arabia','27':'UAE','28':'Iran','29':'Iraq','30':'Thailand',
    '31':'Malaysia','32':'Singapore','33':'South Africa','34':'Kenya','35':'Ghana','36':'Colombia',
    '37':'Argentina','38':'Chile','39':'Peru','40':'Poland','41':'Romania','42':'Czech',
    '43':'Hungary','44':'Sweden','45':'Norway','46':'Denmark','47':'Finland','48':'Ireland',
    '49':'Portugal','50':'Greece','51':'Bulgaria','52':'Croatia','53':'Serbia','55':'Kyrgyzstan',
    '56':'Tajikistan','57':'Armenia','58':'Georgia','59':'Moldova','60':'Belarus','61':'Lithuania',
    '62':'Latvia','63':'Estonia','64':'Myanmar','65':'Cambodia','66':'Laos','67':'Nepal',
    '68':'Sri Lanka','69':'Afghanistan','70':'Tunisia','71':'Algeria','72':'Morocco','73':'Libya',
    '74':'Sudan','75':'Ethiopia','76':'Tanzania','77':'Uganda','78':'Zambia','79':'Zimbabwe',
    '80':'Botswana','81':'Mozambique','82':'Angola','83':'Ivory Coast','84':'Senegal','85':'Mali',
    '86':'Burkina Faso','87':'Niger','88':'Chad','89':'Cameroon','90':'Guinea','91':'Gambia',
    '92':'Liberia','93':'Sierra Leone','95':'Rwanda','96':'South Sudan','97':'Eritrea','98':'Djibouti',
    '99':'Somalia','100':'Madagascar','101':'Mauritius','103':'Cape Verde','107':'Andorra',
    '108':'Monaco','109':'Liechtenstein','110':'San Marino','111':'Malta','112':'Cyprus',
    '113':'Iceland','114':'Luxembourg','115':'Belgium','116':'Netherlands','117':'Austria',
    '118':'Switzerland','119':'Lebanon','120':'Jordan','121':'Syria','122':'Israel','124':'Yemen',
    '125':'Oman','126':'Kuwait','127':'Bahrain','128':'Qatar','129':'Maldives',
}

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('sms_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    c.execute('CREATE TABLE IF NOT EXISTS countries (id INTEGER PRIMARY KEY AUTOINCREMENT, country_code TEXT UNIQUE, country_name TEXT, flag TEXT, api_price REAL, sell_price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_id TEXT, phone TEXT, price REAL, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit(); conn.close()

def db_conn():
    return sqlite3.connect('sms_bot.db')

def get_balance(uid):
    conn = db_conn()
    r = conn.cursor().execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    conn.close()
    if not r:
        conn2 = db_conn()
        conn2.cursor().execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0.0)', (uid,))
        conn2.commit(); conn2.close()
        return 0.0
    return r[0]

def update_balance(uid, amt):
    conn = db_conn()
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id=?', (uid,))
    if not c.fetchone():
        c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (uid, amt))
    else:
        c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

def get_countries():
    conn = db_conn()
    rows = conn.cursor().execute('SELECT country_code, country_name, flag, api_price, sell_price FROM countries ORDER BY country_name').fetchall()
    conn.close(); return rows

def add_country(code, name, flag, api_price, sell_price):
    conn = db_conn()
    conn.cursor().execute('INSERT OR REPLACE INTO countries (country_code, country_name, flag, api_price, sell_price) VALUES (?,?,?,?,?)', (code, name, flag, api_price, sell_price))
    conn.commit(); conn.close()

def remove_country(code):
    conn = db_conn()
    conn.cursor().execute('DELETE FROM countries WHERE country_code=?', (code,))
    conn.commit(); conn.close()

def get_country(code):
    conn = db_conn()
    r = conn.cursor().execute('SELECT country_name, flag, api_price, sell_price FROM countries WHERE country_code=?', (code,)).fetchone()
    conn.close(); return r

def save_order(uid, oid, phone, price):
    conn = db_conn()
    conn.cursor().execute('INSERT INTO orders (user_id, order_id, phone, price, status) VALUES (?,?,?,?,?)', (uid, oid, phone, price, 'active'))
    conn.commit(); conn.close()

def update_order(oid, status):
    conn = db_conn()
    conn.cursor().execute('UPDATE orders SET status=? WHERE order_id=?', (status, oid))
    conn.commit(); conn.close()

def get_all_users():
    conn = db_conn()
    rows = conn.cursor().execute('SELECT user_id, balance FROM users').fetchall()
    conn.close(); return rows

init_db()
client = TelegramClient('sms_bot_session', API_ID, API_HASH)
user_state = {}
pending_receipts = {}
started_users = set()  # Track who already got /start to prevent duplicate

# ==================== API ====================
async def api_call(action, **params):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action}
    p.update(params)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_ENDPOINT, params=p, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.text()
    except Exception as e:
        return f"ERROR:{e}"

# ==================== MAIN MENU ====================
def main_menu(uid):
    btns = [
        [Button.inline("🔢 Buy Number", b"buy")],
        [Button.inline("💰 Balance", b"bal"), Button.inline("💳 Deposit", b"deposit")],
        [Button.inline("👤 Profile", b"profile")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("⚙️ Admin Panel", b"admin")])
    return btns

def main_text(uid):
    bal = get_balance(uid)
    return (
        f"👋 **Welcome to Virtual Number Bot!**\n\n"
        f"🆔 Your ID: `{uid}`\n"
        f"💰 Balance: **{bal:.2f}$**\n\n"
        f"Select an option:"
    )

# ==================== USER HANDLERS ====================
@client.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    uid = event.sender_id
    # Prevent duplicate messages
    if uid in started_users:
        return
    started_users.add(uid)
    await event.respond(main_text(uid), buttons=main_menu(uid))

@client.on(events.CallbackQuery(data=b"back"))
async def cb_back(event):
    uid = event.sender_id
    await event.edit(main_text(uid), buttons=main_menu(uid))

@client.on(events.CallbackQuery(data=b"profile"))
async def cb_profile(event):
    uid = event.sender_id
    bal = get_balance(uid)
    await event.edit(
        f"👤 **Profile**\n\n🆔 `{uid}`\n💰 Balance: **{bal:.2f}$**",
        buttons=[[Button.inline("🔙 Back", b"back")]]
    )

@client.on(events.CallbackQuery(data=b"bal"))
async def cb_balance(event):
    uid = event.sender_id
    bal = get_balance(uid)
    api_res = await api_call('getBalance')
    api_str = ""
    if 'ACCESS_BALANCE' in api_res:
        api_str = f"\n\n🏦 API Balance: **{api_res.split(':')[1]}$**"
    await event.edit(
        f"💰 **Balance**\n\n👤 Your: **{bal:.2f}$**{api_str}",
        buttons=[[Button.inline("🔙 Back", b"back")]]
    )

# ==================== BUY NUMBER ====================
@client.on(events.CallbackQuery(data=b"buy"))
async def cb_buy(event):
    countries = get_countries()
    if not countries:
        await event.edit(
            "⚠️ No countries added yet.\nAsk admin to add countries.",
            buttons=[[Button.inline("🔙 Back", b"back")]]
        )
        return
    btns = []
    for code, name, flag, api_price, sell_price in countries:
        btns.append([Button.inline(f"{flag} {name} — ${sell_price:.2f}", f"buy:{code}:{sell_price}".encode())])
    btns.append([Button.inline("🔙 Back", b"back")])
    await event.edit("🔢 **Select Country:**", buttons=btns)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"buy:")))
async def cb_buy_country(event):
    parts = event.data.decode().split(':')
    ccode = parts[1]
    sell_price = float(parts[2])
    uid = event.sender_id
    bal = get_balance(uid)
    info = get_country(ccode)
    if not info:
        await event.answer("❌ Country not found.", alert=True)
        return
    name, flag = info[0], info[1]
    if bal < sell_price:
        await event.answer(f"❌ Need ${sell_price:.2f}", alert=True)
        return
    await event.edit(f"⏳ **Getting number from {flag} {name}...**")
    res = await api_call('getNumber', service=SERVICE_CODE, country=ccode)
    if 'ACCESS_NUMBER' not in res:
        await event.edit(
            f"⚠️ No number available for {flag} {name}",
            buttons=[[Button.inline("🔄 Retry", f"buy:{ccode}:{sell_price}".encode())], [Button.inline("🔙 Back", b"back")]]
        )
        return
    parts = res.split(':')
    order_id = parts[1]
    phone = parts[2]
    update_balance(uid, -sell_price)
    save_order(uid, order_id, phone, sell_price)
    await event.edit(
        f"✅ **Number Ready!**\n\n"
        f"{flag} **{name}**\n"
        f"📱 Phone: `+{phone}`\n"
        f"🆔 Order: `{order_id}`\n"
        f"💰 Paid: ${sell_price:.2f}\n\n"
        f"Enter code in Telegram, then tap **Get Code**.",
        buttons=[
            [Button.inline("📩 Get Code", f"sms:{order_id}".encode())],
            [Button.inline("❌ Cancel & Refund", f"cancel:{order_id}:{sell_price}".encode())]
        ]
    )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"sms:")))
async def cb_get_sms(event):
    order_id = event.data.decode().split(':')[1]
    res = await api_call('getStatus', id=order_id)
    if 'STATUS_OK' in res:
        code = res.split(':')[1]
        await api_call('setStatus', id=order_id, status='6')
        update_order(order_id, 'completed')
        await event.edit(
            f"📩 **Code Received!**\n\n🔑 Code: `{code}`\n\n✅ Done!",
            buttons=[[Button.inline("🔢 Buy Another", b"buy")], [Button.inline("🔙 Menu", b"back")]]
        )
    elif 'STATUS_WAIT_CODE' in res:
        await event.answer("⏳ Waiting for SMS...", alert=True)
    elif 'STATUS_CANCEL' in res:
        await event.answer("❌ Order expired.", alert=True)
    else:
        await event.answer(f"{res}", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cancel:")))
async def cb_cancel(event):
    parts = event.data.decode().split(':')
    order_id, price = parts[1], float(parts[2])
    uid = event.sender_id
    res = await api_call('setStatus', id=order_id, status='8')
    if 'ACCESS_CANCEL' in res or 'ACCESS_OK' in res:
        update_balance(uid, price)
        update_order(order_id, 'cancelled')
        await event.edit("✅ **Cancelled. Refunded.**", buttons=[[Button.inline("🔙 Menu", b"back")]])
    else:
        await event.answer("❌ Cannot cancel.", alert=True)

# ==================== DEPOSIT ====================
@client.on(events.CallbackQuery(data=b"deposit"))
async def cb_deposit(event):
    pending_receipts[event.sender_id] = True
    await event.edit(
        "💳 **Manual Deposit**\n\n"
        "Transfer to:\n💳 `6037-0000-0000-0000`\n👤 Name: Admin\n\n"
        "Send receipt/screenshot here.",
        buttons=[[Button.inline("❌ Cancel", b"back")]]
    )

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and e.is_private))
async def msg_handler(event):
    uid = event.sender_id
    if uid in pending_receipts:
        del pending_receipts[uid]
        if event.photo or event.document:
            await event.forward_to(ADMIN_ID)
        else:
            await client.send_message(ADMIN_ID, f"📝 From `{uid}`:\n\n{event.text}")
        btns = [
            [Button.inline("✅ $5", f"app:{uid}:5".encode()), Button.inline("✅ $10", f"app:{uid}:10".encode())],
            [Button.inline("✅ $20", f"app:{uid}:20".encode()), Button.inline("✅ $50", f"app:{uid}:50".encode())],
            [Button.inline("❌ Reject", f"rej:{uid}".encode())]
        ]
        await client.send_message(ADMIN_ID, f"📥 **New Receipt** | 👤 `{uid}`", buttons=btns)
        await event.respond("✅ Receipt sent. Wait for approval.")
        return
    # Handle admin text input states
    if uid == ADMIN_ID and uid in user_state:
        state = user_state[uid]
        text = event.raw_text.strip()
        if state == "add_code":
            user_state[uid] = {"step": "add_name", "code": text}
            await event.respond(f"✅ Code: `{text}`\n\nEnter country name:")
        elif isinstance(state, dict) and state.get("step") == "add_name":
            user_state[uid] = {"step": "add_flag", "code": state["code"], "name": text}
            await event.respond(f"✅ Name: {text}\n\nEnter flag emoji:")
        elif isinstance(state, dict) and state.get("step") == "add_flag":
            user_state[uid] = {"step": "add_api_price", "code": state["code"], "name": state["name"], "flag": text}
            await event.respond(f"✅ Flag: {text}\n\nEnter API price ($):")
        elif isinstance(state, dict) and state.get("step") == "add_api_price":
            user_state[uid] = {"step": "add_sell_price", "code": state["code"], "name": state["name"], "flag": state["flag"], "api_price": float(text)}
            await event.respond(f"✅ API Price: ${text}\n\nEnter sell price ($):")
        elif isinstance(state, dict) and state.get("step") == "add_sell_price":
            s = state
            add_country(s["code"], s["name"], s["flag"], s["api_price"], float(text))
            del user_state[uid]
            await event.respond(
                f"✅ **Country Added!**\n\n{s['flag']} {s['name']} (`{s['code']}`)\n💰 API: ${s['api_price']} | Sell: ${text}",
                buttons=[[Button.inline("⚙️ Admin", b"admin")]]
            )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"app:")))
async def cb_approve(event):
    if event.sender_id != ADMIN_ID: return
    parts = event.data.decode().split(':')
    uid, amt = int(parts[1]), float(parts[2])
    update_balance(uid, amt)
    await client.send_message(uid, f"✅ **Deposited ${amt:.2f}!**")
    await event.edit(f"✅ `{uid}` approved | ${amt:.2f}")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"rej:")))
async def cb_reject(event):
    if event.sender_id != ADMIN_ID: return
    uid = int(event.data.decode().split(':')[1])
    await client.send_message(uid, "❌ **Receipt rejected.**")
    await event.edit(f"❌ `{uid}` rejected")

# ==================== ADMIN PANEL ====================
@client.on(events.CallbackQuery(data=b"admin"))
async def cb_admin(event):
    if event.sender_id != ADMIN_ID: return
    users = get_all_users()
    total_bal = sum(b for _, b in users)
    countries = get_countries()
    await event.edit(
        f"⚙️ **Admin Panel**\n\n"
        f"👥 Users: {len(users)}\n"
        f"💰 Total Balance: ${total_bal:.2f}\n"
        f"🌍 Countries: {len(countries)}",
        buttons=[
            [Button.inline("🌍 Countries", b"a_countries"), Button.inline("➕ Add Country", b"a_add")],
            [Button.inline("👥 Users", b"a_users"), Button.inline("📊 Stats", b"a_stats")],
            [Button.inline("💰 Balances", b"a_bals")],
            [Button.inline("🔙 Back", b"back")]
        ]
    )

@client.on(events.CallbackQuery(data=b"a_countries"))
async def cb_a_countries(event):
    if event.sender_id != ADMIN_ID: return
    countries = get_countries()
    if not countries:
        await event.edit("⚠️ No countries.", buttons=[
            [Button.inline("➕ Add", b"a_add")],
            [Button.inline("🔙 Back", b"admin")]
        ])
        return
    text = "🌍 **Countries:**\n\n"
    btns = []
    for code, name, flag, api_price, sell_price in countries:
        text += f"{flag} {name} (`{code}`) | API: ${api_price} | Sell: ${sell_price}\n"
        btns.append([Button.inline(f"🗑️ {flag} {name}", f"a_del:{code}".encode())])
    btns.append([Button.inline("➕ Add Country", b"a_add")])
    btns.append([Button.inline("🔙 Back", b"admin")])
    if len(text) > 4000: text = text[:4000] + "..."
    await event.edit(text, buttons=btns)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"a_del:")))
async def cb_a_del(event):
    if event.sender_id != ADMIN_ID: return
    code = event.data.decode().split(':')[1]
    remove_country(code)
    await event.answer("✅ Removed!")
    await cb_a_countries(event)

@client.on(events.CallbackQuery(data=b"a_add"))
async def cb_a_add(event):
    if event.sender_id != ADMIN_ID: return
    user_state[event.sender_id] = "add_code"
    await event.edit(
        "➕ **Add Country**\n\nStep 1: Country code (e.g. `7` for USA, `0` for Russia)",
        buttons=[[Button.inline("❌ Cancel", b"admin")]]
    )

@client.on(events.CallbackQuery(data=b"a_users"))
async def cb_a_users(event):
    if event.sender_id != ADMIN_ID: return
    users = get_all_users()
    text = "👥 **Users:**\n\n"
    for uid, bal in users:
        text += f"🆔 `{uid}` | ${bal:.2f}\n"
    if len(text) > 4000: text = text[:4000] + "..."
    await event.edit(text, buttons=[[Button.inline("🔙 Back", b"admin")]])

@client.on(events.CallbackQuery(data=b"a_bals"))
async def cb_a_bals(event):
    if event.sender_id != ADMIN_ID: return
    users = get_all_users()
    text = "💰 **Balances:**\n\n"
    for uid, bal in users:
        text += f"🆔 `{uid}` — **${bal:.2f}**\n"
    if len(text) > 4000: text = text[:4000] + "..."
    await event.edit(text, buttons=[[Button.inline("🔙 Back", b"admin")]])

@client.on(events.CallbackQuery(data=b"a_stats"))
async def cb_a_stats(event):
    if event.sender_id != ADMIN_ID: return
    users = get_all_users()
    countries = get_countries()
    total_bal = sum(b for _, b in users)
    api_res = await api_call('getBalance')
    api_bal = "N/A"
    if 'ACCESS_BALANCE' in api_res:
        api_bal = f"{api_res.split(':')[1]}$"
    await event.edit(
        f"📊 **Statistics**\n\n"
        f"👥 Users: {len(users)}\n"
        f"💰 User Balance: ${total_bal:.2f}\n"
        f"🌍 Countries: {len(countries)}\n"
        f"🏦 API Balance: {api_bal}\n"
        f"🤖 Status: Active ✅",
        buttons=[[Button.inline("🔙 Back", b"admin")]]
    )

# ==================== RUN ====================
async def main():
    print("🤖 Starting...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Connected!")
    res = await api_call('getBalance')
    if 'ACCESS_BALANCE' in res:
        print(f"💰 API Balance: {res.split(':')[1]}$")
    print("✅ Bot ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
