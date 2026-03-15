import os
import asyncio
import importlib
import importlib.util
import time
import ast
import sys
import random
import wikipedia
import motor.motor_asyncio  # <--- BURA ƏLAVƏ EDİLDİ (MongoDB üçün)
from gtts import gTTS       # <--- BURA ƏLAVƏ EDİLDİ (Səs üçün)
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator

# Heroku Ayarları
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
MONGO_URL = os.environ.get("MONGO_URL") # Bunu Heroku Config Vars-a əlavə etməyi unutma!

# MongoDB Bağlantısını Başlat
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client["xeyal_userbot"]
plugins_db = db["plugins"]

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
            "• `.tercume [az/ru/ing/fr]` - Tərcümə\n"
            "• `.tagall [səbəb]` - Hamını etiketləyir\n"
            "• `.stoptag` - Tagı dayandırır\n"
            "• `.filter [söz]` - Filter əlavə edir\n"
            "• `.stopfilter [söz]` - Filteri silir\n"
            "• `.ping` - Botun sürəti\n"
            "• `.id` - İstifadəçi məlumatı\n"
            "• `.etiraf` - Təsadüfi etiraf\n"
            "• `.hava [şəhər]` - Hava məlumatı\n"
            "• `.wiki [mövzu]` - Vikipediyadan məlumat\n"
            "• `.shans` - Şansını yoxla\n"
            "• `.bom` - Partlayış effekti\n"
            "• `.dice` - Təsadüfi emoji\n"
            "• `.yazi [mətn]` - Qəribə şrift\n"
        )
        await event.edit(menyu_metni)

# --- FİLTER SİSTEMİ (YENİ) ---
@client.on(events.NewMessage(pattern=r'\.filter (.*)'))
async def filter_add(event):
    if not event.out: return
    if not event.is_reply:
        await event.edit("❌ Filter üçün bir mesaja (mətn, stiker, şəkil) reply at gaga!")
        return
    
    keyword = event.pattern_match.group(1).lower()
    reply_msg = await event.get_reply_message()
    chat_id = event.chat_id
    
    if chat_id not in FILTERS:
        FILTERS[chat_id] = {}
        
    FILTERS[chat_id][keyword] = reply_msg
    await event.edit(f"✅ `{keyword}` sözü üçün filter aktiv edildi!")

@client.on(events.NewMessage(pattern=r'\.stopfilter (.*)'))
async def filter_stop(event):
    if not event.out: return
    keyword = event.pattern_match.group(1).lower()
    chat_id = event.chat_id
    
    if chat_id in FILTERS and keyword in FILTERS[chat_id]:
        del FILTERS[chat_id][keyword]
        await event.edit(f"🗑 `{keyword}` filteri silindi.")
    else:
        await event.edit("❌ Belə bir filter tapılmadı.")

@client.on(events.NewMessage(incoming=True))
async def filter_handler(event):
    chat_id = event.chat_id
    if chat_id in FILTERS:
        msg_text = event.text.lower()
        if msg_text in FILTERS[chat_id]:
            await event.reply(FILTERS[chat_id][msg_text])

# --- VİZYONLU YENİ PLUGİNLƏR ---
@client.on(events.NewMessage(pattern=r'\.ping'))
async def ping_test(event):
    if event.out:
        start = time.time()
        await event.edit("🚀...")
        end = time.time()
        ms = round((end - start) * 1000)
        await event.edit(f"⚡ **Pong!**\nSürət: `{ms}ms`")

@client.on(events.NewMessage(pattern=r'\.id'))
async def get_user_id(event):
    if event.out:
        if event.is_reply:
            reply = await event.get_reply_message()
            user = await client.get_entity(reply.sender_id)
            await event.edit(f"🆔 **ID:** `{user.id}`\n👤 **Ad:** {user.first_name}\n🔗 **Link:** [Keçid](tg://user?id={user.id})")
        else:
            await event.edit(f"🆔 **Sənin ID-in:** `{event.sender_id}`")

@client.on(events.NewMessage(pattern=r'\.etiraf'))
async def etiraf_et(event):
    if event.out:
        etiraflar = [
            "Dünən gecə gizlicə soyuducunu boşaltmışam... 🤫",
            "Mən əslində bir bot deyiləm, kosmosdan gəlmişəm. 🛸",
            "Heç kim görməyəndə öz-özümə rəqs edirəm. 💃",
            "Bir dəfə qonşunun wi-fi kodunu sındırmışdım... 📶"
        ]
        await event.edit(f"💭 **Etirafım:** {random.choice(etiraflar)}")

