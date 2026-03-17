import os
import asyncio
import time
import random
import wikipedia
import sys
import subprocess
import requests
import yt_dlp
import motor.motor_asyncio
import importlib.util
import sys
from pyrogram import Client, filters, enums, idle
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)
from pyrogram.errors import FloodWait, PeerIdInvalid, RPCError
from deep_translator import GoogleTranslator
from gtts import gTTS

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URL = os.environ.get("MONGO_URL")

# Dizayn Ayarları
HELP_IMG = "https://files.catbox.moe/34xlvu.jpg" 
KANAL_URL = "https://t.me/ht_bots"
KANAL_USER = "@ht_bots"

# MongoDB Bağlantısı
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]

import os
from pyrogram import Client, idle

# 1. Dəyişənləri sistemdən (Heroku) çəkirik
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN") # Köməkçi bot üçün mütləq lazımdır

# 2. USERBOT (Sənin atdığın stringlə işləyən hissə)
app = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

# 3. KÖMƏKÇİ BOT (Logda xəta verən 'bot' budur)
bot = Client(
    "helper_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Qlobal dəyişənlər
AFK_REJIM = False
AFK_SEBEB = ""
TAG_REJIM = True
FILTERS = {}
ORIGINAL_PROFILE = {} # Klonlama yaddaşı

# --- KOMANDA İZAHLARI ---
COMMAND_DETAILS = {
    "ping": "🚀 Botun sürətini ölçür.",
    "id": "🆔 İstifadəçi ID-sini göstərir.",
    "etiraf": "💭 Təsadüfi etiraf mesajı göndərir.",
    "tagall": "📣 Hamını etiketləyir.",
    "wiki": "📚 Wikipedia axtarışı.",
    "hava": "🌡 Hava proqnozu.",
    "shans": "🎲 Şans faizi.",
    "bom": "💣 Partlayış effekti.",
    "dice": "🎲 Təsadüfi oyun ikonları.",
    "yazi": "✨ Şrifti dəyişir.",
    "tercume": "🌐 Mesajı tərcümə edir.",
    "ses": "🎙 Yazını səsə çevirir.",
    "afk": "💤 AFK rejimini açır.",
    "online": "✅ AFK-nı söndürür.",
    "htclon": "👤 Profil klonlayır (reply).",
    "unhtclon": "🔄 Klonu ləğv edir.",
    "saat": "🕒 Canlı saat.",
    "ters": "🔄 Yazını tərsinə çevirir.",
    "del": "🗑 Mesajı silir.",
    "ban": "🚫 İstifadəçini ban edir.",
    "kick": "👞 İstifadəçini qrupdan atır.",
    "pluginyukle": "🔌 Yeni modul (.py) əlavə edir."
}

# --- AVTOMATİK SETUP SİSTEMİ (BIO SÖHBƏTİ DÜZƏLDİLDİ) ---
async def setup_account_automatically():
    try:
        me = await app.get_me()
        
        # Köməkçi Botun Profilini Tənzimləyirik (Sənin biona toxunmur)
        try:
            bot_about = f"HT Userbot köməkçisidir. Sahibi: {me.first_name}"
            await bot.set_bot_about(bot_about)
        except: pass

        # 2. Avtomatik Log Qrupu Yaratma
        settings = await db.settings.find_one({"type": "log_group"})
        if not settings:
            try:
                group_name = f"HT LOGS | {me.first_name}"
                group_desc = f"Bu qrup {me.first_name} üçün HT Userbot tərəfindən avtomatik yaradılmışdır.\nKanal: {KANAL_USER}"
                new_group = await app.create_supergroup(group_name, group_desc)
                
                await db.settings.update_one(
                    {"type": "log_group"}, 
                    {"$set": {"group_id": new_group.id}}, 
                    upsert=True
                )
                
                await app.send_message(
                    "me", 
                    f"✅ **HT USERBOT | AVTO SETUP**\n\n"
                    f"🚀 Sizin üçün rəsmi Log qrupu yaradıldı.\n"
                    f"🆔 **ID:** `{new_group.id}`\n"
                    f"👤 **Sahib:** {me.first_name}\n"
                )
            except Exception as e:
                print(f"Log qrupu xətası: {e}")
    except Exception as e:
        print(f"Auto-setup xətası: {e}")

# --- PROFIL KLONLAMA KOMANDALARI ---
@app.on_message(filters.command("htclon", prefixes=".") & filters.me)
async def clone_profile(client, message):
    if not message.reply_to_message:
        return await message.edit("❌ Klonlamaq üçün birinə reply atın!")
    target = message.reply_to_message.from_user
    await message.edit("👤 **Profil klonlanır...**")
    try:
        if not ORIGINAL_PROFILE:
            me = await client.get_me()
            full_me = await client.get_chat("me")
            ORIGINAL_PROFILE["f"] = me.first_name
            ORIGINAL_PROFILE["l"] = me.last_name or ""
            ORIGINAL_PROFILE["b"] = full_me.bio or ""
            async for p in client.get_chat_photos("me", limit=1):
                ORIGINAL_PROFILE["p"] = await client.download_media(p.file_id)

        full_target = await client.get_chat(target.id)
        await client.update_profile(first_name=target.first_name, last_name=target.last_name or "", bio=full_target.bio or "")
        async for p in client.get_chat_photos(target.id, limit=1):
            photo = await client.download_media(p.file_id)
            await client.set_profile_photo(photo=photo)
        await message.edit(f"✅ **{target.first_name}** profili klonlandı!")
    except Exception as e: await message.edit(f"❌ Xəta: {e}")

@app.on_message(filters.command("unhtclon", prefixes=".") & filters.me)
async def restore_profile(client, message):
    if not ORIGINAL_PROFILE: return await message.edit("❌ Yaddaşda köhnə profil yoxdur.")
    await message.edit("🔄 **Profil bərpa edilir...**")
    try:
        await client.update_profile(first_name=ORIGINAL_PROFILE["f"], last_name=ORIGINAL_PROFILE["l"], bio=ORIGINAL_PROFILE["b"])
        if "p" in ORIGINAL_PROFILE: await client.set_profile_photo(photo=ORIGINAL_PROFILE["p"])
        await message.edit("✅ Profil orijinal vəziyyətinə qaytarıldı!")
    except Exception as e: await message.edit(f"❌ Xəta: {e}")

# --- DİNAMİK PLUGİN YÜKLƏYİCİ ---
async def load_plugin_dynamically(name, path):
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
        
        # AVTOMATIK HELP: Faylın adını komanda kimi, 
        # faylın içindəki ilk rəyi (əgər varsa) isə izah kimi götürür.
        description = module.__doc__ if module.__doc__ else f"{name} modulu yükləndi."
        COMMAND_DETAILS[name] = description
        
        return True
    except Exception as e:
        print(f"❌ Plugin oxunarkən xəta: {e}")
        return False
                
@app.on_message(filters.command("pluginyukle", prefixes=".") & filters.me)
async def install_plugin(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.edit("❌ Lütfən bir `.py` faylına reply atın!")
    
    doc = message.reply_to_message.document
    if not doc.file_name.endswith(".py"):
        return await message.edit("❌ Sadece `.py` faylları yüklənə bilər.")

    await message.edit("📥 **Modul bazaya yazılır və aktivləşdirilir...**")
    if not os.path.exists("plugins"): os.makedirs("plugins")
    loc = os.path.join("plugins", doc.file_name)
    await client.download_media(message.reply_to_message, file_name=loc)
    
    with open(loc, "r", encoding="utf-8") as f:
        code = f.read()
    await plugins_db.update_one({"name": doc.file_name}, {"$set": {"code": code}}, upsert=True)
    
    success = await load_plugin_dynamically(doc.file_name.replace(".py", ""), loc)
    
    if success:
        await message.edit(f"✅ **HT USERBOT**\n\n📦 Modul: `{doc.file_name}`\n🚀 Status: **Aktivdir**\n\n_Restart etməyə ehtiyac yoxdur._")
    else:
        await message.edit(f"⚠️ Modul bazaya yazıldı, lakin işə salınarkən xəta baş verdi.")

@app.on_message(filters.command("update", prefixes=".") & filters.me)
async def update_bot(client, message):
    msg = await message.edit("🔄 **Güncəlləmə yoxlanılır...**")
    try:
        import subprocess
        process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if "Already up to date." in stdout.decode():
            return await msg.edit("✅ **Bot artıq ən son versiyadadır.**")
        
        # Yenilənmə bitəndə bu mesajın ID-sini yadda saxlayırıq ki, açılanda redaktə edək
        await msg.edit(f"✅ **Güncəlləndi!** Bot restart olunur...\n\n`{stdout.decode()[:100]}`")
        
        # Hansı qrupda və hansı mesajı redaktə edəcəyimizi qeyd edirik
        with open("update.txt", "w") as f:
            f.write(f"{msg.chat.id}\n{msg.id}")

        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await msg.edit(f"❌ **Güncəlləmə zamanı xəta:** `{e}`")
        
# --- YARDIM MENYUSU ---
@app.on_message(filters.command("hthelp", prefixes=".") & filters.me)
async def help_menu(client, message):
    try:
        results = await client.get_inline_bot_results(bot.me.username, "menu")
        await client.send_inline_bot_result(message.chat.id, results.query_id, results.results[0].id)
        await message.delete()
    except Exception:
        help_text = f"┏━━━━━━━━━━━━━━┓\n  ✨ **HT USERBOT | MENU**\n┗━━━━━━━━━━━━━━┛\n\n"
        for cmd, desc in COMMAND_DETAILS.items():
            help_text += f"▪️ `.{cmd}` : {desc}\n"
        help_text += f"\n📢 **Kanal:** {KANAL_USER}"
        await message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL)]]))

