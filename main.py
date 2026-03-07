import os
import asyncio
import importlib
import importlib.util
import time
import ast
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession
# Tərcümə üçün lazım olan kitabxana
from deep_translator import GoogleTranslator

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Ayarlar
AFK_REJIM = False
AFK_SEBEB = ""
PLUGINS_DIR = "plugins"

if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# --- MENYU KOMANDASI ---
@client.on(events.NewMessage(pattern=r'\.xeyalinmenusu'))
async def menyu(event):
    if event.out:
        menyu_metni = (
            "🌟 **XəyalUserbot Menyusu** 🌟\n\n"
            "🛠 **Mövcud Komandalar:**\n"
            "• `.ters` - Yazını tərsinə çevirir\n"
            "• `.del` - Mesajı silir\n"
            "• `.info` - ID göstərir\n"
            "• `.saat` - Canlı saat\n"
            "• `.afk [səbəb]` - AFK rejimini açır\n"
            "• `.online` - AFK bağlayır\n"
            "• `.pluginyukle` - Plugin əlavə edir\n"
            "• `.burdasangaga` - Botu yoxlayır\n"
            "• `.tercume [az/ru/ing/fr]` - Reply mesajı tərcümə edir\n"
        )
        await event.edit(menyu_metni)

# --- TƏRCÜMƏ KOMANDASI ---
@client.on(events.NewMessage(pattern=r'\.tercume (az|ru|ing|fr)'))
async def tercume_et(event):
    if not event.out: return
    if not event.is_reply:
        await event.edit("❌ Tərcümə etmək üçün bir mesajı reply edin gaga!")
        return

    dil_kodlari = {
        "az": "az",
        "ru": "ru",
        "ing": "en",
        "fr": "fr"
    }
    
    secilen_dil = event.pattern_match.group(1)
    hedef_dil = dil_kodlari.get(secilen_dil)
    
    reply_msg = await event.get_reply_message()
    metn = reply_msg.text
    
    if not metn:
        await event.edit("❌ Tərcümə ediləcək mətn tapılmadı.")
        return

    await event.edit("🔄 Tərcümə edilir...")
    
    try:
        tercume = GoogleTranslator(source='auto', target=hedef_dil).translate(metn)
        await event.edit(f"🌐 **Dil:** `{secilen_dil.upper()}`\n\n📝 **Tərcümə:**\n{tercume}")
    except Exception as e:
        await event.edit(f"❌ Xəta baş verdi: `{str(e)}`")

# --- ƏSAS KOMANDALAR ---
@client.on(events.NewMessage(pattern=r'\.burdasangaga'))
async def burdasan(event):
    if event.out: await event.edit("Hə burdayam gaga")

@client.on(events.NewMessage(pattern=r'\.ters(?:\s+(.*))?'))
async def ters_cevir(event):
    if not event.out: return
    text = event.pattern_match.group(1)
    if event.is_reply:
        reply = await event.get_reply_message()
        text = reply.text
    if text: await event.edit(text[::-1])
    else: await event.edit("❌ Mətn daxil edin və ya reply atın!")

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
        await event.edit(f"👤 **İstifadəçi ID:** `{u_id}`")

@client.on(events.NewMessage(pattern=r'\.saat'))
async def canli_saat(event):
    if event.out:
        for _ in range(15):
            await event.edit(f"🕒 **Saat:** `{time.strftime('%H:%M:%S')}`")
            await asyncio.sleep(1)

@client.on(events.NewMessage(pattern=r'\.afk ?(.*)'))
async def afk_aktiv(event):
    global AFK_REJIM, AFK_SEBEB
    if event.out:
        AFK_REJIM, AFK_SEBEB = True, event.pattern_match.group(1)
        await event.edit(f"💤 AFK aktiv. Səbəb: {AFK_SEBEB if AFK_SEBEB else 'Yoxdur.'}")

@client.on(events.NewMessage(incoming=True))
async def afk_cavab(event):
    if AFK_REJIM and event.is_private:
        await event.respond(f"🤖 AFK-yam.\n📝 Səbəb: {AFK_SEBEB if AFK_SEBEB else 'Yoxdur.'}")

@client.on(events.NewMessage(pattern=r'\.online'))
async def afk_deaktiv(event):
    global AFK_REJIM
    if event.out:
        AFK_REJIM = False
        await event.edit("✅ AFK söndürüldü.")

# --- PLUGİN YÜKLƏMƏ VƏ AKTİVLƏŞDİRMƏ ---
@client.on(events.NewMessage(pattern=r'\.pluginyukle'))
async def plugin_yukle(event):
    if not event.out or not event.is_reply:
        await event.edit("❌ Lütfən bir `.py` faylına reply atın gaga!")
        return
        
    reply_message = await event.get_reply_message()
    if reply_message.file and reply_message.file.name.endswith(".py"):
        p_name = reply_message.file.name
        p_path = os.path.join(PLUGINS_DIR, p_name)
        await client.download_media(reply_message, p_path)
        
        try:
            module_name = p_name[:-3]
            spec = importlib.util.spec_from_file_location(module_name, p_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            with open(p_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            komandalar = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'on':
                    for arg in node.args:
                        if isinstance(arg, ast.Call) and getattr(arg.func, 'attr', '') == 'NewMessage':
                            for kw in arg.keywords:
                                if kw.arg == 'pattern' and isinstance(kw.value, ast.Constant):
                                    komandalar.append(f"`{kw.value.value}`")
            
            await event.edit(f"✅ **Plugin yükləndi gaga!**\n\n🛠 **Komandalar:**\n{chr(10).join(komandalar) if komandalar else 'Tapılmadı.'}")
            
        except Exception as e:
            await event.edit(f"❌ **Plugin yüklənmədi gaga!**\n⚠️ Xəta: `{str(e)}`")
    else:
        await event.edit("❌ Bu düzgün bir plugin faylı deyil gaga!")

async def main():
    await client.start()
    if os.path.exists(PLUGINS_DIR):
        for f in os.listdir(PLUGINS_DIR):
            if f.endswith(".py"):
                try:
                    m_name = f[:-3]
                    spec = importlib.util.spec_from_file_location(m_name, os.path.join(PLUGINS_DIR, f))
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[m_name] = module
                    spec.loader.exec_module(module)
                except: continue
    print("🚀 Userbot Hazırdır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
