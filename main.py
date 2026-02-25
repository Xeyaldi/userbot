import os
import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest

# Heroku Settings (Bunları Heroku Dashboard-da Config Vars hissəsinə yazacaqsan)
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING") # Telethon Session String

client = TelegramClient(SESSION, API_ID, API_HASH)

async def get_combot_links():
    """Combot-dan ilk 3 səhifədəki Türk qruplarını yığır"""
    groups = []
    for page in range(1, 4): # İlk 3 səhifə (~150 qrup)
        url = f"https://combot.org/telegram/top/groups/tr?page={page}"
        try:
            res = requests.get(url, timeout=10)
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
    target = event.pattern_match.group(1)
    
    # Əgər rəqəmdirsə ID kimi qəbul et
    try:
        target_id = int(target)
    except ValueError:
        await event.edit("❌ Lütfən rəqəm şəklində ID daxil edin. Username ilə axtarış dəqiq deyil.")
        return

    status_msg = await event.edit(f"🔍 `{target_id}` ID-si Combot qruplarında axtarılır...")
    
    group_list = await get_combot_links()
    found_in = []

    for username in group_list:
        try:
            # Qrupa girmədən son 50 mesajı analiz edir
            history = await client(GetHistoryRequest(
                peer=username, limit=50, offset_date=None, offset_id=0,
                max_id=0, min_id=0, add_offset=0, hash=0
            ))
            
            for msg in history.messages:
                if msg.from_id and hasattr(msg.from_id, 'user_id'):
                    if msg.from_id.user_id == target_id:
                        found_in.append(f"@{username}")
                        break # Bu qrupda tapıldısa növbəti qrupa keç
            
            await asyncio.sleep(1.5) # Banlanmamaq üçün
        except:
            continue

    if found_in:
        result = "**🔥Tapıldığı qruplar:**\n" + "\n".join(found_in)
        await status_msg.edit(result)
    else:
        await status_msg.edit("😔 Təəssüf ki, aktiv mesaj tapılmadı.")

print("Bot başladıldı...")
client.start()
client.run_until_disconnected()