# --- TAG SİSTEMİ ---
@client.on(events.NewMessage(pattern=r'\.tagall ?(.*)'))
async def tag_all(event):
    global TAG_REJIM
    if not event.out: return
    if not event.is_group:
        await event.edit("❌ Bu komanda yalnız qruplarda işləyir!")
        return
    sebeb = event.pattern_match.group(1)
    TAG_REJIM = True
    await event.delete()
    async for user in client.iter_participants(event.chat_id):
        if not TAG_REJIM:
            await client.send_message(event.chat_id, "🛑 **Tag dayandırıldı!**")
            break
        if not user.bot:
            msg = f"[{user.first_name}](tg://user?id={user.id})"
            if sebeb: msg += f" {sebeb}"
            await client.send_message(event.chat_id, msg)
            await asyncio.sleep(1.5)

@client.on(events.NewMessage(pattern=r'\.stoptag'))
async def stop_tag(event):
    global TAG_REJIM
    if event.out:
        TAG_REJIM = False
        await event.edit("✅ Tag dayandırılır...")

# --- DİGƏR KOMANDALAR (TOXUNULMADI) ---
@client.on(events.NewMessage(pattern=r'\.hava (.*)'))
async def hava_durumu(event):
    if not event.out: return
    seher = event.pattern_match.group(1)
    await event.edit(f"☁️ **{seher}** üçün hava məlumatı axtarılır...")
    await asyncio.sleep(1)
    await event.edit(f"🌡 **Şəhər:** `{seher}`\n🌍 **Vəziyyət:** `Məlumat alınır...` (API tələb olunur)")

@client.on(events.NewMessage(pattern=r'\.wiki (.*)'))
async def wikipedia_search(event):
    if not event.out: return
    query = event.pattern_match.group(1)
    await event.edit(f"🔍 **{query}** haqqında məlumat axtarılır...")
    try:
        wikipedia.set_lang("az")
        summary = wikipedia.summary(query, sentences=3)
        await event.edit(f"📚 **Mövzu:** `{query}`\n\n📝 **Məlumat:** {summary}")
    except:
        await event.edit(f"❌ `{query}` haqqında məlumat tapılmadı.")

@client.on(events.NewMessage(pattern=r'\.shans'))
async def shans_yoxla(event):
    if event.out:
        faiz = random.randint(0, 100)
        await event.edit(f"🎲 Sənin bu günkü şansın: **%{faiz}**")

@client.on(events.NewMessage(pattern=r'\.bom'))
async def bom_effect(event):
    if event.out:
        await event.edit("💣"); await asyncio.sleep(0.8); await event.edit("💥 PARTLADI!")

@client.on(events.NewMessage(pattern=r'\.dice'))
async def dice_roll(event):
    if event.out:
        emojis = ["🎲", "🎯", "🏀", "⚽", "🎳", "🎰"]
        await event.edit(random.choice(emojis))

@client.on(events.NewMessage(pattern=r'\.yazi (.*)'))
async def custom_font(event):
    if event.out:
        metn = event.pattern_match.group(1)
        font_metn = metn.replace('a', 'α').replace('e', 'є').replace('i', 'ι').replace('s', 'ѕ')
        await event.edit(f"✨ {font_metn}")

@client.on(events.NewMessage(pattern=r'\.google (.*)'))
async def google_search(event):
    if not event.out: return
    query = event.pattern_match.group(1)
    link = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    await event.edit(f"🔍 **Google:** `{query}`\n🔗 [Bax]({link})")

@client.on(events.NewMessage(pattern=r'\.reaksion'))
async def reaction_test(event):
    if not event.out: return
    emojiler = ["🔥", "⚡", "❤️", "💎", "🌟"]
    for emoji in emojiler:
        await event.edit(f"**Reaksion:** {emoji}"); await asyncio.sleep(0.4)

# --- TƏRCÜMƏ ---
@client.on(events.NewMessage(pattern=r'\.tercume (az|ru|ing|fr)'))
async def tercume_et(event):
    if not event.out or not event.is_reply: return
    dil_kodlari = {"az": "az", "ru": "ru", "ing": "en", "fr": "fr"}
    secilen_dil = event.pattern_match.group(1)
    hedef_dil = dil_kodlari.get(secilen_dil)
    reply_msg = await event.get_reply_message()
    await event.edit("🔄 Tərcümə edilir...")
    try:
        tercume = GoogleTranslator(source='auto', target=hedef_dil).translate(reply_msg.text)
        await event.edit(f"🌐 **{secilen_dil.upper()}**:\n{tercume}")
    except: await event.edit("❌ Xəta!")

