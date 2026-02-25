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

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

async def get_combot_links():
    """Combot-dan ilk 10 səhifədəki (~500 qrup) Türk qruplarını yığır"""
    groups = []
    headers = {"User-Agent": "Mozilla/5.0"} 
    # Səhifə sayını 10-a qaldırdıq
    for page in range(1, 11):
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
    if not event.out:
        return

    target = event.pattern_match.group(1)
    try:
        target_id = int(target)
    except ValueError:
        await event.edit("❌ Lütfən rəqəm şəklində ID daxil edin.")
        return

    status_msg = await event.edit(f"🚀 **Dərin axtarış başladı...**\n🔍 Hədəf ID: `{target_id}`\n📊 Qruplar toplanır...")
    
    group_list = await get_combot_links()
    found_in = []
    total_groups = len(group_list)

    await status_msg.edit(f"🔎 {total_groups} qrup tapıldı. Yoxlanılır...\n*(Bu proses uzun çəkə bilər)*")

    for index, username in enumerate(group_list):
        try:
            # Mesaj limitini 5000 etdik (Lakin Telegram-ın Flood limitinə görə ehtiyatlı olmalısan)
            # QEYD: 5000 mesaj çəkmək bəzən 1 sorğuda bitmir, ona görə sürəti tənzimləyirik
            history = await client(GetHistoryRequest(
                peer=username, limit=5000, offset_date=None, offset_id=0,
                max_id=0, min_id=0, add_offset=0, hash=0
            ))
            
            for msg in history.messages:
                if msg.from_id and hasattr(msg.from_id, 'user_id'):
                    if msg.from_id.user_id == target_id:
                        found_in.append(f"@{username}")
                        break
            
            # Hər 5 qrupdan bir mütərəqqi məlumat ver
            if index % 5 == 0:
                await status_msg.edit(f"⏳ Yoxlanılır: `{index}/{total_groups}` qrup...\n✅ Tapılan: {len(found_in)}")
            
            # Banlanmamaq üçün 2 saniyə gözləmə (5000 mesaj üçün vacibdir)
            await asyncio.sleep(2) 
            
        except Exception:
            continue

    if found_in:
        result = f"🔥 **ID {target_id} üçün tapılan qruplar:**\n\n" + "\n".join(found_in)
        await status_msg.edit(result)
    else:
        await status_msg.edit(f"😔 `{target_id}` üçün 500 qrupda son 5000 mesajda nəticə tapılmadı.")

async def start_bot():
    await client.start()
    print("✅ Dərin Axtarış Botu Hazırdır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(start_bot())
