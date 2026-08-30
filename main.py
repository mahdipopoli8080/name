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
SERVICE_CODE = 'tg'  # Only Telegram service
# ================================================

# ==================== COUNTRY DATA ====================
COUNTRY_FLAGS = {
    '0':'🇷🇺','1':'🇺🇦','2':'🇰🇿','3':'🇺🇿','4':'🇵🇭','5':'🇮🇩','6':'🇮🇳','7':'🇺🇸',
    '8':'🇬🇧','9':'🇨🇳','10':'🇧🇷','11':'🇵🇰','12':'🇳🇬','13':'🇧🇩','14':'🇪🇬','15':'🇻🇳',
    '16':'🇲🇽','17':'🇹🇷','18':'🇩🇪','19':'🇫🇷','20':'🇮🇹','21':'🇪🇸','22':'🇰🇷','23':'🇯🇵',
    '24':'🇨🇦','25':'🇦🇺','26':'🇸🇦','27':'🇦🇪','28':'🇮🇷','29':'🇮🇶','30':'🇹🇭','31':'🇲🇾',
    '32':'🇸🇬','33':'🇿🇦','34':'🇰🇪','35':'🇬🇭','36':'🇨🇴','37':'🇦🇷','38':'🇨🇱','39':'🇵🇪',
    '40':'🇵🇱','41':'🇷🇴','42':'🇨🇿','43':'🇭🇺','44':'🇸🇪','45':'🇳🇴','46':'🇩🇰','47':'🇫🇮',
    '48':'🇮🇪','49':'🇵🇹','50':'🇬🇷','51':'🇧🇬','52':'🇭🇷','53':'🇷🇸','54':'🇺🇿','55':'🇰🇬',
    '56':'🇹🇯','57':'🇦🇲','58':'🇬🇪','59':'🇲🇩','60':'🇧🇾','61':'🇱🇹','62':'🇱🇻','63':'🇪🇪',
    '64':'🇲🇲','65':'🇰🇭','66':'🇱🇦','67':'🇳🇵','68':'🇱🇰','69':'🇦🇫','70':'🇹🇳','71':'🇩🇿',
    '72':'🇲🇦','73':'🇱🇾','74':'🇸🇩','75':'🇪🇹','76':'🇹🇿','77':'🇺🇬','78':'🇿🇲','79':'🇿🇼',
    '80':'🇧🇼','81':'🇲🇿','82':'🇦🇴','83':'🇨🇮','84':'🇸🇳','85':'🇲🇱','86':'🇧🇫','87':'🇳🇪',
    '88':'🇹🇩','89':'🇨🇲','90':'🇬🇳','91':'🇬🇲','92':'🇱🇷','93':'🇸🇱','94':'🇧🇮','95':'🇷🇼',
    '96':'🇸🇸','97':'🇪🇷','98':'🇩🇯','99':'🇸🇴','100':'🇲🇬','101':'🇲🇺','102':'🇸🇨','103':'🇨🇻',
    '104':'🇬🇼','105':'🇱🇸','106':'🇸🇿','107':'🇦🇩','108':'🇲🇨','109':'🇱🇮','110':'🇸🇲','111':'🇲🇹',
    '112':'🇨🇾','113':'🇮🇸','114':'🇱🇺','115':'🇧🇪','116':'🇳🇱','117':'🇦🇹','118':'🇨🇭','119':'🇱🇧',
    '120':'🇯🇴','121':'🇸🇾','122':'🇮🇱','123':'🇵🇸','124':'🇾🇪','125':'🇴🇲','126':'🇰🇼','127':'🇧🇭',
    '128':'🇶🇦','129':'🇲🇻','130':'🇧🇹','131':'🇧🇳','132':'🇹🇱','133':'🇫🇯','134':'🇵🇬','135':'🇸🇧',
    '136':'🇻🇺','137':'🇼🇸','138':'🇹🇴','139':'🇰🇮','140':'🇳🇷','141':'🇹🇻','142':'🇵🇼','143':'🇫🇲',
    '144':'🇲🇭',
}
COUNTRY_NAMES = {
    '0':'Russia','1':'Ukraine','2':'Kazakhstan','3':'Uzbekistan','4':'Philippines','5':'Indonesia',
    '6':'India','7':'USA','8':'UK','9':'China','10':'Brazil','11':'Pakistan','12':'Nigeria',
    '13':'Bangladesh','14':'Egypt','15':'Vietnam','16':'Mexico','17':'Turkey','18':'Germany',
    '19':'France','20':'Italy','21':'Spain','22':'South Korea','23':'Japan','24':'Canada',
    '25':'Australia','26':'Saudi Arabia','27':'UAE','28':'Iran','29':'Iraq','30':'Thailand',
    '31':'Malaysia','32':'Singapore','33':'South Africa','34':'Kenya','35':'Ghana','36':'Colombia',
    '37':'Argentina','38':'Chile','39':'Peru','40':'Poland','41':'Romania','42':'Czech',
    '43':'Hungary','44':'Sweden','45':'Norway','46':'Denmark','47':'Finland','48':'Ireland',
    '49':'Portugal','50':'Greece','51':'Bulgaria','52':'Croatia','53':'Serbia','54':'Uzbekistan',
    '55':'Kyrgyzstan','56':'Tajikistan','57':'Armenia','58':'Georgia','59':'Moldova','60':'Belarus',
    '61':'Lithuania','62':'Latvia','63':'Estonia','64':'Myanmar','65':'Cambodia','66':'Laos',
    '67':'Nepal','68':'Sri Lanka','69':'Afghanistan','70':'Tunisia','71':'Algeria','72':'Morocco',
    '73':'Libya','74':'Sudan','75':'Ethiopia','76':'Tanzania','77':'Uganda','78':'Zambia',
    '79':'Zimbabwe','80':'Botswana','81':'Mozambique','82':'Angola','83':'Ivory Coast',
    '84':'Senegal','85':'Mali','86':'Burkina Faso','87':'Niger','88':'Chad','89':'Cameroon',
    '90':'Guinea','91':'Gambia','92':'Liberia','93':'Sierra Leone','94':'Burundi','95':'Rwanda',
    '96':'South Sudan','97':'Eritrea','98':'Djibouti','99':'Somalia','100':'Madagascar',
    '101':'Mauritius','102':'Seychelles','103':'Cape Verde','104':'Guinea-Bissau','105':'Lesotho',
    '106':'Eswatini','107':'Andorra','108':'Monaco','109':'Liechtenstein','110':'San Marino',
    '111':'Malta','112':'Cyprus','113':'Iceland','114':'Luxembourg','115':'Belgium','116':'Netherlands',
    '117':'Austria','118':'Switzerland','119':'Lebanon','120':'Jordan','121':'Syria','122':'Israel',
    '123':'Palestine','124':'Yemen','125':'Oman','126':'Kuwait','127':'Bahrain','128':'Qatar',
    '129':'Maldives','130':'Bhutan','131':'Brunei','132':'Timor-Leste','133':'Fiji',
    '134':'Papua New Guinea','135':'Solomon Islands','136':'Vanuatu','137':'Samoa','138':'Tonga',
    '139':'Kiribati','140':'Nauru','141':'Tuvalu','142':'Palau','143':'Micronesia','144':'Marshall Islands',
}
# ========================================================

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('sms_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    c.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_id TEXT, phone TEXT, price REAL, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def get_balance(uid):
    conn = sqlite3.connect('sms_bot.db')
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id=?', (uid,))
    r = c.fetchone()
    if not r:
        c.execute('INSERT INTO users (user_id, balance) VALUES (?, 0.0)', (uid,))
        conn.commit(); conn.close()
        return 0.0
    conn.close()
    return r[0]

def update_balance(uid, amt):
    conn = sqlite3.connect('sms_bot.db')
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id=?', (uid,))
    if not c.fetchone():
        c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (uid, amt))
    else:
        c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

