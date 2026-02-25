import os
import asyncio
import importlib
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# AFK statusu üçün dəyişən
AFK_REJIM = False
AFK_SEBEB = ""

# Plugin qovluğu
if not os.path.exists("plugins"):
    os.makedirs("plugins")

@client.on(events.NewMessage(pattern=r'\.burdasangaga'))
async def burdasan(event):
    if event.out:
        await event.edit("Hə burdayam gaga")

@client.on(events.NewMessage(pattern=r'\.ters (.+)'))
async def ters_cevir(event):
    if event.out:
        text = event.pattern_match.group(1)
        await event.edit(text[::-1])

@client.on(events.NewMessage(pattern=r'\.del'))
async def mesaj_sil(event):
    if event.out and event.is_reply:
        reply = await event.get_reply_message()
        await reply.delete()
        await event.delete()

@client.on(events.NewMessage(pattern=r'\.info'))
async def user_info(event):
    if event.out and event.is_reply:
        reply = await event.get_reply_message()
        u_id = reply.from_id.user_id if hasattr(reply.from_id, 'user_id') else "Tapılmadı"
        await event.edit(f"👤 **İstifadəçi:**\n🆔 **ID:** `{u_id}`")

@client.on(events.NewMessage(pattern=r'\.saat'))
async def canli_saat(event):
    if event.out:
        for _ in range(15): # 15 saniyəlik canlı saat
            current_time = time.strftime("%H:%M:%S")
            await event.edit(f"🕒 **Saat:** `{current_time}`")
            await asyncio.sleep(1)

@client.on(events.NewMessage(pattern=r'\.afk ?(.*)'))
async def afk_aktiv(event):
    global AFK_REJIM, AFK_SEBEB
    if event.out:
        AFK_REJIM = True
        AFK_SEBEB = event.pattern_match.group(1)
        await event.edit(f"💤 **AFK rejimi aktiv edildi.**\nSəbəb: {AFK_SEBEB if AFK_SEBEB else 'Qeyd edilməyib.'}")

@client.on(events.NewMessage(incoming=True))
async def afk_cavab(event):
    global AFK_REJIM
    if AFK_REJIM and event.is_private:
        await event.respond(f"🤖 **Mən hazırda AFK-yam (aktiv deyiləm).**\n\n📝 **Səbəb:** {AFK_SEBEB if AFK_SEBEB else 'Yoxdur.'}")

@client.on(events.NewMessage(pattern=r'\.online'))
async def afk_deaktiv(event):
    global AFK_REJIM
    if event.out:
        AFK_REJIM = False
        await event.edit("✅ **Mən qayıtdım! AFK rejimi söndürüldü.**")

@client.on(events.NewMessage(pattern=r'\.pluginyukle'))
async def plugin_yukle(event):
    if not event.out or not event.is_reply: return
    reply_message = await event.get_reply_message()
    if reply_message.file and reply_message.file.name.endswith(".py"):
        path = os.path.join("plugins", reply_message.file.name)
        await client.download_media(reply_message, path)
        await event.edit(f"✅ `{reply_message.file.name}` yükləndi!")
        # Plugin aktivləşdirmə kodu buraya gələ bilər

async def main():
    await client.start()
    print("🚀 Userbot tam funksiyalarla işə düşdü!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
