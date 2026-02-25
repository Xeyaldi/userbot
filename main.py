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
    # Real brauzer kimi görünmək üçün headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    } 
    
    for page in range(1, 11): # 1-dən 10-cu səhifəyə qədər
        url = f"https://combot.org/telegram/top/groups/tr?page={page}"
        try:
            # Sayta sorğu göndəririk
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if "t.me/" in href:
                    # Linkdən istifadəçi adını təmizləyirik
                    user = href.split('/')[-1].replace('+', '').split('?')[0]
                    if user not in groups and user not in ["combot", "addmetelegram", "share"]:
                        groups.append(user)
        except Exception as e:
            print(f"Səhifə {page} oxunmadı: {e}")
            continue
    return groups

@client.on(events.NewMessage(pattern=r'/axdar (.+)'))
async def search_handler(event):
    # Yalnız sən komanda verə bilərsən
    if not event.out:
        return

    target = event.pattern_match.group(1).strip()
    try:
        target_id = int(target)
    except ValueError:
        await event.edit("❌ Lütfən düzgün bir **ID** (rəqəm) daxil edin.")
        return

    status_msg = await event.edit("🔄 **Axtarış hazırlığı...**\n🌐 Combot-dan qruplar çəkilir...")
    
    # Qrupları çəkirik
    group_list = await get_combot_links()
    
    if not group_list:
        await status_msg.edit("❌ Combot siyahısı boşdur! Sayt blok qoymuş ola bilər. Bir az sonra yoxlayın.")
        return

    total = len(group_list)
    await status_msg.edit(f"🔎 **{total} qrup tapıldı.**\n📊 Hər qrupda son mesajlar analiz edilir...\n\n⏳ *Bu proses 10-15 dəqiqə çəkə bilər.*")

    found_in = []
    
    # Qrupları tək-tək yoxlayırıq
    for index, username in enumerate(group_list, start=1):
        try:
            # get_messages daha stabil işləyir (limit 300 qoydum ki, ban riski azalsın)
            # Sən bunu limit=1000 edə bilərsən, amma yavaşlayacaq
            async for msg in client.iter_messages(username, limit=300):
                if msg.from_id and hasattr(msg.from_id, 'user_id'):
                    if msg.from_id.user_id == target_id:
                        found_in.append(f"@{username}")
                        break # Bu qrupda tapıldısa növbəti qrupa keç
            
            # Hər 10 qrupdan bir mesajı yeniləyirik ki, botun donmadığını görəsən
            if index % 10 == 0:
                await status_msg.edit(
                    f"🔄 **Yoxlanılır:** `{index}/{total}` qrup\n"
                    f"✅ **Tapılan:** `{len(found_in)}` qrup\n"
                    f"📍 **Son baxılan:** @{username}"
                )
            
            # Telegram-dan qovulmamaq üçün kiçik fasilə
            await asyncio.sleep(1.2)
            
        except Exception as e:
            # Qrup bağlıdırsa və ya banlıyıqsa keçirik
            continue

    # Nəticəni göndəririk
    if found_in:
        final_text = f"🔥 **ID `{target_id}` üçün tapılan qruplar:**\n\n"
        final_text += "\n".join(found_in)
        await status_msg.edit(final_text)
    else:
        await status_msg.edit(f"😔 `{target_id}` son 300 mesaj daxilində bu qruplarda tapılmadı.")

async def start_bot():
    await client.start()
    print("✅ Bot uğurla işə düşdü! Telegram-da /axdar ID yazaraq yoxla.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"Bot çökdü: {e}")