def save_order(uid, order_id, phone, price):
    conn = sqlite3.connect('sms_bot.db')
    conn.cursor().execute('INSERT INTO orders (user_id, order_id, phone, price, status) VALUES (?,?,?,?,?)', (uid, order_id, phone, price, 'active'))
    conn.commit(); conn.close()

def update_order_status(order_id, status):
    conn = sqlite3.connect('sms_bot.db')
    conn.cursor().execute('UPDATE orders SET status=? WHERE order_id=?', (status, order_id))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect('sms_bot.db')
    rows = conn.cursor().execute('SELECT user_id, balance FROM users').fetchall()
    conn.close(); return rows

def get_api_balance():
    """Get balance from SMSBower API"""
    import json
    try:
        # This is synchronous, we'll use aiohttp in async context
        pass
    except:
        pass
    return 0.0

init_db()
client = TelegramClient('sms_bot_session', API_ID, API_HASH)
user_state = {}
pending_receipts = {}

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

async def api_json(action, **params):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action}
    p.update(params)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_ENDPOINT, params=p, timeout=aiohttp.ClientTimeout(total=20)) as r:
                return await r.json(content_type=None)
    except:
        return None

# ==================== MAIN MENU ====================
def main_menu(uid):
    bal = get_balance(uid)
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
    await event.respond(main_text(event.sender_id), buttons=main_menu(event.sender_id))

