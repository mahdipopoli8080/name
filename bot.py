import os
import asyncio
import re
import random
from telethon import TelegramClient, events, Button
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ==================== دریافت اطلاعات از متغیرهای محیطی ====================
API_ID = int(os.environ.get('API_ID', 8477522))
API_HASH = os.environ.get('API_HASH', '366c19cf69e02cad530261ad81212a85')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8832756816:AAG2x7shLzKBmhAddJxizQfMxx7cXSk1Tpg')

CLIENT_ID = os.environ.get('CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

CLIENT_CONFIG = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
    }
}

user_credentials = {}
processed_msg_ids = set()

client = TelegramClient('gmail_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def generate_random_case_gmail(base_email="mahdIpopoLi778@gmail.com"):
    name, domain = base_email.split('@')
    random_name = "".join(
        char.upper() if random.choice([True, False]) else char.lower() 
        if char.isalpha() else char 
        for char in name
    )
    return f"{random_name}@{domain}"

def extract_telegram_code(text):
    match = re.search(r'\b\d{5}\b', text)
    return match.group(0) if match else None

async def auto_check_gmail_loop():
    while True:
        try:
            for user_id, creds_data in list(user_credentials.items()):
                creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
                service = build('gmail', 'v1', credentials=creds)

                results = service.users().messages().list(
                    userId='me', 
                    q='from:telegram.org is:unread', 
                    maxResults=5
                ).execute()

                messages = results.get('messages', [])

                for msg in messages:
                    msg_id = msg['id']
                    if msg_id in processed_msg_ids:
                        continue

                    msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                    snippet = msg_data.get('snippet', '')

                    code = extract_telegram_code(snippet)
                    if code:
                        processed_msg_ids.add(msg_id)
                        service.users().messages().batchModify(
                            userId='me', 
                            body={'removeLabelIds': ['UNSEEN'], 'ids': [msg_id]}
                        ).execute()

                        asyncio.create_task(send_code_and_delete(user_id, code))

        except Exception as e:
            print(f"خطا در چک ایمیل: {e}")

        await asyncio.sleep(5)

async def send_code_and_delete(user_id, code):
    text = (
        f"🔑 **کد ورودی تلگرام شما:**\n\n"
        f"`{code}`\n\n"
        f"⚡️ *جهت کپی روی کد بالا کلیک کنید.*\n"
        f"⏱ این پیام بعد از ۳۰ ثانیه خودکار پاک می‌شود."
    )
    sent_msg = await client.send_message(user_id, text, parse_mode='md')
    await asyncio.sleep(30)
    await sent_msg.delete()

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    buttons = [
        [Button.inline("🔐 اتصال جیمیل (دستی)", data="login_gmail")],
        [Button.inline("🎲 دریافت جیمیل رندوم", data="get_random_gmail")]
    ]
    await event.respond("سلام! برای اتصال جیمیل روی دکمه زیر کلیک کنید:", buttons=buttons)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.data == b"login_gmail":
        flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
        auth_url, _ = flow.authorization_url(prompt='consent')
        text = (
            f"1️⃣ روی [این لینک ورود به گوگل]({auth_url}) کلیک کنید.\n"
            "2️⃣ کد تایید را کپی کرده و بفرستید:\n"
            "`/code YOUR_CODE_HERE`"
        )
        await event.respond(text, link_preview=False)

    elif event.data == b"get_random_gmail":
        random_gmail = generate_random_case_gmail()
        await event.respond(f"جیمیل رندوم:\n\n`{random_gmail}`")

@client.on(events.NewMessage(pattern=r'/code (.+)'))
async def set_auth_code(event):
    user_id = event.sender_id
    auth_code = event.pattern_match.group(1).strip()
    try:
        flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        user_credentials[user_id] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        await event.respond("✅ **جیمیل با موفقیت متصل شد!**")
    except Exception as e:
        await event.respond(f"❌ خطا: {e}")

async def main():
    asyncio.create_task(auto_check_gmail_loop())
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
