import os
import asyncio
import importlib
import importlib.util
import time
import ast
import sys
import random
import wikipedia
import motor.motor_asyncio  
from gtts import gTTS       
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
MONGO_URL = os.environ.get("MONGO_URL") 

# MongoDB Bağlantısını Başlat
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]

# Client-i təyin edirik (Səhv burada idi, obyekt düzgün yerdə olmalıdır)
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Qlobal dəyişənlər
AFK_REJIM = False
AFK_SEBEB = ""
TAG_REJIM = True
PLUGINS_DIR = "plugins"
FILTERS = {}

# Qovluğun yoxlanılması
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# --- BUTONLU MENYU (.htmenu) ---
@client.on(events.NewMessage(pattern=r'\.htmenu'))
async def ht_menyu(event):
    if event.out:
        res = await client.get_me()
        text = f"🌟 **ᎻᎢ ᏌᏚᎬᎡᏴOᎢ** 🌟\n\n👤 **Sahib:** [{res.first_name}](tg://user?id={res.id})\n\n🛠 **Komandalar üçün kateqoriya seçin:**"
        buttons = [
            [Button.inline("📁 Pluginlər", data="m_plug"), Button.inline("🎙 Səs/Dil", data="m_voice")],
            [Button.inline("⚙️ Sistem", data="m_sys"), Button.inline("🎭 Əyləncə", data="m_fun")],
            [Button.inline("🗑 Bağla", data="close")]
        ]
        try:
            await event.edit(text, buttons=buttons)
        except:
            await event.edit(text + "\n\n• `.ses` • `.htlive` • `.ping` • `.id` • `.tercume` • `.tagall` • `.filter`")

@client.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"m_plug":
        await event.edit("📁 **Plugin Komandaları:**\n\n• `.pluginyukle` - Yeni plugin əlavə edər.")
    elif event.data == b"m_voice":
        await event.edit("🎙 **Səs və Dil:**\n\n• `.ses [mətn]` - Mətni səsə çevirər.\n• `.tercume [kod]` - Tərcümə edər.")
    elif event.data == b"m_sys":
        await event.edit("⚙️ **Sistem:**\n\n• `.ping` - Sürət.\n• `.id` - Məlumat.\n• `.saat` - Saat.\n• `.afk` - AFK rejimi.")
    elif event.data == b"m_fun":
        await event.edit("🎭 **Əyləncə:**\n\n• `.ters` - Çevirmə.\n• `.etiraf` - Etiraf.\n• `.yazi` - Fontlar.\n• `.bom` - Partlayış.")
    elif event.data == b"close":
        await event.delete()