@client.on(events.CallbackQuery(data=b"back"))
async def cb_back(event):
    await event.edit(main_text(event.sender_id), buttons=main_menu(event.sender_id))

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
    # Also get API balance
    api_bal = await api_call('getBalance')
    api_balance_str = ""
    if 'ACCESS_BALANCE' in api_bal:
        api_balance_str = f"\n\n🏦 SMSBower Balance: **{api_bal.split(':')[1]}$**"
    await event.edit(
        f"💰 **Balance**\n\n👤 Your: **{bal:.2f}$**{api_balance_str}",
        buttons=[[Button.inline("🔙 Back", b"back")]]
    )

# ==================== BUY NUMBER ====================
@client.on(events.CallbackQuery(data=b"buy"))
async def cb_buy(event):
    await event.edit(
        "🔢 **Buy Telegram Number**\n\n🌍 Select country:",
        buttons=[[Button.inline("🔄 Sync from API", b"sync_now")], [Button.inline("🔙 Back", b"back")]]
    )
    # Show countries from API
    data = await api_json('getPrices', service=SERVICE_CODE)
    if not data:
        await event.answer("⚠️ API error. Try again.", alert=True)
        return
    btns = []
    for ccode, svcs in data.items():
        if SERVICE_CODE in svcs:
            info = svcs[SERVICE_CODE]
            cost = info.get('cost', 0)
            count = info.get('count', 0)
            if cost > 0 and count > 0:
                flag = COUNTRY_FLAGS.get(str(ccode), '🌍')
                name = COUNTRY_NAMES.get(str(ccode), f'#{ccode}')
                sell = round(cost * 1.2, 2)  # 20% margin
                btns.append([Button.inline(f"{flag} {name} — ${sell:.2f} ({count})", f"buy:{ccode}:{sell}".encode())])
    if btns:
        btns.append([Button.inline("🔙 Back", b"back")])
        # Split into pages if too many
        if len(btns) > 10:
            btns = btns[:10] + [[Button.inline("🔙 Back", b"back")]]
        await event.edit("🔢 **Select Country:**", buttons=btns)
    else:
        await event.edit("⚠️ No numbers available.", buttons=[[Button.inline("🔙 Back", b"back")]])

