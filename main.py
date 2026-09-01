import asyncio
import sqlite3
import time
import aiohttp
from telethon import TelegramClient, events, Button

# ==================== CONFIG ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8772444673:AAHP0EWqVFwRyM9tvKS6VuRvrGxL3tB0cek'
ADMIN_ID = 5190717598
SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_URL = 'https://smsbower.page/stubs/handler_api.php'
# ================================================

# ==================== DB ====================
def get_db():
    return sqlite3.connect("shop.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT UNIQUE,
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
    conn.close()
    if r: return r[0]
    conn2 = get_db()
    conn2.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn2.commit(); conn2.close()
    return 0.0

def add_balance(uid, amt):
    conn = get_db()
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

def create_user(uid):
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn.commit(); conn.close()

init_db()
client = TelegramClient("shop_bot_session", API_ID, API_HASH)
admin_states = {}
auto_check_tasks = {}  # order_id: asyncio.Task
start_done = set()
user_locks = {}         # uid: asyncio.Lock — prevent race on /start
processing_buys = set() # prevent double-click buy (uid_cid)

# ==================== API ====================
async def api(action, **kw):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.text()
    except:
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
        [Button.inline("🔙 Main Menu", b"back_main")]
    ]

# ==================== AUTO CHECK SMS ====================
async def auto_check_sms(uid, order_id, msg):
    """Background task: check SMS every 3 seconds until code arrives or cancelled"""
    try:
        for _ in range(200):  # max 10 minutes
            await asyncio.sleep(3)
            
            # Check if order still active
            conn = get_db()
            r = conn.execute('SELECT status FROM orders WHERE order_id=?', (order_id,)).fetchone()
            conn.close()
            if not r or r[0] != 'WAITING':
                return
            
            status = await api('getStatus', id=order_id)
            
            if status.startswith('STATUS_OK'):
                code = status.split(':')[1]
                # Complete activation on API
                await api('setStatus', id=order_id, status='6')
                # Update DB
                conn = get_db()
                conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                # Balance already deducted at purchase time
                # Send code to user
                await client.send_message(uid,
                    f"🎉 **Code Received!**\n\n"
                    f"📱 Phone: `+{msg['phone']}`\n"
                    f"🔑 Code: `{code}`\n\n"
                    f"✅ Done!",
                    buttons=[[Button.inline("🛒 Buy Again", b"buy_tg")], [Button.inline("🔙 Menu", b"back_main")]]
                )
                return
            
            elif status.startswith('STATUS_CANCEL'):
                conn = get_db()
                conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                await client.send_message(uid, "❌ **Order expired/cancelled.**",
                    buttons=[[Button.inline("🔙 Menu", b"back_main")]])
                return
        
        # Timeout after 10 minutes
        await client.send_message(uid, "⏰ **Timeout** — No code received in 10 min.\nUse ❌ Cancel to refund.",
            buttons=[[Button.inline("📩 Check Again", f"chk_sms_{order_id}".encode())],
                     [Button.inline("❌ Cancel", f"cnc_ord_{order_id}".encode())]])
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Auto check error: {e}")

# ==================== START ====================
@client.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    uid = event.sender_id
    if uid not in user_locks:
        user_locks[uid] = asyncio.Lock()
    async with user_locks[uid]:
        if uid in start_done:
            return
        start_done.add(uid)
        create_user(uid)
        user = await event.get_sender()
        name = user.first_name if user and user.first_name else "User"
        bal = get_balance(uid)
        await event.respond(
            f"👋 **Hello {name}!**\n\n"
            f"💳 Balance: **${bal:.2f}**\n"
            f"⚡ Service: **Telegram**\n\n"
            f"Choose:",
            buttons=main_buttons(uid)
        )

