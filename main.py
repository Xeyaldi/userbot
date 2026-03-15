import os
import asyncio
import time
import random
import wikipedia
import requests
import yt_dlp
import motor.motor_asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)
from pyrogram.errors import FloodWait
from deep_translator import GoogleTranslator
from gtts import gTTS

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URL = os.environ.get("MONGO_URL")

# MongoDB Bağlantısı
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]

# Client-lər
app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Qlobal dəyişənlər
AFK_REJIM = False
AFK_SEBEB = ""
TAG_REJIM = True
FILTERS = {}

# --- KOMANDA İZAHLARI ---
COMMAND_DETAILS = {
    "ping": "🚀 **Ping:** Botun sürətini ölçür.",
    "id": "🆔 **ID:** İstifadəçi ID-sini göstərir.",
    "etiraf": "💭 **Etiraf:** Təsadüfi etiraf mesajı göndərir.",
    "tagall": "📣 **TagAll:** Hamını etiketləyir.",
    "wiki": "📚 **Wiki:** Wikipedia axtarışı.",
    "hava": "🌡 **Hava:** Hava proqnozu.",
    "shans": "🎲 **Şans:** Şans faizi.",
    "bom": "💣 **BOM:** Partlayış effekti.",
    "dice": "🎲 **Dice:** Təsadüfi oyun ikonları.",
    "yazi": "✨ **Yazı:** Şrifti dəyişir.",
    "tercume": "🌐 **Tərcümə:** Mesajı tərcümə edir.",
    "ses": "🎙 **Səs:** Yazını səsə çevirir.",
    "afk": "💤 **AFK:** AFK rejimini açır.",
    "online": "✅ **Online:** AFK-nı söndürür.",
    "saat": "🕒 **Saat:** Canlı saat.",
    "ters": "🔄 **Tərs:** Yazını tərsinə çevirir.",
    "del": "🗑 **Sil:** Mesajı silir.",
    "ban": "🚫 **Ban:** İstifadəçini ban edir.",
    "kick": "👞 **Kick:** İstifadəçini qrupdan atır."
}

# --- YARDIM MENYUSU (.hthelp) ---
@app.on_message(filters.command("hthelp", prefixes=".") & filters.me)
async def help_menu(client, message):
    try:
        results = await client.get_inline_bot_results(bot.me.username, "menu")
        await client.send_inline_bot_result(
            message.chat.id, 
            results.query_id, 
            results.results[0].id,
            hide_via=True
        )
        await message.delete()
    except Exception as e:
        await message.edit(f"❌ Xəta: {e}")

@bot.on_inline_query()
async def inline_handler(client, query):
    if query.query == "menu":
        buttons = [
            [InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")],
            [InlineKeyboardButton("📢 HT Kanal", url="https://t.me/Kullaniciadidi"), InlineKeyboardButton("❌ Bağla", callback_data="close_m")]
        ]
        await query.answer([
            InlineQueryResultArticle(
                title="HT Menu",
                input_message_content=InputTextMessageContent("✨ **HT USERBOT | İdarə Paneli**\n\nSistem aktivdir."),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        ], cache_time=1)

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    if data == "view_cmds":
        cmd_buttons = []
        keys = list(COMMAND_DETAILS.keys())
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(f"🔹 {keys[i]}", callback_data=f"info_{keys[i]}")]
            if i + 1 < len(keys): row.append(InlineKeyboardButton(f"🔹 {keys[i+1]}", callback_data=f"info_{keys[i+1]}"))
            cmd_buttons.append(row)
        cmd_buttons.append([InlineKeyboardButton("⬅️ Geri", callback_data="back")])
        await callback_query.edit_message_text("🛠 **Sistem Komandaları:**", reply_markup=InlineKeyboardMarkup(cmd_buttons))
    elif data.startswith("info_"):
        cmd = data.split("_")[1]
        desc = COMMAND_DETAILS.get(cmd, "Məlumat yoxdur.")
        await callback_query.edit_message_text(f"🔍 **Komanda:** `.{cmd}`\n\n{desc}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data="view_cmds")]]))
    elif data == "back":
        await callback_query.edit_message_text("✨ **HT USERBOT | İdarə Paneli**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠 Komandalar", callback_data="view_cmds")]]))
    elif data == "close_m":
        await callback_query.message.delete()

# --- .htlive ---
@app.on_message(filters.command("htlive", prefixes=".") & filters.me)
async def htlive(client, message):
    res = client.me
    font_text = f"ᎻᎢ ᏌᏚᎬᎡᏴOᎢ [{res.first_name}](tg://user?id={res.id}) ϋçϋи αктινdιя"
    await message.edit(f"🚀 {font_text}")