# --- HTLIVE KOMANDASI (.htlive) ---
@client.on(events.NewMessage(pattern=r'\.htlive'))
async def htlive(event):
    if event.out:
        res = await client.get_me()
        font_text = f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ [{res.first_name}](tg://user?id={res.id}) ϋçϋи αктινdιя"
        await event.edit(f"🚀 {font_text}")

# --- FİLTER SİSTEMİ ---
@client.on(events.NewMessage(pattern=r'\.filter (.*)'))
async def filter_add(event):
    if not event.out: return
    if not event.is_reply:
        await event.edit("❌ Filter üçün bir mesaja reply at gaga!")
        return
    keyword = event.pattern_match.group(1).lower()
    reply_msg = await event.get_reply_message()
    chat_id = event.chat_id
    if chat_id not in FILTERS: FILTERS[chat_id] = {}
    FILTERS[chat_id][keyword] = reply_msg
    await event.edit(f"✅ `{keyword}` filteri aktiv edildi!")

@client.on(events.NewMessage(pattern=r'\.stopfilter (.*)'))
async def filter_stop(event):
    if not event.out: return
    keyword = event.pattern_match.group(1).lower()
    chat_id = event.chat_id
    if chat_id in FILTERS and keyword in FILTERS[chat_id]:
        del FILTERS[chat_id][keyword]
        await event.edit(f"🗑 `{keyword}` filteri silindi.")
    else: await event.edit("❌ Belə bir filter tapılmadı.")

@client.on(events.NewMessage(incoming=True))
async def filter_handler(event):
    chat_id = event.chat_id
    if chat_id in FILTERS:
        msg_text = event.text.lower()
        if msg_text in FILTERS[chat_id]:
            await event.reply(FILTERS[chat_id][msg_text])

# --- KOMANDALAR ---
@client.on(events.NewMessage(pattern=r'\.ping'))
async def ping_test(event):
    if event.out:
        start = time.time()
        await event.edit("🚀...")
        ms = round((time.time() - start) * 1000)
        await event.edit(f"⚡ **ᎻᎢ ᏌᏚᎬᎡᏴOᎢ Sürəti:** `{ms}ms`")

@client.on(events.NewMessage(pattern=r'\.id'))
async def get_user_id(event):
    if event.out:
        if event.is_reply:
            reply = await event.get_reply_message()
            user = await client.get_entity(reply.sender_id)
            await event.edit(f"🆔 **ID:** `{user.id}`\n👤 **Ad:** {user.first_name}")
        else: await event.edit(f"🆔 **Sənin ID-in:** `{event.sender_id}`")

@client.on(events.NewMessage(pattern=r'\.etiraf'))
async def etiraf_et(event):
    if event.out:
        etiraflar = ["Dünən gizlicə soyuducunu boşaltmışam... 🤫", "Mən əslində bir bot deyiləm 🛸"]
        await event.edit(f"💭 **Etirafım:** {random.choice(etiraflar)}")

@client.on(events.NewMessage(pattern=r'\.tagall ?(.*)'))
async def tag_all(event):
    global TAG_REJIM
    if not event.out or not event.is_group: return
    sebeb = event.pattern_match.group(1)
    TAG_REJIM = True
    await event.delete()
    async for user in client.iter_participants(event.chat_id):
        if not TAG_REJIM: break
        if not user.bot:
            msg = f"[{user.first_name}](tg://user?id={user.id}) {sebeb}"
            await client.send_message(event.chat_id, msg)
            await asyncio.sleep(1.5)

@client.on(events.NewMessage(pattern=r'\.stoptag'))
async def stop_tag(event):
    global TAG_REJIM
    if event.out:
        TAG_REJIM = False
        await event.edit("✅ Tag dayandırıldı.")

@client.on(events.NewMessage(pattern=r'\.hava (.*)'))
async def hava_durumu(event):
    if event.out: await event.edit(f"🌡 **Şəhər:** `{event.pattern_match.group(1)}` üçün hava məlumatı axtarılır...")

@client.on(events.NewMessage(pattern=r'\.wiki (.*)'))
async def wikipedia_search(event):
    if not event.out: return
    query = event.pattern_match.group(1)
    try:
        wikipedia.set_lang("az")
        summary = wikipedia.summary(query, sentences=3)
        await event.edit(f"📚 **Məlumat:** {summary}")
    except: await event.edit("❌ Tapılmadı.")

@client.on(events.NewMessage(pattern=r'\.shans'))
async def shans_yoxla(event):
    if event.out: await event.edit(f"🎲 Sənin şansın: **%{random.randint(0, 100)}**")

@client.on(events.NewMessage(pattern=r'\.bom'))
async def bom_effect(event):
    if event.out: await event.edit("💣"); await asyncio.sleep(0.8); await event.edit("💥 PARTLADI!")

@client.on(events.NewMessage(pattern=r'\.dice'))
async def dice_roll(event):
    if event.out: await event.edit(random.choice(["🎲", "🎯", "🏀", "⚽"]))

@client.on(events.NewMessage(pattern=r'\.yazi (.*)'))
async def custom_font(event):
    if event.out:
        metn = event.pattern_match.group(1)
        font_metn = metn.replace('a', 'α').replace('e', 'є').replace('i', 'ι').replace('s', 'ѕ')
        await event.edit(f"✨ {font_metn}")

@client.on(events.NewMessage(pattern=r'\.tercume (az|ru|ing|fr)'))
async def tercume_et(event):
    if not event.out or not event.is_reply: return
    dil_kodlari = {"az": "az", "ru": "ru", "ing": "en", "fr": "fr"}
    hedef_dil = dil_kodlari.get(event.pattern_match.group(1))
    reply_msg = await event.get_reply_message()
    try:
        tercume = GoogleTranslator(source='auto', target=hedef_dil).translate(reply_msg.text)
        await event.edit(f"🌐 **Tərcümə:**\n{tercume}")
    except: await event.edit("❌ Xəta!")

@client.on(events.NewMessage(pattern=r'\.ses(?: |$)(.*)'))
async def text_to_speech(event):
    if not event.out: return
    args = event.pattern_match.group(1).strip()
    text = args if args else (await event.get_reply_message()).text if event.is_reply else ""
    if not text: return await event.edit("❌ Mətn yazın!")
    await event.edit("🎙 **Səs hazırlanır...**")
    try:
        tts = gTTS(text, lang='az')
        tts.save("voice.mp3")
        await client.send_file(event.chat_id, "voice.mp3", voice_note=True, reply_to=event.reply_to_msg_id)
        await event.delete()
    except Exception as e: await event.edit(f"❌ Xəta: {e}")
    finally:
        if os.path.exists("voice.mp3"): os.remove("voice.mp3")

@client.on(events.NewMessage(pattern=r'\.afk ?(.*)'))
async def afk_aktiv(event):
    global AFK_REJIM, AFK_SEBEB
    if event.out:
        AFK_REJIM, AFK_SEBEB = True, event.pattern_match.group(1)
        await event.edit(f"💤 AFK aktiv. Səbəb: {AFK_SEBEB}")

@client.on(events.NewMessage(incoming=True))
async def afk_cavab(event):
    if AFK_REJIM and event.is_private:
        await event.respond(f"🤖 AFK-yam. Səbəb: {AFK_SEBEB}")

@client.on(events.NewMessage(pattern=r'\.online'))
async def afk_deaktiv(event):
    global AFK_REJIM
    if event.out:
        AFK_REJIM = False
        await event.edit("✅ AFK söndürüldü.")

@client.on(events.NewMessage(incoming=True))
async def auto_downloader(event):
    text = event.text
    if not text or not any(site in text for site in ["instagram.com", "tiktok.com", "youtube.com"]): return
    status_msg = await event.reply("📥 Yüklenir...")
    if not os.path.exists("downloads"): os.makedirs("downloads")
    file_path = f'downloads/{event.id}.mp4'
    try:
        with yt_dlp.YoutubeDL({'format': 'best', 'outtmpl': file_path, 'quiet': True}) as ydl: ydl.download([text])
        await event.reply("ᎻᎢ ᏌᏚᎬᎡᏴOᎢ 🗿", file=file_path)
        await status_msg.delete()
    except: await status_msg.edit("❌ Xəta.")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@client.on(events.NewMessage(pattern=r'\.pluginyukle'))
async def plugin_yukle(event):
    if not event.out or not event.is_reply: return await event.edit("❌ Fayla reply at!")
    reply_message = await event.get_reply_message()
    if reply_message.file and reply_message.file.name.endswith(".py"):
        p_name = reply_message.file.name
        p_path = os.path.join(PLUGINS_DIR, p_name)
        content = await client.download_media(reply_message, bytes)
        await plugins_db.update_one({"name": p_name}, {"$set": {"content": content}}, upsert=True)
        with open(p_path, "wb") as f: f.write(content)
        await event.edit(f"✅ **ᎻᎢ ᏌᏚᎬᎡᏴOᎢ:** {p_name} yükləndi!")
        os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern=r'\.saat'))
async def canli_saat(event):
    if event.out:
        for _ in range(5):
            await event.edit(f"🕒 **Saat:** `{time.strftime('%H:%M:%S')}`")
            await asyncio.sleep(1)

@client.on(events.NewMessage(pattern=r'\.ters(?:\s+(.*))?'))
async def ters_cevir(event):
    if not event.out: return
    text = event.pattern_match.group(1)
    if event.is_reply: text = (await event.get_reply_message()).text
    if text: await event.edit(text[::-1])

@client.on(events.NewMessage(pattern=r'\.del'))
async def mesaj_sil(event):
    if event.out and event.is_reply:
        await (await event.get_reply_message()).delete(); await event.delete()

async def main():
    await client.start()
    async for plugin in plugins_db.find():
        p_path = os.path.join(PLUGINS_DIR, plugin['name'])
        with open(p_path, "wb") as f: f.write(plugin['content'])
        try:
            spec = importlib.util.spec_from_file_location(plugin['name'][:-3], p_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except: continue
    print("🚀 HT USERBOT Hazırdır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
