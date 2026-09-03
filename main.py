import asyncio
import sqlite3
import time
import random
import aiohttp
from telethon import TelegramClient, events, Button
from telethon.sessions import MemorySession
from telethon.errors import MessageNotModifiedError

# ==================== CONFIG ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8873527644:AAFwK1OYPDcZu-jQgsghcn_ID4KJzHdhwgc'
ADMIN_ID = 5190717598
SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_URL = 'https://smsbower.page/stubs/handler_api.php'
# ================================================

# ==================== FAKE NAMES API ====================
async def get_fake_name():
    """Get a random fake name from multiple sources"""
    sources = [
        'https://api.namefake.com/',
        'https://randomuser.me/api/',
    ]
    # Try randomuser.me
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get('https://randomuser.me/api/?nat=us,gb,ru,de', timeout=aiohttp.ClientTimeout(total=5)) as r:
                data = await r.json()
                if 'results' in data and data['results']:
                    u = data['results'][0]
                    first = u['name']['first'].title()
                    last = u['name']['last'].title()
                    return f"{first} {last}"
    except: pass
    # Fallback: random from list
    first_names = ['James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','David','Elizabeth','William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Christopher','Karen','Charles','Lisa','Daniel','Nancy','Matthew','Betty','Anthony','Margaret','Mark','Sandra','Donald','Ashley','Steven','Kimberly','Paul','Emily','Andrew','Donna','Joshua','Michelle']
    last_names = ['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin','Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson','Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores']
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# ==================== DB ====================
def get_db():
    return sqlite3.connect("shop.db", timeout=15)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT NOT NULL,
        name TEXT,
        flag TEXT,
        provider_ids TEXT DEFAULT '',
        price REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_id TEXT UNIQUE,
        phone TEXT,
        country_name TEXT,
        price REAL,
        status TEXT DEFAULT 'WAITING',
        created_at INTEGER
    )''')
    conn.commit(); conn.close()

def get_balance(uid):
    conn = get_db()
    r = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    if r:
        conn.close(); return r[0]
    conn.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn.commit(); conn.close()
    return 0.0

def add_balance(uid, amt):
    conn = get_db()
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

def create_user(uid):
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn.commit(); conn.close()

def all_users():
    conn = get_db()
    rows = conn.execute('SELECT user_id, balance FROM users ORDER BY balance DESC').fetchall()
    conn.close(); return rows

init_db()

client = TelegramClient(MemorySession(), API_ID, API_HASH)
admin_states = {}
user_states = {}
auto_check_tasks = {}
PROCESSED_EVENTS = set()

def is_duplicate(evt_key):
    if evt_key in PROCESSED_EVENTS:
        return True
    PROCESSED_EVENTS.add(evt_key)
    if len(PROCESSED_EVENTS) > 10000:
        PROCESSED_EVENTS.clear()
    return False

# ==================== API ====================
async def api(action, **kw):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=15)) as r:
                res = await r.text()
                return res.strip() if res else 'ERROR'
    except Exception:
        return 'ERROR'

# ==================== BUTTONS ====================
def main_buttons(uid):
    btns = [
        [Button.inline("🛒 Buy Telegram", b"buy_tg"), Button.inline("👤 Account", b"my_account")],
        [Button.inline("📋 Active Orders", b"active_orders")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("⚙️ Admin Panel", b"admin_panel")])
    return btns

def main_text(uid):
    bal = get_balance(uid)
    return f"👋 **Welcome!**\n\n💳 Balance: **${bal:.2f}**\n⚡ Service: **Telegram**\n\nChoose:"

def admin_buttons():
    return [
        [Button.inline("➕ Add Country", b"adm_add_c"), Button.inline("📋 Countries", b"adm_list_c")],
        [Button.inline("➕ Add Balance", b"adm_add_b"), Button.inline("➖ Sub Balance", b"adm_sub_b")],
        [Button.inline("👥 User Balances", b"adm_balances")],
        [Button.inline("🔙 Main Menu", b"back_main")]
    ]

# ==================== RETRY GET NUMBER ====================
async def retry_get_number(c_code, provider_ids, max_retries=10, delay=2):
    """Try multiple times to get a number from the API"""
    params = {'service': 'tg', 'country': c_code}
    if provider_ids:
        params['providerIds'] = provider_ids
    for attempt in range(max_retries):
        res = await api('getNumber', **params)
        if res.startswith('ACCESS_NUMBER'):
            parts = res.split(':')
            return True, parts[1], parts[2]
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    return False, None, None

# ==================== AUTO CHECK SMS ====================
async def auto_check_sms(uid, order_id, phone):
    try:
        for _ in range(120):
            await asyncio.sleep(3)
            conn = get_db()
            r = conn.execute('SELECT status FROM orders WHERE order_id=?', (order_id,)).fetchone()
            conn.close()
            if not r or r[0] != 'WAITING':
                return

            status = await api('getStatus', id=order_id)
            if status.startswith('STATUS_OK'):
                parts = status.split(':')
                code = parts[1] if len(parts) > 1 else 'RECEIVED'
                await api('setStatus', id=order_id, status='6')

                conn = get_db()
                conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                auto_check_tasks.pop(order_id, None)

                # Get fake name for display
                fake_name = await get_fake_name()
                try:
                    await client.send_message(uid,
                        f"🎉 **Code Received!**\n\n"
                        f"📱 Phone: `+{phone}`\n"
                        f"👤 **{fake_name}**\n"
                        f"🔑 Code: `{code}`\n\n✅ Done!",
                        buttons=[[Button.inline("📋 Active Orders", b"active_orders")], [Button.inline("🔙 Menu", b"back_main")]])
                except: pass
                return

            elif status.startswith('STATUS_CANCEL'):
                conn = get_db()
                row = conn.execute("SELECT price, status FROM orders WHERE order_id=?", (order_id,)).fetchone()
                if row and row[1] == 'WAITING':
                    conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
                    conn.commit()
                    add_balance(uid, row[0])
                    try:
                        await client.send_message(uid,
                            f"❌ **Order Expired/Cancelled**\n📱 `+{phone}`\n💵 ${row[0]:.2f} refunded.",
                            buttons=[[Button.inline("🔙 Menu", b"back_main")]])
                    except: pass
                conn.close()
                auto_check_tasks.pop(order_id, None)
                return
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Auto check error: {e}")

# ==================== BATCH BUY ====================
async def process_batch_purchase(event, uid, cid, count):
    conn = get_db()
    row = conn.execute("SELECT country_code, name, flag, provider_ids, price FROM countries WHERE id=?", (cid,)).fetchone()
    if not row:
        conn.close(); await event.respond("❌ Country not found."); return
    c_code, name, flag, provider_ids, price = row
    total_cost = price * count

    bal_row = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    bal = bal_row[0] if bal_row else 0.0
    conn.close()

    if bal < total_cost:
        await event.respond(f"❌ Need **${total_cost:.2f}** (You have **${bal:.2f}**)")
        return

    progress_msg = await event.respond(f"⏳ Ordering {count}x {flag} {name}...")

    successful = 0
    created_orders = []

    for i in range(count):
        # Retry up to 5 times per number
        for attempt in range(5):
            params = {'service': 'tg', 'country': c_code}
            if provider_ids:
                params['providerIds'] = provider_ids
            res = await api('getNumber', **params)
            if res.startswith('ACCESS_NUMBER'):
                parts = res.split(':')
                order_id, phone = parts[1], parts[2]
                add_balance(uid, -price)

                conn = get_db()
                conn.execute(
                    "INSERT INTO orders (user_id, order_id, phone, country_name, price, status, created_at) VALUES (?,?,?,?,?,'WAITING',?)",
                    (uid, order_id, phone, name, price, int(time.time())))
                conn.commit(); conn.close()

                task = asyncio.create_task(auto_check_sms(uid, order_id, phone))
                auto_check_tasks[order_id] = task
                successful += 1
                created_orders.append((order_id, phone))
                break
            else:
                await asyncio.sleep(2)
        await asyncio.sleep(0.5)

    if successful == 0:
        await progress_msg.edit(
            f"⚠️ No numbers available for {flag} {name}.",
            buttons=[[Button.inline("🔄 Retry", f"buy_c_{cid}".encode())], [Button.inline("🔙 Back", b"back_main")]])
        return

    lines = [f"📱 `+{p}` (ID: `{o}`)" for o, p in created_orders]
    summary = (
        f"✅ **{successful}/{count} Numbers!**\n\n"
        f"🌍 {flag} **{name}**\n💵 Deducted: **${(successful * price):.2f}**\n\n"
        + "\n".join(lines) + "\n\n⏳ Auto-checking SMS...")
    await progress_msg.edit(summary, buttons=[
        [Button.inline("📋 Active Orders", b"active_orders")],
        [Button.inline("❌ Cancel All", b"cnc_all")]])

# ==================== START ====================
@client.on(events.NewMessage(pattern=r'^/start$', incoming=True, func=lambda e: e.is_private))
async def cmd_start(event):
    if is_duplicate(f"start_{event.id}"): return
    uid = event.sender_id
    create_user(uid)
    user_states.pop(uid, None)
    user = await event.get_sender()
    name = user.first_name if user and user.first_name else "User"
    bal = get_balance(uid)
    await event.respond(
        f"👋 **Hello {name}!**\n\n💳 Balance: **${bal:.2f}**\n⚡ Service: **Telegram**\n\nChoose:",
        buttons=main_buttons(uid))

# ==================== CALLBACK ROUTER ====================
@client.on(events.CallbackQuery)
async def callback_router(event):
    query_id = getattr(event.query, 'id', None)
    if query_id and is_duplicate(f"q_{query_id}"):
        await event.answer(); return

    uid = event.sender_id
    try: data = event.data.decode()
    except: await event.answer(); return

    try:
        if data == "back_main":
            admin_states.pop(uid, None); user_states.pop(uid, None)
            await event.edit(main_text(uid), buttons=main_buttons(uid))

        elif data == "my_account":
            bal = get_balance(uid)
            await event.edit(f"👤 **Account**\n\n🆔 `{uid}`\n💰 **${bal:.2f}**",
                buttons=[[Button.inline("🔙 Back", b"back_main")]])

        elif data == "buy_tg":
            conn = get_db()
            rows = conn.execute("SELECT id, name, flag, price FROM countries ORDER BY id").fetchall()
            conn.close()
            if not rows:
                await event.answer("⚠️ No countries.", alert=True); return
            btns = [[Button.inline(f"{f} {n} — ${p:.2f}", f"buy_c_{i}".encode())] for i, n, f, p in rows]
            btns.append([Button.inline("🔙 Back", b"back_main")])
            await event.edit("🌍 **Select Country:**", buttons=btns)

        elif data.startswith("buy_c_"):
            cid = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT name, flag, price FROM countries WHERE id=?", (cid,)).fetchone()
            conn.close()
            if not row:
                await event.answer("Not found", alert=True); return
            name, flag, price = row
            btns = [
                [Button.inline("1x", f"qty_{cid}_1".encode()), Button.inline("2x", f"qty_{cid}_2".encode()), Button.inline("3x", f"qty_{cid}_3".encode())],
                [Button.inline("5x", f"qty_{cid}_5".encode()), Button.inline("✏️ Custom", f"custom_qty_{cid}".encode())],
                [Button.inline("🔙 Back", b"buy_tg")]]
            await event.edit(f"🌍 **{flag} {name}**\n💵 Price: **${price:.2f}**\n\nQuantity:", buttons=btns)

        elif data.startswith("qty_"):
            parts = data.split("_")
            cid, qty = parts[1], int(parts[2])
            await event.answer()
            await process_batch_purchase(event, uid, cid, qty)

        elif data.startswith("custom_qty_"):
            cid = data.split("_")[2]
            user_states[uid] = {"step": "custom_qty", "cid": cid}
            await event.edit("✏️ Send quantity (1-50):", buttons=[[Button.inline("🔙 Cancel", b"buy_tg")]])

        elif data.startswith("chk_sms_"):
            order_id = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT status, phone FROM orders WHERE order_id=?", (order_id,)).fetchone()
            conn.close()
            if not row:
                await event.answer("Not found", alert=True); return
            status = await api('getStatus', id=order_id)
            if status.startswith('STATUS_OK'):
                parts = status.split(':')
                code = parts[1] if len(parts) > 1 else 'RECEIVED'
                await api('setStatus', id=order_id, status='6')
                conn = get_db()
                conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                if order_id in auto_check_tasks:
                    auto_check_tasks[order_id].cancel(); del auto_check_tasks[order_id]
                fake_name = await get_fake_name()
                await event.respond(
                    f"🎉 **Code Received!**\n\n📱 `+{row[1]}`\n👤 **{fake_name}**\n🔑 Code: `{code}`\n\n✅ Done!",
                    buttons=[[Button.inline("📋 Active Orders", b"active_orders")], [Button.inline("🔙 Menu", b"back_main")]])
            elif status == 'STATUS_WAIT_CODE':
                await event.answer("⏳ Waiting...", alert=True)
            elif status == 'STATUS_CANCEL':
                await event.answer("❌ Expired", alert=True)
            else:
                await event.answer(f"{status[:50]}", alert=True)

        elif data.startswith("cnc_ord_"):
            order_id = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT price, status FROM orders WHERE order_id=? AND user_id=?", (order_id, uid)).fetchone()
            if not row or row[1] != 'WAITING':
                conn.close(); await event.answer("❌ Cannot cancel", alert=True); return
            if order_id in auto_check_tasks:
                auto_check_tasks[order_id].cancel(); del auto_check_tasks[order_id]
            res = await api('setStatus', id=order_id, status='8')
            if any(x in res for x in ['ACCESS_CANCEL', 'ACCESS_OK', 'STATUS_CANCEL', 'CANCEL']):
                conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                add_balance(uid, row[0])
                await event.answer(f"✅ Refunded ${row[0]:.2f}", alert=True)
                await show_active_orders(event, uid)
            else:
                conn.close(); await event.answer(f"❌ {res[:50]}", alert=True)

        elif data == "cnc_all":
            conn = get_db()
            active = conn.execute("SELECT order_id, price FROM orders WHERE user_id=? AND status='WAITING'", (uid,)).fetchall()
            conn.close()
            if not active:
                await event.answer("No active orders.", alert=True); return
            total = 0.0; cnt = 0
            for oid, price in active:
                if oid in auto_check_tasks:
                    auto_check_tasks[oid].cancel(); del auto_check_tasks[oid]
                res = await api('setStatus', id=oid, status='8')
                if any(x in res for x in ['ACCESS_CANCEL', 'ACCESS_OK', 'CANCEL']):
                    conn2 = get_db()
                    conn2.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (oid,))
                    conn2.commit(); conn2.close()
                    total += price; cnt += 1
                await asyncio.sleep(0.3)
            add_balance(uid, total)
            await event.edit(f"✅ **{cnt} Cancelled!**\n💵 Refunded: **${total:.2f}**\n\n{main_text(uid)}",
                buttons=main_buttons(uid))

        elif data == "active_orders":
            await show_active_orders(event, uid)

        # ==================== ADMIN ====================
        elif data == "admin_panel" and uid == ADMIN_ID:
            admin_states.pop(uid, None)
            await event.edit("⚙️ **Admin Panel**", buttons=admin_buttons())

        elif data == "adm_add_c" and uid == ADMIN_ID:
            admin_states[uid] = {"step": 1, "data": {}}
            await event.edit("**Step 1:** Country code\n(e.g. `0` = Russia, `7` = USA)",
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])

        elif data == "adm_list_c" and uid == ADMIN_ID:
            conn = get_db()
            rows = conn.execute("SELECT id, name, flag, country_code, price, provider_ids FROM countries").fetchall()
            conn.close()
            if not rows:
                await event.answer("No countries.", alert=True); return
            txt = "🌍 **Countries:**\n\n"
            btns = []
            for cid, name, flag, code, price, prov in rows[:30]:
                p = f" 🏷️{prov}" if prov else ""
                txt += f"{flag} {name} (`{code}`) | ${price:.2f}{p}\n"
                btns.append([Button.inline(f"🗑️ {flag} {name}", f"del_c_{cid}".encode())])
            btns.append([Button.inline("🔙 Back", b"admin_panel")])
            await event.edit(txt[:3900], buttons=btns)

        elif data.startswith("del_c_") and uid == ADMIN_ID:
            cid = data.split("_")[2]
            conn = get_db()
            conn.execute("DELETE FROM countries WHERE id=?", (cid,))
            conn.commit(); conn.close()
            await event.answer("✅ Deleted!")
            await event.edit("⚙️ **Admin Panel**", buttons=admin_buttons())

        elif data in ["adm_add_b", "adm_sub_b"] and uid == ADMIN_ID:
            is_add = (data == "adm_add_b")
            admin_states[uid] = {"step": "balance", "is_add": is_add}
            await event.edit(f"**{'Add' if is_add else 'Sub'} Balance**\n\nSend: `user_id amount`",
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])

        elif data == "adm_balances" and uid == ADMIN_ID:
            users = all_users()
            if not users:
                await event.answer("No users.", alert=True); return
            txt = "👥 **User Balances:**\n\n"
            for uid2, bal in users[:50]:
                txt += f"🆔 `{uid2}` — **${bal:.2f}**\n"
            btns = [[Button.inline("🔙 Back", b"admin_panel")]]
            await event.edit(txt[:3900], buttons=btns)

    except MessageNotModifiedError:
        pass
    except Exception as e:
        print(f"Callback Error: {e}")

async def show_active_orders(event, uid):
    conn = get_db()
    rows = conn.execute("SELECT order_id, phone, country_name FROM orders WHERE user_id=? AND status='WAITING'", (uid,)).fetchall()
    conn.close()
    if not rows:
        await event.edit("📋 No active orders.", buttons=[[Button.inline("🔙 Menu", b"back_main")]]); return
    btns = []
    for oid, phone, cname in rows:
        btns.append([Button.inline(f"📱 +{phone} ({cname})", f"chk_sms_{oid}".encode()),
                     Button.inline("❌ Cancel", f"cnc_ord_{oid}".encode())])
    btns.append([Button.inline("❌ Cancel All", b"cnc_all")])
    btns.append([Button.inline("🔙 Menu", b"back_main")])
    await event.edit("📋 **Active Orders:**", buttons=btns)

# ==================== TEXT INPUT ====================
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and not e.text.startswith('/')))
async def msg_handler(event):
    if is_duplicate(f"msg_{event.id}"): return
    uid = event.sender_id
    text = event.raw_text.strip()

    if uid in user_states and user_states[uid].get("step") == "custom_qty":
        cid = user_states[uid].get("cid")
        user_states.pop(uid, None)
        try:
            qty = int(text)
            if qty < 1 or qty > 50:
                await event.respond("❌ 1-50"); return
            await process_batch_purchase(event, uid, cid, qty)
        except: await event.respond("❌ Send a number")
        return

    if uid != ADMIN_ID or uid not in admin_states:
        return

    state = admin_states[uid]
    step = state.get("step")

    if step == 1:
        state["data"]["code"] = text; state["step"] = 2
        await event.respond("**Step 2:** Country name")
    elif step == 2:
        state["data"]["name"] = text; state["step"] = 3
        await event.respond("**Step 3:** Flag emoji")
    elif step == 3:
        state["data"]["flag"] = text; state["step"] = 4
        await event.respond("**Step 4:** Provider IDs\n(e.g. `3193` or `0` for all)")
    elif step == 4:
        state["data"]["provider"] = "" if text == "0" else text; state["step"] = 5
        await event.respond("**Step 5:** Sell price ($)")
    elif step == 5:
        try:
            price = float(text)
            d = state["data"]
            conn = get_db()
            # Allow duplicate countries with same code (different providers)
            conn.execute(
                "INSERT INTO countries (country_code, name, flag, provider_ids, price) VALUES (?,?,?,?,?)",
                (d["code"], d["name"], d["flag"], d["provider"], price))
            conn.commit(); conn.close()
            prov = f" 🏷️{d['provider']}" if d['provider'] else ""
            del admin_states[uid]
            await event.respond(f"✅ **Added!**\n{d['flag']} {d['name']} | ${price:.2f}{prov}",
                buttons=admin_buttons())
        except ValueError:
            await event.respond("❌ Send a valid price:")
    elif step == "balance":
        try:
            parts = text.split()
            tid, amt = int(parts[0]), float(parts[1])
            if not state["is_add"]: amt = -amt
            create_user(tid); add_balance(tid, amt)
            del admin_states[uid]
            sign = "+" if state["is_add"] else "-"
            await event.respond(f"✅ `{tid}` {sign}${abs(amt):.2f}", buttons=admin_buttons())
        except: await event.respond("❌ Format: `user_id amount`")

# ==================== RUN ====================
async def main():
    print("🤖 Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