# ==================== CALLBACK ROUTER ====================
@client.on(events.CallbackQuery)
async def callback_router(event):
    data = event.data.decode()
    uid = event.sender_id

    # --- Main Menu ---
    if data == "back_main":
        start_done.add(uid)
        await event.edit(main_text(uid), buttons=main_buttons(uid))

    # --- Profile ---
    elif data == "my_account":
        bal = get_balance(uid)
        await event.edit(
            f"👤 **Account**\n\n🆔 `{uid}`\n💰 Balance: **${bal:.2f}**",
            buttons=[[Button.inline("🔙 Back", b"back_main")]]
        )

    # --- Buy Telegram ---
    elif data == "buy_tg":
        conn = get_db()
        rows = conn.execute("SELECT id, name, flag, price FROM countries ORDER BY id").fetchall()
        conn.close()
        if not rows:
            await event.answer("⚠️ No countries added yet.", alert=True)
            return
        btns = [[Button.inline(f"{f} {n} — ${p:.2f}", f"buy_c_{i}".encode())] for i, n, f, p in rows]
        btns.append([Button.inline("🔙 Back", b"back_main")])
        await event.edit("🌍 **Select Country:**", buttons=btns)

    # --- Buy Country ---
    elif data.startswith("buy_c_"):
        cid = data.split("_")[2]
        key = f"{uid}_{cid}"
        if key in processing_buys:
            await event.answer("⏳ Already processing, wait...", alert=True)
            return
        processing_buys.add(key)
        try:
            conn = get_db()
            row = conn.execute("SELECT country_code, name, flag, provider_ids, price FROM countries WHERE id=?", (cid,)).fetchone()
            if not row:
                conn.close()
                await event.answer("Not found", alert=True)
                return
            c_code, name, flag, provider_ids, price = row
            bal_row = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
            bal = bal_row[0] if bal_row else 0.0
            conn.close()

            if bal < price:
                await event.answer(f"❌ Need ${price:.2f}", alert=True)
                return

            await event.answer("⏳ Getting number...")
            params = {'service': 'tg', 'country': c_code}
            if provider_ids:
                params['providerIds'] = provider_ids
            
            res = await api('getNumber', **params)
            if not res.startswith('ACCESS_NUMBER'):
                await event.respond(f"⚠️ No number available for {flag} {name}",
                    buttons=[[Button.inline("🔄 Retry", f"buy_c_{cid}".encode())], [Button.inline("🔙 Back", b"back_main")]])
                return

            parts = res.split(':')
            order_id, phone = parts[1], parts[2]

            # Deduct balance NOW at purchase
            add_balance(uid, -price)

            conn = get_db()
            conn.execute("INSERT INTO orders (user_id, order_id, phone, country_name, price, status, created_at) VALUES (?,?,?,?,?,'WAITING',?)",
                (uid, order_id, phone, name, price, int(time.time())))
            conn.commit()
            conn.close()

            # Start auto-check background task
            order_info = {'phone': phone, 'order_id': order_id}
            task = asyncio.create_task(auto_check_sms(uid, order_id, order_info))
            auto_check_tasks[order_id] = task

            await event.edit(
                f"✅ **Number Ready!**\n\n"
                f"{flag} **{name}**\n"
                f"📱 `+{phone}`\n"
                f"💰 ${price:.2f}\n"
                f"🆔 `{order_id}`\n\n"
                f"⏳ Auto-checking for code...\n"
                f"Enter code in Telegram.",
                buttons=[
                    [Button.inline("📩 Get Code", f"chk_sms_{order_id}".encode())],
                    [Button.inline("❌ Cancel & Refund", f"cnc_ord_{order_id}".encode())]
                ]
            )
        finally:
            processing_buys.discard(key)

    # --- Check SMS ---
    elif data.startswith("chk_sms_"):
        order_id = data.split("_")[2]
        conn = get_db()
        row = conn.execute("SELECT status, phone FROM orders WHERE order_id=?", (order_id,)).fetchone()
        conn.close()
        if not row:
            await event.answer("Order not found", alert=True); return

        status = await api('getStatus', id=order_id)
        if status.startswith('STATUS_OK'):
            code = status.split(':')[1]
            await api('setStatus', id=order_id, status='6')
            conn = get_db()
            conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
            conn.commit(); conn.close()
            # Cancel auto-check if running
            if order_id in auto_check_tasks:
                auto_check_tasks[order_id].cancel()
                del auto_check_tasks[order_id]
            await event.respond(
                f"🎉 **Code Received!**\n\n📱 `+{row[1]}`\n🔑 Code: `{code}`\n\n✅ Done!",
                buttons=[[Button.inline("🛒 Buy Again", b"buy_tg")], [Button.inline("🔙 Menu", b"back_main")]]
            )
        elif status == 'STATUS_WAIT_CODE':
            await event.answer("⏳ Waiting...", alert=True)
        elif status.startswith('STATUS_WAIT_RETRY'):
            last = status.split(':')[1] if ':' in status else '?'
            await event.answer(f"⏳ Last: {last} — waiting next...", alert=True)
        elif status == 'STATUS_CANCEL':
            await event.answer("❌ Expired", alert=True)
        else:
            await event.answer(f"{status[:60]}", alert=True)

    # --- Cancel Order ---
    elif data.startswith("cnc_ord_"):
        order_id = data.split("_")[2]
        conn = get_db()
        row = conn.execute("SELECT price, status FROM orders WHERE order_id=? AND user_id=?", (order_id, uid)).fetchone()
        if not row or row[1] != 'WAITING':
            conn.close(); await event.answer("❌ Cannot cancel", alert=True); return
        
        price = row[0]
        res = await api('setStatus', id=order_id, status='8')
        
        # Cancel auto-check task
        if order_id in auto_check_tasks:
            auto_check_tasks[order_id].cancel()
            del auto_check_tasks[order_id]
        
        if 'ACCESS_CANCEL' in res or 'ACCESS_OK' in res:
            conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
            conn.commit(); conn.close()
            add_balance(uid, price)
            await event.edit(f"✅ **Cancelled.** ${price:.2f} refunded.\n\n{main_text(uid)}", buttons=main_buttons(uid))
        else:
            conn.close()
            await event.answer(f"❌ Cannot cancel: {res[:50]}", alert=True)

    # --- Active Orders ---
    elif data == "active_orders":
        conn = get_db()
        rows = conn.execute("SELECT order_id, phone, country_name FROM orders WHERE user_id=? AND status='WAITING'", (uid,)).fetchall()
        conn.close()
        if not rows:
            await event.answer("No active orders.", alert=True); return
        btns = []
        for oid, phone, cname in rows:
            btns.append([Button.inline(f"📱 +{phone} ({cname})", f"chk_sms_{oid}".encode())])
            btns.append([Button.inline(f"❌ Cancel", f"cnc_ord_{oid}".encode())])
        btns.append([Button.inline("🔙 Menu", b"back_main")])
        await event.edit("📋 **Active Orders:**", buttons=btns)

    # ==================== ADMIN ====================
    elif data == "admin_panel" and uid == ADMIN_ID:
        await event.edit("⚙️ **Admin Panel**", buttons=admin_buttons())

    elif data == "adm_add_c" and uid == ADMIN_ID:
        admin_states[uid] = {"step": 1, "data": {}}
        await event.respond("**Step 1:** Country code\n(e.g. `0` = Russia, `7` = USA)")

    elif data == "adm_list_c" and uid == ADMIN_ID:
        conn = get_db()
        rows = conn.execute("SELECT id, name, flag, country_code, price, provider_ids FROM countries").fetchall()
        conn.close()
        if not rows:
            await event.answer("No countries.", alert=True); return
        txt = "🌍 **Countries:**\n\n"
        btns = []
        for cid, name, flag, code, price, prov in rows:
            p = f" 🏷️{prov}" if prov else ""
            txt += f"{flag} {name} (`{code}`) | ${price:.2f}{p}\n"
            btns.append([Button.inline(f"🗑️ {flag} {name}", f"del_c_{cid}".encode())])
        btns.append([Button.inline("🔙 Back", b"admin_panel")])
        if len(txt) > 4000: txt = txt[:4000] + "..."
        await event.edit(txt, buttons=btns)

    elif data.startswith("del_c_") and uid == ADMIN_ID:
        cid = data.split("_")[2]
        conn = get_db()
        conn.execute("DELETE FROM countries WHERE id=?", (cid,))
        conn.commit(); conn.close()
        await event.answer("✅ Deleted!")
        # Refresh list
        conn = get_db()
        rows = conn.execute("SELECT id, name, flag, country_code, price, provider_ids FROM countries").fetchall()
        conn.close()
        txt = "🌍 **Countries:**\n\n"
        btns = []
        for cid2, name, flag, code, price, prov in rows:
            p = f" 🏷️{prov}" if prov else ""
            txt += f"{flag} {name} (`{code}`) | ${price:.2f}{p}\n"
            btns.append([Button.inline(f"🗑️ {flag} {name}", f"del_c_{cid2}".encode())])
        btns.append([Button.inline("🔙 Back", b"admin_panel")])
        if len(txt) > 4000: txt = txt[:4000] + "..."
        await event.edit(txt, buttons=btns)

    elif data in ["adm_add_b", "adm_sub_b"] and uid == ADMIN_ID:
        is_add = (data == "adm_add_b")
        admin_states[uid] = {"step": "balance", "is_add": is_add}
        act = "Add" if is_add else "Sub"
        await event.respond(f"**{act} Balance**\n\nSend: `user_id amount`\nExample: `123456789 2.5`")