@bot.on_inline_query()
async def inline_handler(client, query):
    if query.query == "menu":
        buttons = [
            [InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")],
            [InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL), InlineKeyboardButton("❌ Bağla", callback_data="close_m")]
        ]
        await query.answer([
            InlineQueryResultArticle(
                title="HT Userbot Menu",
                description="İdarəetmə Paneli",
                thumb_url=HELP_IMG,
                input_message_content=InputTextMessageContent(
                    f"[\u200b]({HELP_IMG})✨ **HT USERBOT | İdarə Paneli**\n\n👤 **İstifadəçi:** {app.me.first_name}\n🛡 **Sistem:** Aktiv\n📢 **Kanal:** {KANAL_USER}\n\n_Komandalar üçün aşağıdakı düyməyə vurun._",
                    parse_mode=enums.ParseMode.MARKDOWN
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        ], cache_time=1)

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    if callback_query.from_user.id != app.me.id:
        return await callback_query.answer("⚠️ Bu menyu yalnız bot sahibinə məxsusdur!", show_alert=True)      
    data = callback_query.data
    main_text = f"[\u200b]({HELP_IMG})✨ **HT USERBOT | İdarə Paneli**\n\n👤 **İstifadəçi:** {app.me.first_name}\n🛡 **Sistem:** Aktiv\n📢 **Kanal:** {KANAL_USER}\n\n_Komandalar üçün aşağıdakı düyməyə vurun._"
    main_buttons = [
        [InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")],
        [InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL), InlineKeyboardButton("❌ Bağla", callback_data="close_m")]
    ]

    if data == "view_cmds":
        cmd_buttons = []
        keys = list(COMMAND_DETAILS.keys())
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(f"🔹 {keys[i]}", callback_data=f"info_{keys[i]}")]
            if i + 1 < len(keys): row.append(InlineKeyboardButton(f"🔹 {keys[i+1]}", callback_data=f"info_{keys[i+1]}"))
            cmd_buttons.append(row)
        cmd_buttons.append([InlineKeyboardButton("⬅️ Geri", callback_data="back")])
        await callback_query.edit_message_text(f"[\u200b]({HELP_IMG})🛠 **Komanda Siyahısı:**", reply_markup=InlineKeyboardMarkup(cmd_buttons))
    
    elif data.startswith("info_"):
        cmd = data.split("_")[1]
        desc = COMMAND_DETAILS.get(cmd, "Məlumat yoxdur.")
        await callback_query.edit_message_text(f"[\u200b]({HELP_IMG})🔍 **Komanda:** `.{cmd}`\n\n{desc}\n\n🛡 {KANAL_USER}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="view_cmds")]]))
    
    elif data == "back":
        await callback_query.edit_message_text(main_text, reply_markup=InlineKeyboardMarkup(main_buttons))
    
    elif data == "close_m":
        await callback_query.message.delete()

@app.on_message(filters.command("htlive", prefixes=".") & filters.me)
async def htlive(client, message):
    res = client.me
    font_text = f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ [{res.first_name}](tg://user?id={res.id}) ϋçϋи αктινdιя"
    await message.edit(f"🚀 {font_text}")

@app.on_message(filters.command("filter", prefixes=".") & filters.me)
async def filter_add(client, message):
    if not message.reply_to_message: return await message.edit("❌ Filter üçün bir mesaja reply at!")
    keyword = message.text.split(None, 1)[1].lower()
    chat_id = message.chat.id
    if chat_id not in FILTERS: FILTERS[chat_id] = {}
    FILTERS[chat_id][keyword] = message.reply_to_message.id
    await message.edit(f"✅ `{keyword}` filteri aktiv edildi!")

@app.on_message(filters.command("stopfilter", prefixes=".") & filters.me)
async def filter_stop(client, message):
    if len(message.command) < 2: return
    keyword = message.text.split(None, 1)[1].lower()
    if message.chat.id in FILTERS and keyword in FILTERS[message.chat.id]:
        del FILTERS[message.chat.id][keyword]
        await message.edit(f"🗑 `{keyword}` filteri silindi.")
    else: await message.edit("❌ Tapılmadı.")

@app.on_message(filters.incoming & filters.text & ~filters.me)
async def filter_handler(client, message):
    chat_id = message.chat.id
    if chat_id in FILTERS:
        word = message.text.lower()
        if word in FILTERS[chat_id]: await message.reply_to_message(FILTERS[chat_id][word])

@app.on_message(filters.command("ping", prefixes=".") & filters.me)
async def ping(client, message):
    start = time.time()
    await message.edit("🚀...")
    ms = round((time.time() - start) * 1000)
    await message.edit(f"⚡ **ᎻᎢ ᏌᏚᎬᎡᏴOᎢ Sürəti:** `{ms}ms`")

@app.on_message(filters.command("id", prefixes=".") & filters.me)
async def get_id(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.edit(f"🆔 **ID:** `{user.id}`\n👤 **Ad:** {user.first_name}")
    else: await message.edit(f"🆔 **Sənin ID-in:** `{message.from_user.id}`")

@app.on_message(filters.command("etiraf", prefixes=".") & filters.me)
async def etiraf(client, message):
    etiraflar = ["Dünən gizlicə soyuducunu boşaltmışam... 🤫", "Mən əslində bir bot deyiləm 🛸"]
    await message.edit(f"💭 **Etirafım:** {random.choice(etiraflar)}")

@app.on_message(filters.command("tagall", prefixes=".") & filters.me)
async def tagall(client, message):
    global TAG_REJIM
    TAG_REJIM = True
    sebeb = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    await message.delete()
    try:
        async for member in client.get_chat_members(message.chat.id):
            if not TAG_REJIM: break
            if not member.user.is_bot:
                await client.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {sebeb}")
                await asyncio.sleep(1.5)
    except FloodWait as e: await asyncio.sleep(e.value)

@app.on_message(filters.command("stoptag", prefixes=".") & filters.me)
async def stoptag(client, message):
    global TAG_REJIM
    TAG_REJIM = False
    await message.edit("✅ Tag dayandırıldı.")

@app.on_message(filters.command("hava", prefixes=".") & filters.me)
async def hava(client, message):
    if len(message.command) < 2: return
    city = message.text.split(None, 1)[1]
    await message.edit(f"🌡 **Şəhər:** `{city}` üçün hava axtarılır...")

@app.on_message(filters.command("wiki", prefixes=".") & filters.me)
async def wiki(client, message):
    if len(message.command) < 2: return
    query = message.text.split(None, 1)[1]
    try:
        wikipedia.set_lang("az")
        res = wikipedia.summary(query, sentences=2)
        await message.edit(f"📚 **Wiki:** {res}")
    except: await message.edit("❌ Tapılmadı.")

@app.on_message(filters.command("shans", prefixes=".") & filters.me)
async def shans(client, message): await message.edit(f"🎲 Sənin şansın: **%{random.randint(0, 100)}**")

@app.on_message(filters.command("bom", prefixes=".") & filters.me)
async def bom(client, message):
    await message.edit("💣"); await asyncio.sleep(0.8); await message.edit("💥 PARTLADI!")

@app.on_message(filters.command("dice", prefixes=".") & filters.me)
async def dice(client, message): await message.edit(random.choice(["🎲", "🎯", "🏀", "⚽"]))

@app.on_message(filters.command("yazi", prefixes=".") & filters.me)
async def yazi(client, message):
    if len(message.command) < 2: return
    metn = message.text.split(None, 1)[1]
    font = metn.replace('a', 'α').replace('e', 'є').replace('i', 'ι')
    await message.edit(f"✨ {font}")

@app.on_message(filters.command("tercume", prefixes=".") & filters.me)
async def tercume(client, message):
    if not message.reply_to_message: return
    lang = message.command[1] if len(message.command) > 1 else "az"
    res = GoogleTranslator(source='auto', target=lang).translate(message.reply_to_message.text)
    await message.edit(f"🌐 **Tərcümə:**\n{res}")

@app.on_message(filters.command("ses", prefixes=".") & filters.me)
async def ses(client, message):
    text = ""
    if len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    
    if not text: 
        return await message.edit("❌ Mətn daxil edin və ya mesajı reply edin.")
    
    await message.edit("🎙 **Səs emal olunur...**")
    
    try:
        tts = gTTS(text=text, lang="tr")
        tts.save("voice.mp3")
        await client.send_voice(
            chat_id=message.chat.id, 
            voice="voice.mp3",
            reply_to_message_id=message.reply_to_message.id if message.reply_to_message else None
        )
        await message.delete() 
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")
    finally:
        if os.path.exists("voice.mp3"): os.remove("voice.mp3")

@app.on_message(filters.command("afk", prefixes=".") & filters.me)
async def afk_on(client, message):
    global AFK_REJIM, AFK_SEBEB
    AFK_REJIM = True
    AFK_SEBEB = message.text.split(None, 1)[1] if len(message.command) > 1 else "Yoxam."
    await message.edit(f"💤 AFK aktiv: {AFK_SEBEB}")

@app.on_message(filters.command("online", prefixes=".") & filters.me)
async def afk_off(client, message):
    global AFK_REJIM
    AFK_REJIM = False
    await message.edit("✅ Onlaynam!")

@app.on_message(filters.incoming & filters.private & ~filters.me)
async def afk_handler(client, message):
    if AFK_REJIM: await message.reply(f"🤖 AFK-yam: {AFK_SEBEB}")

@app.on_message(filters.incoming & filters.text & ~filters.me)
async def dl_handler(client, message):
    if any(x in message.text for x in ["instagram.com", "tiktok.com", "youtube.com"]):
        try:
            path = f"downloads/{message.id}.mp4"
            with yt_dlp.YoutubeDL({'format': 'best', 'outtmpl': path, 'quiet': True}) as ydl: ydl.download([message.text])
            await message.reply_video(path, caption=f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ 🗿\n{KANAL_USER}")
            if os.path.exists(path): os.remove(path)
        except Exception: pass 

@app.on_message(filters.command("ban", prefixes=".") & filters.me)
async def ban(client, message):
    if message.reply_to_message:
        await client.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.edit("🚫 Ban edildi.")

@app.on_message(filters.command("kick", prefixes=".") & filters.me)
async def kick(client, message):
    if message.reply_to_message:
        await client.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.edit("👞 Atıldı.")

@app.on_message(filters.command("saat", prefixes=".") & filters.me)
async def saat(client, message):
    for _ in range(5):
        await message.edit(f"🕒 **Saat:** `{time.strftime('%H:%M:%S')}`")
        await asyncio.sleep(1)

@app.on_message(filters.command("ters", prefixes=".") & filters.me)
async def ters(client, message):
    text = message.reply_to_message.text if message.reply_to_message else (message.text.split(None, 1)[1] if len(message.command) > 1 else None)
    if text: await message.edit(text[::-1])

@app.on_message(filters.command("del", prefixes=".") & filters.me)
async def delete_msg(client, message):
    if message.reply_to_message:
        await message.reply_to_message.delete()
        await message.delete()
# --- SİSTEM BAŞLATMA (YENİLƏNMİŞ RUN FUNKSİYASI) ---
async def run():
    await app.start()
    await bot.start()
    
    # UPDATE MESAJI YOXLANISI (Restartdan sonra redaktə edir)
    if os.path.exists("update.txt"):
        try:
            with open("update.txt", "r") as f:
                data = f.readlines()
                if len(data) == 2:
                    chat_id = int(data[0].strip())
                    msg_id = int(data[1].strip())
                    # Köhnə mesajı tapıb uğurla açıldığını bildirir
                    await app.edit_message_text(chat_id, msg_id, "✅ **Bot uğurla güncəlləndi və yenidən başladıldı!**")
            os.remove("update.txt") # İş bitdikdən sonra müvəqqəti faylı silirik
        except Exception as e:
            print(f"Update mesaj xətası: {e}")

    # Sənin orijinal funksiyaların (Orijinal koddakı kimi qaldı)
    await setup_account_automatically() 
    await load_stored_plugins() 
    
    print(f"✅ HT USERBOT ONLINE!")
    await idle()
    await app.stop()
    await bot.stop()

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    # Botu işə salırıq
    asyncio.get_event_loop().run_until_complete(run())
