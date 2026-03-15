import os
import asyncio
import importlib
import importlib.util
import time
import ast
import sys
import random
import wikipedia
import requests
import yt_dlp
import motor.motor_asyncio
from gtts import gTTS
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
MONGO_URL = os.environ.get("MONGO_URL") 
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# MongoDB Bağlantısı
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]
config_db = db["config"] 

# Client-lər
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
tgbot = TelegramClient("bot_session", API_ID, API_HASH)

# Qlobal dəyişənlər
AFK_REJIM = False
AFK_SEBEB = ""
TAG_REJIM = True
PLUGINS_DIR = "plugins"
FILTERS = {}
BOT_USERNAME = "" 

if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# --- KOMANDA İZAHLARI (SİLMƏDİM) ---
COMMAND_DETAILS = {
    "ping": "🚀 **Ping:** Botun cavab sürətini ölçür.",
    "id": "🆔 **ID:** İstifadəçinin və ya reply atılan şəxsin ID-sini göstərir.",
    "etiraf": "💭 **Etiraf:** Bot təsadüfi bir etiraf mesajı göndərir.",
    "tagall": "📣 **TagAll:** Qrupdakı hamını etiketləyir.",
    "wiki": "📚 **Wiki:** Wikipedia-da axtarış edir.",
    "hava": "🌡 **Hava:** Şəhər üzrə hava proqnozu.",
    "shans": "🎲 **Şans:** Şans faizinizi göstərir.",
    "bom": "💣 **BOM:** Partlayış effekti yaradır.",
    "dice": "🎲 **Dice:** Təsadüfi oyun ikonları göndərir.",
    "yazi": "✨ **Yazı:** Yazını fərqli şriftə salır.",
    "tercume": "🌐 **Tərcümə:** Mesajı başqa dilə çevirir.",
    "ses": "🎙 **Səs:** Yazını səsə çevirir.",
    "afk": "💤 **AFK:** Avtomatik cavab rejimini açır.",
    "online": "✅ **Online:** AFK rejimini söndürür.",
    "saat": "🕒 **Saat:** Canlı saatı göstərir.",
    "ters": "🔄 **Tərs:** Yazını tərsinə çevirir.",
    "del": "🗑 **Sil:** Mesajı dərhal silir.",
    "pluginyukle": "🔌 **Plugin:** Yeni plugin əlavə edir.",
    "ban": "🚫 **Ban:** İstifadəçini birdəfəlik ban edir.",
    "kick": "👞 **Kick:** İstifadəçini qrupdan atır."
}

# --- MÖHTƏŞƏM ASENA MENYUSU (VİA BOT YAZISI OLMADAN) ---
@client.on(events.NewMessage(pattern=r'\.hthelp'))
async def help_menu(event):
    if not event.out: return
    try:
        me_bot = await tgbot.get_me()
        # Userbot arxa fonda botun inline funksiyasını çağırır
        results = await client.inline_query(me_bot.username, "menu")
        # XƏTA BURADA İDİ: results[0].click istifadə edərək mesajı sənin adından "via-sız" atırıq
        await results[0].click(event.chat_id, reply_to=event.reply_to_msg_id, hide_via=True)
        await event.delete()
    except Exception as e:
        await event.edit(f"❌ Menyu xətası: {e}\n@BotFather-də 'Inline Mode'u açın.")

@tgbot.on(events.InlineQuery())
async def inline_handler(event):
    me = await client.get_me()
    if event.sender_id != me.id: return
    
    query = event.query.query
    builder = event.builder
    
    if query == "menu":
        buttons = [
            [Button.inline("🛠 Komandalar", data="view_cmds"), Button.inline("🔌 Pluginlər", data="view_plugs")],
            [Button.url("📢 HT Kanal", url="https://t.me/Kullaniciadidi"), Button.inline("❌ Bağla", data="close_m")]
        ]
        res = builder.article(title="HT Menu", text="✨ **HT USERBOT | İdarə Paneli**\n\nSistem aktivdir. Aşağıdakı bölmələri seçin:", buttons=buttons)
        await event.answer([res])