# --- MƏTNİ SƏSƏ ÇEVİRMƏ (TTS + REPLY DƏSTƏYİ) ---
@client.on(events.NewMessage(pattern=r'\.ses(?: |$)(.*)'))
async def text_to_speech(event):
    if not event.out: return
    
    args = event.pattern_match.group(1).strip()
    text = ""

    # Əgər bir mesaja reply atılıbsa
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.text:
            text = reply_msg.text
    
    # Əgər komandanın yanında mətn yazılıbsa (bu reply-dan daha öncəliklidir)
    if args:
        text = args

    if not text:
        await event.edit("❌ Səsə çevirmək üçün ya mətn yazın, ya da bir yazıya reply atın!")
        return

    await event.edit("🎙 **Mətn səsə çevrilir...**")
    
    try:
        # Azərbaycan dilində (az) səs hazırlayır
        tts = gTTS(text, lang='az') 
        tts.save("voice.mp3")
        
        # Səsli mesaj (voice note) kimi göndərir
        await client.send_file(
            event.chat_id, 
            "voice.mp3", 
            voice_note=True, 
            reply_to=event.reply_to_msg_id # Reply atılan mesajı hədəf alır
        )
        await event.delete() # ".ses" komandasını silir
    except Exception as e:
        await event.edit(f"❌ Xəta baş verdi: `{str(e)}`")
    finally:
        if os.path.exists("voice.mp3"):
            os.remove("voice.mp3")
            

# --- ƏSAS KOMANDALAR (SƏNİN ORİJİNAL KODUN) ---
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

@client.on(events.NewMessage(pattern=r'\.del'))
async def mesaj_sil(event):
    if event.out and event.is_reply:
        reply = await event.get_reply_message()
        await reply.delete(); await event.delete()

@client.on(events.NewMessage(pattern=r'\.info'))
async def user_info(event):
    if event.out and event.is_reply:
        reply = await event.get_reply_message()
        u_id = reply.from_id.user_id if hasattr(reply.from_id, 'user_id') else "Tapılmadı"
        await event.edit(f"👤 **ID:** `{u_id}`")

@client.on(events.NewMessage(pattern=r'\.saat'))
async def canli_saat(event):
    if event.out:
        for _ in range(10):
            await event.edit(f"🕒 **Saat:** `{time.strftime('%H:%M:%S')}`")
            await asyncio.sleep(1)

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

# --- YENİ FUNKSİYA: AVTO-DOWNLOAD + COOKIE (SƏS SİSTEMİ SİLİNDİ) ---
import requests
import yt_dlp
import os

# Heroku üçün ayarlar
COOKIES_RAW = os.environ.get("COOKIES_DATA", None)
COOKIE_PATH = "cookies.txt"

def prepare_cookies():
    if COOKIES_RAW:
        try:
            with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                f.write(COOKIES_RAW)
            print("✅ Cookielər Config-dən yazıldı.")
        except Exception as e:
            print(f"❌ Cookie xətası: {e}")

# Cookieləri bəri başdan hazırlayırıq
prepare_cookies()

# Avtomatik Video Yükləyici (XeyalUserbot 🗿)
@client.on(events.NewMessage(incoming=True))
async def auto_downloader(event):
    text = event.text
    if not text or not any(site in text for site in ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]):
        return
        
    status_msg = await event.reply("📥 Link aşkarlandı, emal olunur...")
    
    if not os.path.exists("downloads"): 
        os.makedirs("downloads")
        
    file_path = f'downloads/{event.id}.mp4'
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'cookiefile': COOKIE_PATH if os.path.exists(COOKIE_PATH) else None,
        'quiet': True, 
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([text])
        
        # Sənin istədiyin imza ilə göndərir
        await event.reply("XeyalUserbot 🗿", file=file_path)
        await status_msg.delete()
        
        if os.path.exists(file_path): 
            os.remove(file_path)
    except Exception as e:
        await status_msg.edit(f"❌ Xəta: `{str(e)}`")
# --- FUNKSİYANIN SONU ---

# --- PLUGİN YÜKLƏMƏ (SƏNİN ORİJİNAL KODUN) ---
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
            await event.edit(f"✅ **Plugin yükləndi!**\n\n🛠 **Komandalar:**\n{chr(10).join(komandalar)}")
        except Exception as e:
            await event.edit(f"❌ Xəta: `{str(e)}`")
    else:
        await event.edit("❌ Bu düzgün bir plugin deyil!")

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
