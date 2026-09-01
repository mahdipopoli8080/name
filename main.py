import asyncio
import sqlite3
import aiohttp
from telethon import TelegramClient, events, Button

# ==================== CONFIG ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8766659658:AAGjRIsXi_4wzsa9P5ua6Izk6CTvDNK_OeY'
SMSBOWER_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_URL = 'https://smsbower.page/stubs/handler_api.php'
ADMIN_ID = 5190717598
# ================================================

# ==================== DB ====================
def db():
    return sqlite3.connect('sms_bot.db')

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, bal REAL DEFAULT 0.0)')
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        code TEXT PRIMARY KEY,
        name TEXT,
        flag TEXT,
        api_price REAL,
        sell_price REAL,
        providers TEXT DEFAULT ''
    )''')
    c.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, oid TEXT, phone TEXT, price REAL, status TEXT DEFAULT "active")')
    conn.commit(); conn.close()

def get_bal(uid):
    conn = db()
    r = conn.execute('SELECT bal FROM users WHERE uid=?', (uid,)).fetchone()
    conn.close()
    if r: return r[0]
    conn2 = db()
    conn2.execute('INSERT OR IGNORE INTO users (uid,bal) VALUES (?,0)', (uid,))
    conn2.commit(); conn2.close()
    return 0.0

def add_bal(uid, amt):
    conn = db()
    if conn.execute('SELECT 1 FROM users WHERE uid=?', (uid,)).fetchone():
        conn.execute('UPDATE users SET bal=bal+? WHERE uid=?', (amt, uid))
    else:
        conn.execute('INSERT INTO users (uid,bal) VALUES (?,?)', (uid, amt))
    conn.commit(); conn.close()

def save_order(uid, oid, phone, price):
    conn = db()
    conn.execute('INSERT INTO orders (uid,oid,phone,price) VALUES (?,?,?,?)', (uid, oid, phone, price))
    conn.commit(); conn.close()

def upd_order(oid, st):
    conn = db()
    conn.execute('UPDATE orders SET status=? WHERE oid=?', (st, oid))
    conn.commit(); conn.close()

def get_countries():
    conn = db()
    r = conn.execute('SELECT code,name,flag,api_price,sell_price,providers FROM countries ORDER BY name').fetchall()
    conn.close(); return r

def get_country(code):
    conn = db()
    r = conn.execute('SELECT name,flag,api_price,sell_price,providers FROM countries WHERE code=?', (code,)).fetchone()
    conn.close(); return r

def add_country(code, name, flag, api_p, sell_p, providers=''):
    conn = db()
    conn.execute('INSERT OR REPLACE INTO countries (code,name,flag,api_price,sell_price,providers) VALUES (?,?,?,?,?,?)', (code, name, flag, api_p, sell_p, providers))
    conn.commit(); conn.close()

def del_country(code):
    conn = db()
    conn.execute('DELETE FROM countries WHERE code=?', (code,))
    conn.commit(); conn.close()

def all_users():
    conn = db()
    r = conn.execute('SELECT uid,bal FROM users').fetchall()
    conn.close(); return r

# Migrate old DB: add providers column if missing
try:
    conn = db()
    conn.execute('ALTER TABLE countries ADD COLUMN providers TEXT DEFAULT ""')
    conn.commit(); conn.close()
except:
    pass

init_db()
client = TelegramClient('sms_bot', API_ID, API_HASH)
state = {}
receipts = set()
start_done = set()

# ==================== API ====================
async def api(action, **kw):
    p = {'api_key': SMSBOWER_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.text()
    except:
        return 'ERROR'

async def api_json(action, **kw):
    p = {'api_key': SMSBOWER_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=20)) as r:
                return await r.json(content_type=None)
    except:
        return None

# ==================== MENUS ====================
def menu(uid):
    btns = [
        [Button.inline("🔢 Buy Number", b"buy")],
        [Button.inline("💰 Balance", b"bal"), Button.inline("💳 Deposit", b"dep")],
        [Button.inline("👤 Profile", b"profile")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("⚙️ Admin", b"adm")])
    return btns

def menu_txt(uid):
    return f"👋 **Welcome!**\n\n🆔 `{uid}`\n💰 **{get_bal(uid):.2f}$**\n\nChoose:"

# ==================== START ====================
@client.on(events.NewMessage(pattern='/start'))
async def onStart(e):
    if e.sender_id in start_done: return
    start_done.add(e.sender_id)
    await e.respond(menu_txt(e.sender_id), buttons=menu(e.sender_id))

@client.on(events.CallbackQuery(data=b"back"))
async def onBack(e):
    start_done.add(e.sender_id)
    await e.edit(menu_txt(e.sender_id), buttons=menu(e.sender_id))

@client.on(events.CallbackQuery(data=b"profile"))
async def onProf(e):
    await e.edit(f"👤 **Profile**\n\n🆔 `{e.sender_id}`\n💰 **{get_bal(e.sender_id):.2f}$**", buttons=[[Button.inline("🔙 Back", b"back")]])

@client.on(events.CallbackQuery(data=b"bal"))
async def onBal(e):
    r = await api('getBalance')
    extra = f"\n🏦 API: **{r.split(':')[1]}$**" if 'ACCESS_BALANCE' in r else ""
    await e.edit(f"💰 **Balance**\n\n👤 You: **{get_bal(e.sender_id):.2f}$**{extra}", buttons=[[Button.inline("🔙 Back", b"back")]])

# ==================== BUY ====================
@client.on(events.CallbackQuery(data=b"buy"))
async def onBuy(e):
    cs = get_countries()
    if not cs:
        await e.edit("⚠️ No countries available.", buttons=[[Button.inline("🔙 Back", b"back")]])
        return
    btns = []
    for c, n, f, ap, sp, pr in cs:
        prov = f" ⭐" if pr else ""
        btns.append([Button.inline(f"{f} {n} — ${sp:.2f}{prov}", f"bc:{c}".encode())])
    btns.append([Button.inline("🔙 Back", b"back")])
    await e.edit("🔢 **Select Country:**\n\n⭐ = Custom providers", buttons=btns)

@client.on(events.CallbackQuery(data=b"top"))
async def onTop(e):
    if e.sender_id != ADMIN_ID:
        await e.answer("⛔ Admin only", alert=True); return
    await e.edit("⏳ **Fetching top providers...**")
    data = await api_json('getTopCountriesByService', service='tg')
    if not data:
        await e.edit("❌ API error", buttons=[[Button.inline("🔙 Back", b"buy")]])
        return
    txt = "🏆 **Top Providers (Telegram):**\n\n"
    for ccode, providers in list(data.items())[:10]:
        flag = COUNTRY_FLAGS.get(str(ccode), '🌍')
        name = COUNTRY_NAMES.get(str(ccode), f'#{ccode}')
        txt += f"{flag} **{name}:**\n"
        for pid, info in list(providers.items())[:3]:
            price = info.get('price', 0)
            count = info.get('count', 0)
            txt += f"  🏷️ ID: `{pid}` | ${price} | {count} pcs\n"
        txt += "\n"
    if len(txt) > 4000: txt = txt[:4000] + "..."
    await e.edit(txt, buttons=[[Button.inline("🔙 Back", b"buy")]])

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"bc:")))
async def onBuyC(e):
    code = e.data.decode().split(':')[1]
    uid = e.sender_id
    info = get_country(code)
    if not info:
        await e.answer("❌ Not found", alert=True); return
    name, flag, api_price, sell_price, providers = info
    if get_bal(uid) < sell_price:
        await e.answer(f"❌ Need ${sell_price:.2f}", alert=True); return
    await e.edit(f"⏳ **Getting number from {flag} {name}...**")
    # Build API params
    params = {'service': 'tg', 'country': code, 'maxPrice': str(api_price)}
    if providers:
        params['providerIds'] = providers
    r = await api('getNumberV2', **params)
    if 'ACCESS_NUMBER' not in r:
        r = await api('getNumber', **params)
    if 'ACCESS_NUMBER' not in r:
        await e.edit(f"⚠️ No number for {flag} {name}", buttons=[
            [Button.inline("🔄 Retry", f"bc:{code}".encode())],
            [Button.inline("🔙 Back", b"back")]
        ]); return
    parts = r.split(':')
    oid, phone = parts[1], parts[2]
    add_bal(uid, -sell_price)
    save_order(uid, oid, phone, sell_price)
    prov_txt = f"\n🏷️ Provider: `{providers}`" if providers else ""
    await e.edit(
        f"✅ **Number Ready!**\n\n"
        f"{flag} **{name}**\n"
        f"📱 `+{phone}`\n"
        f"🆔 `{oid}`\n"
        f"💰 ${sell_price:.2f}{prov_txt}\n\n"
        f"Enter code in Telegram, then tap **Get Code**.",
        buttons=[
            [Button.inline("📩 Get Code", f"sms:{oid}".encode())],
            [Button.inline("🔄 New Code", f"retry:{oid}".encode())],
            [Button.inline("❌ Cancel", f"cnl:{oid}:{sell_price}".encode())]
        ]
    )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"sms:")))
async def onSms(e):
    oid = e.data.decode().split(':')[1]
    r = await api('getStatus', id=oid)
    if 'STATUS_OK' in r:
        code = r.split(':')[1]
        await api('setStatus', id=oid, status='6')
        upd_order(oid, 'done')
        await e.edit(f"📩 **Code:** `{code}`\n\n✅ Done!", buttons=[
            [Button.inline("🔢 Buy Again", b"buy")], [Button.inline("🔙 Menu", b"back")]
        ])
    elif 'STATUS_WAIT_RETRY' in r:
        last = r.split(':')[1] if ':' in r else '?'
        await e.answer(f"⏳ Last: {last} — waiting next...", alert=True)
    elif 'STATUS_WAIT_CODE' in r:
        await e.answer("⏳ Waiting...", alert=True)
    elif 'STATUS_CANCEL' in r:
        await e.answer("❌ Expired", alert=True)
        await e.edit("❌ Expired.", buttons=[[Button.inline("🔙 Menu", b"back")]])
    else:
        await e.answer(r, alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"retry:")))
async def onRetry(e):
    oid = e.data.decode().split(':')[1]
    r = await api('setStatus', id=oid, status='3')
    if 'ACCESS_RETRY_GET' in r:
        await e.answer("🔄 New code requested!", alert=True)
    else:
        await e.answer(f"Status: {r}", alert=True)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cnl:")))
async def onCnl(e):
    _, oid, price = e.data.decode().split(':')
    price = float(price)
    r = await api('setStatus', id=oid, status='8')
    if 'ACCESS_CANCEL' in r or 'ACCESS_OK' in r:
        add_bal(e.sender_id, price)
        upd_order(oid, 'cancelled')
        await e.edit("✅ **Cancelled. Refunded.**", buttons=[[Button.inline("🔙 Menu", b"back")]])
    else:
        await e.answer("❌ Can't cancel (2min rule)", alert=True)

# ==================== DEPOSIT ====================
@client.on(events.CallbackQuery(data=b"dep"))
async def onDep(e):
    receipts.add(e.sender_id)
    await e.edit(
        "💳 **Deposit**\n\n💳 `6037-0000-0000-0000`\n👤 Admin\n\nSend receipt here.",
        buttons=[[Button.inline("❌ Cancel", b"back")]]
    )

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and e.is_private))
async def onMsg(e):
    uid = e.sender_id
    if uid in receipts:
        receipts.discard(uid)
        if e.photo or e.document:
            await e.forward_to(ADMIN_ID)
        else:
            await client.send_message(ADMIN_ID, f"📝 `{uid}`:\n{e.text}")
        btns = [
            [Button.inline("✅ $5", f"ap:{uid}:5".encode()), Button.inline("✅ $10", f"ap:{uid}:10".encode())],
            [Button.inline("✅ $20", f"ap:{uid}:20".encode()), Button.inline("✅ $50", f"ap:{uid}:50".encode())],
            [Button.inline("❌ Reject", f"rj:{uid}".encode())]
        ]
        await client.send_message(ADMIN_ID, f"📥 **Receipt** | `{uid}`", buttons=btns)
        await e.respond("✅ Sent. Wait for approval.")
        return
    # Admin text input
    if uid == ADMIN_ID and uid in state:
        s = state[uid]
        txt = e.raw_text.strip()
        if s == 'ac':
            state[uid] = {'s':'an','c':txt}
            await e.respond(f"✅ **Step 1:** Code `{txt}`\n\nStep 2: Country name:")
        elif isinstance(s, dict) and s.get('s') == 'an':
            state[uid] = {'s':'af','c':s['c'],'n':txt}
            await e.respond(f"✅ **Step 2:** {txt}\n\nStep 3: Flag emoji:")
        elif isinstance(s, dict) and s.get('s') == 'af':
            state[uid] = {'s':'ap','c':s['c'],'n':s['n'],'f':txt}
            await e.respond(f"✅ **Step 3:** {txt}\n\nStep 4: Max API price ($):")
        elif isinstance(s, dict) and s.get('s') == 'ap':
            state[uid] = {'s':'asp','c':s['c'],'n':s['n'],'f':s['f'],'ap':float(txt)}
            await e.respond(f"✅ **Step 4:** ${txt}\n\nStep 5: Your sell price ($):")
        elif isinstance(s, dict) and s.get('s') == 'asp':
            state[uid] = {'s':'apr','c':s['c'],'n':s['n'],'f':s['f'],'ap':s['ap'],'sp':float(txt)}
            await e.respond(
                f"✅ **Step 5:** ${txt}\n\n"
                f"**Step 6:** Provider IDs (optional)\n\n"
                f"Enter provider IDs separated by comma:\n"
                f"Example: `3193,4120`\n\n"
                f"Or type `skip` to use all providers."
            )
        elif isinstance(s, dict) and s.get('s') == 'apr':
            providers = '' if txt.lower() == 'skip' else txt
            add_country(s['c'], s['n'], s['f'], s['ap'], s['sp'], providers)
            profit = s['sp'] - s['ap']
            prov_txt = f"\n🏷️ Providers: `{providers}`" if providers else "\n🏷️ Providers: All"
            del state[uid]
            await e.respond(
                f"✅ **Country Added!**\n\n"
                f"{s['f']} {s['n']} (`{s['c']}`)\n"
                f"💰 API: ${s['ap']} → Sell: ${s['sp']}\n"
                f"💵 Profit: ${profit:.2f}{prov_txt}",
                buttons=[[Button.inline("⚙️ Admin", b"adm")]]
            )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"ap:")))
async def onApprove(e):
    if e.sender_id != ADMIN_ID: return
    _, uid, amt = e.data.decode().split(':')
    add_bal(int(uid), float(amt))
    await client.send_message(int(uid), f"✅ **${float(amt):.2f} deposited!**")
    await e.edit(f"✅ `{uid}` +${float(amt):.2f}")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"rj:")))
async def onReject(e):
    if e.sender_id != ADMIN_ID: return
    uid = int(e.data.decode().split(':')[1])
    await client.send_message(uid, "❌ **Rejected.**")
    await e.edit(f"❌ `{uid}` rejected")

# ==================== ADMIN ====================
@client.on(events.CallbackQuery(data=b"adm"))
async def onAdmin(e):
    if e.sender_id != ADMIN_ID: return
    us = all_users()
    cs = get_countries()
    tb = sum(b for _, b in us)
    r = await api('getBalance')
    ab = r.split(':')[1] + '$' if 'ACCESS_BALANCE' in r else 'N/A'
    await e.edit(
        f"⚙️ **Admin**\n\n"
        f"👥 Users: {len(us)}\n"
        f"💰 Total: ${tb:.2f}\n"
        f"🌍 Countries: {len(cs)}\n"
        f"🏦 API Balance: {ab}",
        buttons=[
            [Button.inline("🌍 Countries", b"ac_list"), Button.inline("➕ Add", b"ac_add")],
            [Button.inline("🏆 Top Providers", b"top")],
            [Button.inline("👥 Users", b"au"), Button.inline("📊 Stats", b"ast")],
            [Button.inline("💰 Balances", b"ab")],
            [Button.inline("🔙 Back", b"back")]
        ]
    )

@client.on(events.CallbackQuery(data=b"ac_list"))
async def onCList(e):
    if e.sender_id != ADMIN_ID: return
    cs = get_countries()
    if not cs:
        await e.edit("⚠️ Empty", buttons=[
            [Button.inline("➕ Add", b"ac_add")],
            [Button.inline("🔙 Back", b"adm")]
        ]); return
    txt = "🌍 **Countries:**\n\n"
    btns = []
    for c, n, f, ap, sp, pr in cs:
        profit = sp - ap
        prov = f" 🏷️{pr}" if pr else ""
        txt += f"{f} {n} (`{c}`) | ${ap} → ${sp} (+${profit:.2f}){prov}\n"
        btns.append([Button.inline(f"🗑️ {f} {n}", f"acd:{c}".encode())])
    btns += [[Button.inline("➕ Add", b"ac_add")], [Button.inline("🔙 Back", b"adm")]]
    if len(txt) > 4000: txt = txt[:4000] + "..."
    await e.edit(txt, buttons=btns)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"acd:")))
async def onCDel(e):
    if e.sender_id != ADMIN_ID: return
    del_country(e.data.decode().split(':')[1])
    await e.answer("✅ Deleted!")
    await onCList(e)

@client.on(events.CallbackQuery(data=b"ac_add"))
async def onCAdd(e):
    if e.sender_id != ADMIN_ID: return
    state[e.sender_id] = 'ac'
    await e.edit(
        "➕ **Add Country (6 Steps)**\n\n"
        "**Step 1:** Country code\n\n"
        "Common codes:\n"
        "`0` = 🇷🇺 Russia\n"
        "`7` = 🇺🇸 USA\n"
        "`8` = 🇬🇧 UK\n"
        "`17` = 🇹🇷 Turkey\n"
        "`18` = 🇩🇪 Germany\n"
        "`28` = 🇮🇷 Iran\n"
        "`6` = 🇮🇳 India",
        buttons=[[Button.inline("❌ Cancel", b"adm")]]
    )

@client.on(events.CallbackQuery(data=b"au"))
async def onUsers(e):
    if e.sender_id != ADMIN_ID: return
    us = all_users()
    txt = "👥 **Users:**\n\n" + "\n".join(f"🆔 `{u}` — ${b:.2f}" for u, b in us)
    if len(txt) > 4000: txt = txt[:4000] + "..."
    await e.edit(txt, buttons=[[Button.inline("🔙 Back", b"adm")]])

@client.on(events.CallbackQuery(data=b"ab"))
async def onBals(e):
    if e.sender_id != ADMIN_ID: return
    us = all_users()
    txt = "💰 **Balances:**\n\n" + "\n".join(f"🆔 `{u}` — **${b:.2f}**" for u, b in us)
    if len(txt) > 4000: txt = txt[:4000] + "..."
    await e.edit(txt, buttons=[[Button.inline("🔙 Back", b"adm")]])

@client.on(events.CallbackQuery(data=b"ast"))
async def onStats(e):
    if e.sender_id != ADMIN_ID: return
    us = all_users()
    cs = get_countries()
    tb = sum(b for _, b in us)
    r = await api('getBalance')
    ab = r.split(':')[1] + '$' if 'ACCESS_BALANCE' in r else 'N/A'
    total_profit = sum(sp - ap for _, _, _, ap, sp, _ in cs)
    avg = total_profit / len(cs) if cs else 0
    await e.edit(
        f"📊 **Stats**\n\n"
        f"👥 Users: {len(us)}\n"
        f"💰 Total: ${tb:.2f}\n"
        f"🌍 Countries: {len(cs)}\n"
        f"🏦 API: {ab}\n"
        f"💵 Avg Profit: ${avg:.2f}",
        buttons=[[Button.inline("🔙 Back", b"adm")]]
    )

# ==================== COUNTRY DATA ====================
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

# ==================== RUN ====================
async def main():
    print("🤖 Starting...")
    await client.start(bot_token=BOT_TOKEN)
    r = await api('getBalance')
    if 'ACCESS_BALANCE' in r: print(f"💰 API: {r.split(':')[1]}$")
    print("✅ Ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
