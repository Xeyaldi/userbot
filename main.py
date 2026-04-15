import os
import asyncio
import time
import re
import random
import wikipedia
import sys
import subprocess
import requests
import yt_dlp
import motor.motor_asyncio
import importlib.util
import logging
from pyrogram import Client, filters, enums, idle
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
    MessageEntity
)
from pyrogram.errors import FloodWait, PeerIdInvalid, RPCError
from pyrogram.enums import ParseMode, MessageEntityType
from deep_translator import GoogleTranslator
from gtts import gTTS

# --- KONFİQURASİYA ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URL = os.environ.get("MONGO_URL")

HELP_IMG = "https://files.catbox.moe/34xlvu.jpg"
KANAL_URL = "https://t.me/ht_bots"
KANAL_USER = "@ht_bots"

# MongoDB
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]

# Pyrogram-ın daxili xəta loqlarını söndürürük
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pyrogram.session.messenger").setLevel(logging.CRITICAL)

# --- CLIENT-LƏR ---
app = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

bot = Client(
    name="helper_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Bütün pluginlərdə istifadə üçün qısa funksiya
import builtins
builtins.P = lambda eid, alt="✨": f"<tg-emoji emoji-id='{eid}'>{alt}</tg-emoji>"
builtins.HTML = ParseMode.HTML

@app.on_message(filters.command("pe", prefixes=".") & filters.me)
async def send_premium_emoji(client, message):
    """
    Premium emoji göndər.
    İstifadə: .pe fire  |  .pe heart  |  .pe star  |  .pe crown
    Siyahı: .pe list
    """
    args = message.text.split(None, 1)
    if len(args) < 2:
        keys = "  |  ".join(PREMIUM_EMOJIS.keys())
        return await message.edit(f"❌ İstifadə: `.pe <ad>`\n\n📋 **Mövcud:** {keys}")

    key = args[1].strip().lower()

    if key == "list":
        text = "📋 **Premium Emoji Siyahısı:**\n\n"
        for name in PREMIUM_EMOJIS:
            text += f"• `.pe {name}`\n"
        return await message.edit(text)

    doc_id = PREMIUM_EMOJIS.get(key)
    if not doc_id:
        keys = "  |  ".join(PREMIUM_EMOJIS.keys())
        return await message.edit(f"❌ Tapılmadı.\n📋 **Mövcud:** {keys}")

    await message.delete()
    emoji_html = make_premium_emoji(doc_id, "⭐")
    await client.send_message(
        message.chat.id,
        emoji_html,
        parse_mode=ParseMode.HTML
    )

@app.on_message(filters.command("petext", prefixes=".") & filters.me)
async def premium_emoji_with_text(client, message):
    """
    Mətn + premium emoji.
    İstifadə: .petext fire Salam dünya
    """
    args = message.text.split(None, 2)
    if len(args) < 3:
        return await message.edit("❌ İstifadə: `.petext <emoji_adı> <mətn>`\nNümunə: `.petext fire Salam!`")

    key = args[1].strip().lower()
    text = args[2].strip()

    doc_id = PREMIUM_EMOJIS.get(key)
    if not doc_id:
        keys = "  |  ".join(PREMIUM_EMOJIS.keys())
        return await message.edit(f"❌ Tapılmadı.\n📋 **Mövcud:** {keys}")

    await message.delete()
    emoji_html = make_premium_emoji(doc_id, "⭐")
    await client.send_message(
        message.chat.id,
        f"{emoji_html} {text}",
        parse_mode=ParseMode.HTML
    )

# --- QLOBAL DƏYİŞƏNLƏR ---
AFK_REJIM = False
AFK_SEBEB = ""
TAG_REJIM = True
FILTERS = {}
ORIGINAL_PROFILE = {}

# --- KOMANDA İZAHLARI ---
COMMAND_DETAILS = {
    "ping":           "🚀 Botun sürətini ölçür.",
    "id":             "🆔 İstifadəçi ID-sini göstərir.",
    "etiraf":         "💭 Təsadüfi etiraf mesajı göndərir.",
    "tagall":         "📣 Hamını etiketləyir.",
    "stoptag":        "🛑 Teqi dayandırır.",
    "wiki":           "📚 Wikipedia axtarışı.",
    "hava":           "🌡 Hava proqnozu.",
    "shans":          "🎲 Şans faizi.",
    "bom":            "💣 Partlayış effekti.",
    "dice":           "🎲 Təsadüfi oyun ikonları.",
    "yazi":           "✨ Şrifti dəyişir.",
    "tercume":        "🌐 Mesajı tərcümə edir.",
    "ses":            "🎙 Yazını səsə çevirir.",
    "afk":            "💤 AFK rejimini açır.",
    "online":         "✅ AFK-nı söndürür.",
    "htclon":         "👤 Profil klonlayır (reply).",
    "unhtclon":       "🔄 Klonu ləğv edir.",
    "saat":           "🕒 Canlı saat.",
    "ters":           "🔄 Yazını tərsinə çevirir.",
    "del":            "🗑 Mesajı silir.",
    "ban":            "🚫 İstifadəçini ban edir.",
    "kick":           "👞 İstifadəçini qrupdan atır.",
    "htplugininsall": "🔌 Yeni modul (.py) əlavə edir.",
    "hthelp":         "📋 Bu menyu.",
}

# --- PROFİL KLONLAMA ---
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
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")

@app.on_message(filters.command("unhtclon", prefixes=".") & filters.me)
async def restore_profile(client, message):
    if not ORIGINAL_PROFILE:
        return await message.edit("❌ Yaddaşda köhnə profil yoxdur.")
    await message.edit("🔄 **Profil bərpa edilir...**")
    try:
        await client.update_profile(first_name=ORIGINAL_PROFILE["f"], last_name=ORIGINAL_PROFILE["l"], bio=ORIGINAL_PROFILE["b"])
        if "p" in ORIGINAL_PROFILE:
            await client.set_profile_photo(photo=ORIGINAL_PROFILE["p"])
        await message.edit("✅ Profil orijinal vəziyyətinə qaytarıldı!")
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")

# --- DİNAMİK PLUGİN YÜKLƏYİCİ (RESTARSTSIZ) ---
async def load_plugin_dynamically(name, path):
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
        description = module.__doc__ if module.__doc__ else f"{name} modulu yükləndi."
        COMMAND_DETAILS[name] = description
        return True
    except Exception as e:
        print(f"❌ Plugin xətası: {e}")
        return False

async def load_stored_plugins():
    if not os.path.exists("plugins"):
        os.makedirs("plugins")
    async for plugin in plugins_db.find():
        try:
            name = plugin["name"]
            code = plugin["code"]
            path = os.path.join("plugins", name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            await load_plugin_dynamically(name.replace(".py", ""), path)
        except Exception as e:
            print(f"Plugin bərpa xətası: {e}")

@app.on_message(filters.command("htplugininsall", prefixes=".") & filters.me)
async def dynamic_plugin_installer(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.edit("❌ **Səhv:** Bir `.py` faylına cavab verin.")
    doc = message.reply_to_message.document
    if not doc.file_name.endswith(".py"):
        return await message.edit("❌ **Səhv:** Yalnız `.py` faylı yüklənə bilər.")
    if not os.path.exists("plugins"):
        os.makedirs("plugins")
    plugin_name = doc.file_name.replace(".py", "")
    plugin_path = os.path.join("plugins", doc.file_name)
    await message.edit(f"📥 **{doc.file_name}** analiz edilir...")
    try:
        await message.reply_to_message.download(file_name=plugin_path)
        cmd_info = []
        with open(plugin_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            match = re.search(r'command\("([^"]+)"', line)
            if match:
                cmd = match.group(1)
                comment = "İzah yoxdur."
                if i > 0 and "# İzah:" in lines[i - 1]:
                    comment = lines[i - 1].split("# İzah:")[1].strip()
                cmd_info.append(f"• `.{cmd}` - {comment}")
        cmd_text = "\n".join(cmd_info) if cmd_info else "• _Avtomatik modul._"

        # Kodu botu söndürmədən aktivləşdir
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in dir(module):
            val = getattr(module, attr)
            if hasattr(val, "handlers"):
                for handler, group in val.handlers:
                    app.add_handler(handler, group)

        # Baza saxla
        with open(plugin_path, "r", encoding="utf-8") as f:
            code = f.read()
        await plugins_db.update_one({"name": doc.file_name}, {"$set": {"code": code}}, upsert=True)

        await message.edit(
            f"✅ **HT USERBOT - YENİ MODUL**\n\n"
            f"📦 **Fayl:** `{doc.file_name}`\n"
            f"🛠 **Komandalar:**\n{cmd_text}\n\n"
            f"✨ _Modul aktiv edildi._"
        )
    except Exception as e:
        await message.edit(f"❌ **Modul yüklənmədi:** `{e}`")

# --- YARDIM MENYUSU ---
@app.on_message(filters.command("hthelp", prefixes=".") & filters.me)
async def help_menu(client, message):
    try:
        results = await client.get_inline_bot_results(bot.me.username, "menu")
        await client.send_inline_bot_result(message.chat.id, results.query_id, results.results[0].id)
        await message.delete()
    except Exception:
        help_text = f"┏━━━━━━━━━━━━━━┓\n ✨ **HT USERBOT | MENU**\n┗━━━━━━━━━━━━━━┛\n\n"
        for cmd, desc in COMMAND_DETAILS.items():
            help_text += f"▪️ `.{cmd}` : {desc}\n"
        help_text += f"\n📢 **Kanal:** {KANAL_USER}"
        await message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL)]]))