# --- FİLTER SİSTEMİ ---
@app.on_message(filters.command("filter", prefixes=".") & filters.me)
async def filter_add(client, message):
    if not message.reply_to_message:
        return await message.edit("❌ Filter üçün bir mesaja reply at gaga!")
    keyword = message.text.split(None, 1)[1].lower()
    FILTERS[message.chat.id] = FILTERS.get(message.chat.id, {})
    FILTERS[message.chat.id][keyword] = message.reply_to_message.id
    await message.edit(f"✅ `{keyword}` filteri aktiv edildi!")

@app.on_message(filters.command("stopfilter", prefixes=".") & filters.me)
async def filter_stop(client, message):
    keyword = message.text.split(None, 1)[1].lower()
    if message.chat.id in FILTERS and keyword in FILTERS[message.chat.id]:
        del FILTERS[message.chat.id][keyword]
        await message.edit(f"🗑 `{keyword}` filteri silindi.")
    else: await message.edit("❌ Tapılmadı.")

@app.on_message(filters.incoming & filters.text & ~filters.private)
async def filter_handler(client, message):
    if message.chat.id in FILTERS:
        word = message.text.lower()
        if word in FILTERS[message.chat.id]:
            await message.reply_reply_to_message(FILTERS[message.chat.id][word])

# --- PİNG VƏ ID ---
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
    async for member in client.get_chat_members(message.chat.id):
        if not TAG_REJIM: break
        if not member.user.is_bot:
            await client.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {sebeb}")
            await asyncio.sleep(1.5)

@app.on_message(filters.command("stoptag", prefixes=".") & filters.me)
async def stoptag(client, message):
    global TAG_REJIM
    TAG_REJIM = False
    await message.edit("✅ Tag dayandırıldı.")

# --- HAVA VƏ WİKİ ---
@app.on_message(filters.command("hava", prefixes=".") & filters.me)
async def hava(client, message):
    city = message.text.split(None, 1)[1]
    await message.edit(f"🌡 **Şəhər:** `{city}` üçün hava axtarılır...")

@app.on_message(filters.command("wiki", prefixes=".") & filters.me)
async def wiki(client, message):
    query = message.text.split(None, 1)[1]
    try:
        wikipedia.set_lang("az")
        res = wikipedia.summary(query, sentences=2)
        await message.edit(f"📚 **Wiki:** {res}")
    except: await message.edit("❌ Tapılmadı.")

# --- ŞANS, BOM, DİCE ---
@app.on_message(filters.command("shans", prefixes=".") & filters.me)
async def shans(client, message):
    await message.edit(f"🎲 Sənin şansın: **%{random.randint(0, 100)}**")

@app.on_message(filters.command("bom", prefixes=".") & filters.me)
async def bom(client, message):
    await message.edit("💣"); await asyncio.sleep(0.8); await message.edit("💥 PARTLADI!")

@app.on_message(filters.command("dice", prefixes=".") & filters.me)
async def dice(client, message):
    await message.edit(random.choice(["🎲", "🎯", "🏀", "⚽"]))

# --- YAZI, TƏRCÜMƏ, SƏS ---
@app.on_message(filters.command("yazi", prefixes=".") & filters.me)
async def yazi(client, message):
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
    text = message.reply_to_message.text if message.reply_to_message else message.text.split(None, 1)[1]
    await message.edit("🎙 Hazırlanır...")
    tts = gTTS(text=text, lang="tr")
    tts.save("voice.mp3")
    await client.send_voice(message.chat.id, "voice.mp3")
    await message.delete()

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

@app.on_message(filters.incoming & filters.private)
async def afk_handler(client, message):
    if AFK_REJIM: await message.reply(f"🤖 AFK-yam: {AFK_SEBEB}")

# --- DOWNLOADER ---
@app.on_message(filters.incoming & ~filters.private)
async def dl_handler(client, message):
    if message.text and any(x in message.text for x in ["instagram.com", "tiktok.com", "youtube.com"]):
        status = await message.reply("📥 Yüklenir...")
        path = f"downloads/{message.id}.mp4"
        try:
            with yt_dlp.YoutubeDL({'format': 'best', 'outtmpl': path, 'quiet': True}) as ydl: ydl.download([message.text])
            await message.reply_video(path, caption="ᎻᎢ ᏌᏚᎬᎡᏴOᎢ 🗿")
            await status.delete()
        except: await status.edit("❌ Xəta.")
        if os.path.exists(path): os.remove(path)

# --- ADMIN ---
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
    text = message.reply_to_message.text if message.reply_to_message else message.text.split(None, 1)[1]
    await message.edit(text[::-1])

@app.on_message(filters.command("del", prefixes=".") & filters.me)
async def delete_msg(client, message):
    if message.reply_to_message:
        await message.reply_to_message.delete()
        await message.delete()

# --- MAIN RUN ---
async def run():
    await app.start()
    await bot.start()
    print("✅ HT USERBOT ONLINE!")
    await asyncio.gather(app.run_until_disconnected(), bot.run_until_disconnected())

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