# ==================== ADMIN TEXT INPUT ====================
@client.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def msg_handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    if uid != ADMIN_ID or uid not in admin_states:
        return

    state = admin_states[uid]
    step = state.get("step")

    if step == 1:
        state["data"]["code"] = text
        state["step"] = 2
        await event.respond("**Step 2:** Country name\n(e.g. `Russia`)")

    elif step == 2:
        state["data"]["name"] = text
        state["step"] = 3
        await event.respond("**Step 3:** Flag emoji\n(e.g. 🇷🇺)")

    elif step == 3:
        state["data"]["flag"] = text
        state["step"] = 4
        await event.respond("**Step 4:** Provider IDs\n(e.g. `3193,4120` or `0` for all)")

    elif step == 4:
        state["data"]["provider"] = "" if text == "0" else text
        state["step"] = 5
        await event.respond("**Step 5:** Sell price ($)\n(e.g. `0.50`)")

    elif step == 5:
        try:
            price = float(text)
            d = state["data"]
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO countries (country_code, name, flag, provider_ids, price) VALUES (?,?,?,?,?)",
                (d["code"], d["name"], d["flag"], d["provider"], price))
            conn.commit(); conn.close()
            prov = f" 🏷️{d['provider']}" if d['provider'] else ""
            del admin_states[uid]
            await event.respond(
                f"✅ **Added!**\n\n{d['flag']} {d['name']} (`{d['code']}`) | ${price:.2f}{prov}",
                buttons=admin_buttons()
            )
        except ValueError:
            await event.respond("❌ Invalid price. Send a number:")

    elif step == "balance":
        try:
            parts = text.split()
            target_uid = int(parts[0])
            amount = float(parts[1])
            is_add = state["is_add"]
            if not is_add:
                amount = -amount
            create_user(target_uid)
            add_balance(target_uid, amount)
            del admin_states[uid]
            sign = "+" if is_add else "-"
            await event.respond(f"✅ `{target_uid}` balance updated {sign}${abs(amount):.2f}", buttons=admin_buttons())
            try:
                await client.send_message(target_uid, f"💳 Balance updated: **{sign}${abs(amount):.2f}**")
            except: pass
        except:
            await event.respond("❌ Format: `user_id amount`\nExample: `123456789 2.5`")

# ==================== RUN ====================
async def main():
    print("🤖 Starting...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