@bot.on_inline_query()
async def inline_handler(client, query):
    if query.query == "menu":
        buttons = [
            [InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")],
            [InlineKeyboardButton("💎 Premium Emoji", callback_data="view_pe")],
            [InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL), InlineKeyboardButton("❌ Bağla", callback_data="close_m")]
        ]
        await query.answer([
            InlineQueryResultArticle(
                title="HT Userbot Menu",
                description="İdarəetmə Paneli",
                thumb_url=HELP_IMG,
                input_message_content=InputTextMessageContent(
                    f"[\u200b]({HELP_IMG})✨ **HT USERBOT | İdarə Paneli**\n\n"
                    f"👤 **İstifadəçi:** {app.me.first_name}\n"
                    f"🛡 **Sistem:** Aktiv\n"
                    f"📢 **Kanal:** {KANAL_USER}\n\n"
                    f"_Komandalar üçün aşağıdakı düyməyə vurun._",
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
    main_text = (
        f"[\u200b]({HELP_IMG})✨ **HT USERBOT | İdarə Paneli**\n\n"
        f"👤 **İstifadəçi:** {app.me.first_name}\n"
        f"🛡 **Sistem:** Aktiv\n"
        f"📢 **Kanal:** {KANAL_USER}\n\n"
        f"_Komandalar üçün aşağıdakı düyməyə vurun._"
    )
    main_buttons = [
        [InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")],
        [InlineKeyboardButton("📢 RƏSMİ KANAL", url=KANAL_URL), InlineKeyboardButton("❌ Bağla", callback_data="close_m")]
    ]

    if data == "view_cmds":
        cmd_buttons = []
        keys = list(COMMAND_DETAILS.keys())
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(f"🔹 {keys[i]}", callback_data=f"info_{keys[i]}")]
            if i + 1 < len(keys):
                row.append(InlineKeyboardButton(f"🔹 {keys[i+1]}", callback_data=f"info_{keys[i+1]}"))
            cmd_buttons.append(row)
        cmd_buttons.append([InlineKeyboardButton("⬅️ Geri", callback_data="back")])
        await callback_query.edit_message_text(f"[\u200b]({HELP_IMG})🛠 **Komanda Siyahısı:**", reply_markup=InlineKeyboardMarkup(cmd_buttons))

    elif data == "view_pe":
        pe_text = f"[\u200b]({HELP_IMG})💎 **Premium Emoji Siyahısı:**\n\n"
        for name in PREMIUM_EMOJIS:
            pe_text += f"• `.pe {name}`\n"
        pe_text += "\n📝 Mətnlə: `.petext fire Salam!`"
        await callback_query.edit_message_text(pe_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]))

    elif data.startswith("info_"):
        cmd = data.split("_", 1)[1]
        desc = COMMAND_DETAILS.get(cmd, "Məlumat yoxdur.")
        await callback_query.edit_message_text(
            f"[\u200b]({HELP_IMG})🔍 **Komanda:** `.{cmd}`\n\n{desc}\n\n🛡 {KANAL_USER}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="view_cmds")]])
        )

    elif data == "back":
        await callback_query.edit_message_text(main_text, reply_markup=InlineKeyboardMarkup(main_buttons))

    elif data == "close_m":
        await callback_query.message.delete()

# --- PING ---
@app.on_message(filters.command("ping", prefixes=".") & filters.me)
async def ping(client, message):
    start = time.time()
    await message.edit("🚀...")
    ms = round((time.time() - start) * 1000)
    await message.edit(f"⚡ **ᎻᎢ ᏌᏚᎬᎡᏴOᎢ Sürəti:** `{ms}ms`")

# --- ID ---
@app.on_message(filters.command("id", prefixes=".") & filters.me)
async def get_id(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.edit(f"🆔 **ID:** `{user.id}`\n👤 **Ad:** {user.first_name}")
    else:
        await message.edit(f"🆔 **Sənin ID-in:** `{message.from_user.id}`")

# --- ETİRAF ---
@app.on_message(filters.command("etiraf", prefixes=".") & filters.me)
async def etiraf(client, message):
    etiraflar = ["Dünən gizlicə soyuducunu boşaltmışam... 🤫", "Mən əslində bir bot deyiləm 🛸"]
    await message.edit(f"💭 **Etirafım:** {random.choice(etiraflar)}")

# --- TAGALL ---
@app.on_message(filters.command("tagall", prefixes=".") & filters.me)
async def tagall(client, message):
    global TAG_REJIM
    TAG_REJIM = True
    sebeb = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    await message.delete()
    try:
        async for member in client.get_chat_members(message.chat.id):
            if not TAG_REJIM:
                break
            if not member.user.is_bot:
                await client.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {sebeb}")
                await asyncio.sleep(1.5)
    except FloodWait as e:
        await asyncio.sleep(e.value)

@app.on_message(filters.command("stoptag", prefixes=".") & filters.me)
async def stoptag(client, message):
    global TAG_REJIM
    TAG_REJIM = False
    await message.edit("✅ Tag dayandırıldı.")

# --- HAVA ---
@app.on_message(filters.command("hava", prefixes=".") & filters.me)
async def hava(client, message):
    if len(message.command) < 2:
        return
    city = message.text.split(None, 1)[1]
    await message.edit(f"🌡 **Şəhər:** `{city}` üçün hava axtarılır...")

# --- WİKİ ---
@app.on_message(filters.command("wiki", prefixes=".") & filters.me)
async def wiki(client, message):
    if len(message.command) < 2:
        return
    query = message.text.split(None, 1)[1]
    try:
        wikipedia.set_lang("az")
        res = wikipedia.summary(query, sentences=2)
        await message.edit(f"📚 **Wiki:** {res}")
    except:
        await message.edit("❌ Tapılmadı.")

# --- ŞANS ---
@app.on_message(filters.command("shans", prefixes=".") & filters.me)
async def shans(client, message):
    await message.edit(f"🎲 Sənin şansın: **%{random.randint(0, 100)}**")

# --- BOM ---
@app.on_message(filters.command("bom", prefixes=".") & filters.me)
async def bom(client, message):
    await message.edit("💣")
    await asyncio.sleep(0.8)
    await message.edit("💥 PARTLADI!")

# --- DICE ---
@app.on_message(filters.command("dice", prefixes=".") & filters.me)
async def dice(client, message):
    await message.edit(random.choice(["🎲", "🎯", "🏀", "⚽"]))

# --- YAZI ---
@app.on_message(filters.command("yazi", prefixes=".") & filters.me)
async def yazi(client, message):
    if len(message.command) < 2:
        return
    metn = message.text.split(None, 1)[1]
    font = metn.replace('a', 'α').replace('e', 'є').replace('i', 'ι')
    await message.edit(f"✨ {font}")

# --- TƏRCÜMƏ ---
@app.on_message(filters.command("tercume", prefixes=".") & filters.me)
async def tercume(client, message):
    args = message.command
    lang = "az"
    text = ""
    if len(args) > 1:
        lang = args[1].lower()
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif len(args) > 2:
        text = " ".join(args[2:])
    if not text:
        return await message.edit("❌ Mətn yoxdur. Reply edin və ya `.tercume az [mətn]` yazın.")
    try:
        result = GoogleTranslator(source='auto', target=lang).translate(text)
        await message.edit(f"🌐 **Tərcümə ({lang}):**\n{result}")
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")

# --- SƏS ---
@app.on_message(filters.command("ses", prefixes=".") & filters.me)
async def ses(client, message):
    args = message.command
    lang = "tr"
    text = ""
    supported_langs = {"tr": "tr", "az": "az", "en": "en", "fr": "fr", "es": "es", "zh": "zh-CN", "ja": "ja", "ko": "ko"}
    if len(args) > 1 and args[1].lower() in supported_langs:
        lang = supported_langs[args[1].lower()]
        if len(args) > 2:
            text = " ".join(args[2:])
    elif len(args) > 1:
        text = " ".join(args[1:])
    if message.reply_to_message:
        reply_text = message.reply_to_message.text or message.reply_to_message.caption
        if reply_text and not text:
            await message.edit(f"🌐 `{lang}` dilinə tərcümə olunur və səsləndirilir...")
            text = GoogleTranslator(source='auto', target=lang).translate(reply_text)
    if not text:
        return await message.edit("❌ Mətn daxil edin. Nümunə: `.ses en Hello`")
    await message.edit("🎙 **Səs emal olunur...**")
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("voice.mp3")
        await client.send_voice(
            chat_id=message.chat.id,
            voice="voice.mp3",
            caption=f"📝 **Mətn:** {text[:100]}...",
            reply_to_message_id=message.reply_to_message.id if message.reply_to_message else None
        )
        await message.delete()
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")
    finally:
        if os.path.exists("voice.mp3"):
            os.remove("voice.mp3")

# --- AFK ---
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
    if AFK_REJIM:
        await message.reply(f"🤖 AFK-yam: {AFK_SEBEB}")

# --- SAAT ---
@app.on_message(filters.command("saat", prefixes=".") & filters.me)
async def saat(client, message):
    for _ in range(5):
        await message.edit(f"🕒 **Saat:** `{time.strftime('%H:%M:%S')}`")
        await asyncio.sleep(1)

# --- TERS ---
@app.on_message(filters.command("ters", prefixes=".") & filters.me)
async def ters(client, message):
    text = message.reply_to_message.text if message.reply_to_message else (message.text.split(None, 1)[1] if len(message.command) > 1 else None)
    if text:
        await message.edit(text[::-1])

# --- SİL ---
@app.on_message(filters.command("del", prefixes=".") & filters.me)
async def delete_msg(client, message):
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()

# --- BAN / KICK ---
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

# --- FİLTER ---
@app.on_message(filters.command("filter", prefixes=".") & filters.me)
async def filter_add(client, message):
    if not message.reply_to_message:
        return await message.edit("❌ Filter üçün bir mesaja reply at!")
    keyword = message.text.split(None, 1)[1].lower()
    chat_id = message.chat.id
    if chat_id not in FILTERS:
        FILTERS[chat_id] = {}
    FILTERS[chat_id][keyword] = message.reply_to_message.id
    await message.edit(f"✅ `{keyword}` filteri aktiv edildi!")

@app.on_message(filters.command("stopfilter", prefixes=".") & filters.me)
async def filter_stop(client, message):
    if len(message.command) < 2:
        return
    keyword = message.text.split(None, 1)[1].lower()
    if message.chat.id in FILTERS and keyword in FILTERS[message.chat.id]:
        del FILTERS[message.chat.id][keyword]
        await message.edit(f"🗑 `{keyword}` filteri silindi.")
    else:
        await message.edit("❌ Tapılmadı.")

# --- SOSİAL MEDİA YÜKLƏYİCİ ---
@app.on_message(filters.incoming & filters.text & ~filters.me)
async def dl_handler(client, message):
    if any(x in message.text for x in ["instagram.com", "tiktok.com", "youtube.com"]):
        try:
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            path = f"downloads/{message.id}.mp4"
            with yt_dlp.YoutubeDL({'format': 'best', 'outtmpl': path, 'quiet': True}) as ydl:
                ydl.download([message.text])
            await message.reply_video(path, caption=f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ 🗿\n{KANAL_USER}")
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# --- ƏSAS FUNKSIYA ---
async def run():
    try:
        await app.start()
        await bot.start()
        await app.get_me()

        if os.path.exists("update.txt"):
            try:
                with open("update.txt", "r") as f:
                    data = f.readlines()
                if len(data) >= 2:
                    chat_id = int(data[0].strip())
                    msg_id = int(data[1].strip())
                    await app.edit_message_text(chat_id, msg_id, "✅ **Plugin uğurla yükləndi və aktiv edildi!**")
                os.remove("update.txt")
            except:
                pass

        try:
            await load_stored_plugins()
        except Exception:
            pass

        print("✅ HT USERBOT AKTİVDİR")
        await idle()

    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"Kritik xəta: {e}")
    finally:
        try:
            if app.is_connected:
                await app.stop()
            if bot.is_connected:
                await bot.stop()
        except:
            pass

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