@client.on(events.CallbackQuery(data=b"sync_now"))
async def cb_sync_now(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ Admin only!", alert=True)
        return
    await event.edit("⏳ **Syncing from API...**")
    data = await api_json('getPrices', service=SERVICE_CODE)
    if not data:
        await event.edit("❌ API error.", buttons=[[Button.inline("🔙 Back", b"back")]])
        return
    count = 0
    for ccode, svcs in data.items():
        if SERVICE_CODE in svcs:
            info = svcs[SERVICE_CODE]
            if info.get('cost', 0) > 0:
                count += 1
    await event.edit(f"✅ **Synced!** {count} countries found.", buttons=[[Button.inline("🔢 Buy", b"buy")], [Button.inline("🔙 Back", b"back")]])

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"buy:")))
async def cb_buy_country(event):
    parts = event.data.decode().split(':')
    ccode = parts[1]
    sell_price = float(parts[2])
    uid = event.sender_id
    bal = get_balance(uid)
    flag = COUNTRY_FLAGS.get(ccode, '🌍')
    name = COUNTRY_NAMES.get(ccode, f'#{ccode}')

    if bal < sell_price:
        await event.answer(f"❌ Need ${sell_price:.2f} but you have ${bal:.2f}", alert=True)
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
        f"Enter the code in Telegram, then tap **Get Code**.",
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
        update_order_status(order_id, 'completed')
        await event.edit(
            f"📩 **Code Received!**\n\n🔑 Code: `{code}`\n\n✅ Done!",
            buttons=[[Button.inline("🔢 Buy Another", b"buy")], [Button.inline("🔙 Menu", b"back")]]
        )
    elif 'STATUS_WAIT_CODE' in res:
        await event.answer("⏳ Waiting for SMS...", alert=True)
    elif 'STATUS_CANCEL' in res:
        await event.answer("❌ Order cancelled/expired.", alert=True)
        await event.edit("❌ Order expired.", buttons=[[Button.inline("🔙 Menu", b"back")]])
    else:
        await event.answer(f"Status: {res}", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cancel:")))
async def cb_cancel(event):
    parts = event.data.decode().split(':')
    order_id = parts[1]
    price = float(parts[2])
    uid = event.sender_id
    res = await api_call('setStatus', id=order_id, status='8')
    if 'ACCESS_CANCEL' in res or 'ACCESS_OK' in res:
        update_balance(uid, price)
        update_order_status(order_id, 'cancelled')
        await event.edit("✅ **Cancelled. Refunded.**", buttons=[[Button.inline("🔙 Menu", b"back")]])
    else:
        await event.answer("❌ Cannot cancel now.", alert=True)

# ==================== DEPOSIT ====================
@client.on(events.CallbackQuery(data=b"deposit"))
async def cb_deposit(event):
    pending_receipts[event.sender_id] = True
    await event.edit(
        "💳 **Manual Deposit**\n\n"
        "Transfer to:\n💳 `6037-0000-0000-0000`\n👤 Name: Admin\n\n"
        "Send receipt/screenshot here after transfer.",
        buttons=[[Button.inline("❌ Cancel", b"back")]]
    )

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and e.is_private))
async def msg_handler(event):
    uid = event.sender_id
    # Handle receipts
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
        await event.respond("✅ Receipt sent. Wait for admin approval.")
        return

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
    await event.edit(
        f"⚙️ **Admin Panel**\n\n"
        f"👥 Users: {len(users)}\n"
        f"💰 Total Balance: ${total_bal:.2f}",
        buttons=[
            [Button.inline("👥 Users", b"a_users"), Button.inline("📊 Stats", b"a_stats")],
            [Button.inline("💰 Balances", b"a_bals")],
            [Button.inline("🔙 Back", b"back")]
        ]
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
    total_bal = sum(b for _, b in users)
    # Get API balance
    api_res = await api_call('getBalance')
    api_bal = "N/A"
    if 'ACCESS_BALANCE' in api_res:
        api_bal = f"{api_res.split(':')[1]}$"
    await event.edit(
        f"📊 **Statistics**\n\n"
        f"👥 Users: {len(users)}\n"
        f"💰 User Balance: ${total_bal:.2f}\n"
        f"🏦 API Balance: {api_bal}\n"
        f"🤖 Status: Active ✅",
        buttons=[[Button.inline("🔙 Back", b"admin")]]
    )

# ==================== RUN ====================
async def main():
    print("🤖 Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Connected to Telegram!")
    print("📊 Syncing from API...")

    # Get API balance
    res = await api_call('getBalance')
    if 'ACCESS_BALANCE' in res:
        print(f"💰 API Balance: {res.split(':')[1]}$")

    # Get available countries count
    data = await api_json('getPrices', service=SERVICE_CODE)
    if data:
        count = sum(1 for c, s in data.items() if SERVICE_CODE in s and s[SERVICE_CODE].get('cost', 0) > 0)
        print(f"🌍 Available countries: {count}")

    print("✅ Bot ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