@tgbot.on(events.CallbackQuery())
async def callback_handler(event):
    me = await client.get_me()
    if event.sender_id != me.id: return
    data = event.data.decode("utf-8")

    if data == "view_cmds":
        cmd_buttons = []
        keys = list(COMMAND_DETAILS.keys())
        for i in range(0, len(keys), 2):
            row = [Button.inline(f"🔹 {keys[i]}", data=f"info_{keys[i]}")]
            if i + 1 < len(keys): row.append(Button.inline(f"🔹 {keys[i+1]}", data=f"info_{keys[i+1]}"))
            cmd_buttons.append(row)
        cmd_buttons.append([Button.inline("⬅️ Geri", data="back_to_main")])
        await event.edit("🛠 **Sistem Komandaları:**", buttons=cmd_buttons)

    elif data == "view_plugs":
        plugin_buttons = []
        if os.path.exists("plugins"):
            files = [f[:-3] for f in os.listdir("plugins") if f.endswith(".py") and f != "__init__.py"]
            for i in range(0, len(files), 2):
                row = [Button.inline(f"📦 {files[i]}", data=f"pinfo_{files[i]}")]
                if i + 1 < len(files): row.append(Button.inline(f"📦 {files[i+1]}", data=f"pinfo_{files[i+1]}"))
                plugin_buttons.append(row)
        if not plugin_buttons: return await event.answer("📭 Plugin yoxdur!", alert=True)
        plugin_buttons.append([Button.inline("⬅️ Geri", data="back_to_main")])
        await event.edit("🔌 **Yüklənmiş Pluginlər:**", buttons=plugin_buttons)

    elif data.startswith("info_"):
        cmd = data.split("_")[1]
        desc = COMMAND_DETAILS.get(cmd, "Məlumat yoxdur.")
        await event.edit(f"🔍 **Komanda:** `.{cmd}`\n\n{desc}", buttons=[[Button.inline("⬅️ Geri", data="view_cmds")]])

    elif data == "back_to_main":
        await event.edit("✨ **HT USERBOT | İdarə Paneli**", buttons=[
            [Button.inline("🛠 Komandalar", data="view_cmds"), Button.inline("🔌 Pluginlər", data="view_plugs")],
            [Button.inline("❌ Bağla", data="close_m")]
        ])
    elif data == "close_m": await event.delete()

# --- SƏNİN DİGƏR BÜTÜN FUNKSİYALARIN (Hec nə silinmədi) ---

@client.on(events.NewMessage(pattern=r'\.htlive'))
async def htlive(event):
    if event.out:
        res = await client.get_me()
        font_text = f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ [{res.first_name}](tg://user?id={res.id}) ϋçϋи αктινdιя"
        await event.edit(f"🚀 {font_text}")

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

# --- DUZELTILMIS WIKI ---
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

@client.on(events.NewMessage(pattern=r'\.ses(?:\s+(\w+))?(?:\s+(.*))?'))
async def intelligent_tts(event):
    if not event.out: return
    arg1 = event.pattern_match.group(1)
    arg2 = event.pattern_match.group(2)
    target_lang = "tr"; text_to_process = ""
    if event.is_reply:
        reply_msg = await event.get_reply_message(); text_to_process = reply_msg.text
        if arg1 and len(arg1) <= 4: target_lang = arg1
    else:
        if arg1 and arg2: target_lang, text_to_process = arg1, arg2
        elif arg1: text_to_process = arg1
    if not text_to_process: return await event.edit("❌ Mətn yoxdur.")
    await event.edit("🎙 Hazırlanır...")
    try:
        tts = gTTS(text=text_to_process, lang="tr")
        tts.save("voice.mp3")
        await client.send_file(event.chat_id, "voice.mp3", voice_note=True)
        await event.delete()
    except: await event.edit("❌ Səs xətası.")

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

# --- AUTO DOWNLOADER (ORİJİNAL) ---
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

# --- YENİ ADMİN PLUGİNLƏRİ (DEDİYİN KİMİ 2 DƏNƏ) ---
@client.on(events.NewMessage(pattern=r'\.ban'))
async def ban_user(event):
    if not event.out or not event.is_group: return
    r = await event.get_reply_message()
    if r:
        await client.edit_permissions(event.chat_id, r.sender_id, view_messages=False)
        await event.edit("🚫 İstifadəçi ban edildi!")

@client.on(events.NewMessage(pattern=r'\.kick'))
async def kick_user(event):
    if not event.out or not event.is_group: return
    r = await event.get_reply_message()
    if r:
        await client.kick_participant(event.chat_id, r.sender_id)
        await event.edit("👞 İstifadəçi qrupdan çıxarıldı!")

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
        await (await event.get_reply_message()).delete()
        await event.delete()

@client.on(events.NewMessage(pattern=r'\.pluginyukle'))
async def plugin_yukle(event):
    if not event.out or not event.is_reply: return
    reply_message = await event.get_reply_message()
    if reply_message.file and reply_message.file.name.endswith(".py"):
        p_name = reply_message.file.name
        p_path = os.path.join(PLUGINS_DIR, p_name)
        content = await client.download_media(reply_message, bytes)
        await plugins_db.update_one({"name": p_name}, {"$set": {"content": content}}, upsert=True)
        with open(p_path, "wb") as f: f.write(content)
        await event.edit(f"✅ {p_name} yükləndi!")
        os.execl(sys.executable, sys.executable, *sys.argv)

# --- MAIN ---
async def main():
    await client.start()
    await tgbot.start(bot_token=BOT_TOKEN)
    
    async for p in plugins_db.find():
        p_path = os.path.join(PLUGINS_DIR, p['name'])
        with open(p_path, "wb") as f: f.write(p['content'])
        try:
            spec = importlib.util.spec_from_file_location(p['name'][:-3], p_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except: continue
            
    print("✅ HT USERBOT ONLINE!")
    await asyncio.gather(client.run_until_disconnected(), tgbot.run_until_disconnected())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
