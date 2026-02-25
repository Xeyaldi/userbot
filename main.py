import os
import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from telethon.sessions import StringSession 
from telethon.tl.functions.messages import GetHistoryRequest

# Heroku Settings
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

# Client-i StringSession ilə qururuq
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

async def get_combot_links():
    """Combot-dan ilk 3 səhifədəki Türk qruplarını yığır"""
    groups = []
    headers = {"User-Agent": "Mozilla/5.0"} 
    for page in range(1, 4):
        url = f"https://combot.org/telegram/top/groups/tr?page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if "t.me/" in a['href']:
                    user = a['href'].split('/')[-1].split('?')[0]
                    if user not in groups and user not in ["combot", "addmetelegram"]:
                        groups.append(user)
        except:
            continue
    return groups

@client.on(events.NewMessage(pattern=r'/axdar (.+)'))
async def search_handler(event):
    if not event.out: # Yalnız sənin öz göndərdiyin mesajlara cavab versin
        return

    target = event.pattern_match.group(1)
    try:
        target_id = int(target)
    except ValueError:
        await event.edit("❌ Lütfən rəqəm şəklində ID daxil edin.")
        return

    status_msg = await event.edit(f"🔍 `{target_id}` axtarılır...")
    group_list = await get_combot_links()
    found_in = []

    for username in group_list:
        try:
            history = await client(GetHistoryRequest(
                peer=username, limit=50, offset_date=None, offset_id=0,
                max_id=0, min_id=0, add_offset=0, hash=0
            ))
            for msg in history.messages:
                if msg.from_id and hasattr(msg.from_id, 'user_id'):
                    if msg.from_id.user_id == target_id:
                        found_in.append(f"@{username}")
                        break
            await asyncio.sleep(1.5)
        except:
            continue

    if found_in:
        await status_msg.edit(f"✅ **Tapıldı:**\n" + "\n".join(found_in))
    else:
        await status_msg.edit("😔 Mesaj tapılmadı.")

# XƏTANI DÜZƏLDƏN ƏSAS HİSSƏ:
async def start_bot():
    await client.start()
    print("✅ Bot Heroku-da uğurla işə düşdü!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(start_bot())
