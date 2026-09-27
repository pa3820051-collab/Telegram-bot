import os
import re
import random
import string
import asyncio
import requests
import qrcode
from PIL import Image
from bs4 import BeautifulSoup
from flask import Flask, render_template_string
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import yt_dlp
from gtts import gTTS

BOT_TOKEN = "BOT_TOKEN_HEAR"

user_modes = {}
user_temp_mails = {}
user_temp_phones = {}
user_states = {}
anon_bins = {}

# Flask Web Server for Secret Vault
app_flask = Flask(__name__)

@app_flask.route('/note/<token>')
def view_note(token):
    if token in anon_bins:
        secret_data = anon_bins.pop(token)
        html_content = f"""
        <!DOCTYPE html>
        <html lang="hi">
        <head>
            <meta charset="UTF-8">
            <title>Parvez Hacker - Secure Vault</title>
            <style>
                body {{ background-color: #0f172a; color: #38bdf8; font-family: monospace; text-align: center; padding-top: 50px; }}
                h1 {{ color: #ef4444; font-size: 3rem; text-shadow: 0 0 10px #ef4444; }}
                .box {{ background: #1e293b; border: 2px solid #38bdf8; display: inline-block; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px #38bdf8; }}
                .secret {{ font-size: 2.5rem; color: #22c55e; margin: 20px 0; word-break: break-all; }}
                button {{ background: #22c55e; color: #000; border: none; padding: 15px 30px; font-size: 1.2rem; font-weight: bold; cursor: pointer; border-radius: 5px; }}
                button:hover {{ background: #16a34a; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>☠️ PARVEZ HACKER VAULT ☠️</h1>
                <p>Aapka secure confidential data:</p>
                <div class="secret" id="myText">{secret_data}</div>
                <button onclick="copyText()">📋 COPY DATA</button>
            </div>
            <script>
                function copyText() {{
                    const text = document.getElementById("myText").innerText;
                    navigator.clipboard.writeText(text);
                    alert("Data copied successfully!");
                }}
            </script>
        </body>
        </html>
        """
        return render_template_string(html_content)
    else:
        expired_html = """
        <!DOCTYPE html>
        <html lang="hi">
        <head>
            <meta charset="UTF-8">
            <title>Expired Link - Parvez Hacker</title>
            <style>
                body {{ background-color: #000; color: #ef4444; font-family: monospace; text-align: center; padding-top: 100px; }}
                h1 {{ font-size: 4rem; text-shadow: 0 0 20px #ef4444; }}
                p {{ font-size: 1.5rem; color: #fff; }}
            </style>
        </head>
        <body>
            <h1>EXPIRED LINK</h1>
            <p>⚠️ Yeh link pehle hi read kiya ja chuka hai, isiliye ab yeh hamesha ke liye expire ho chuka hai!</p>
        </body>
        </html>
        """
        return render_template_string(expired_html)

def run_flask():
    app_flask.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def create_female_voice_guide(text: str, file_path: str):
    try:
        detailed_script = f"A se Z jankari. {text} Isko use karne ke liye sahi input bhejiye."
        tts = gTTS(text=detailed_script, lang='hi', slow=False)
        tts.save(file_path)
    except Exception:
        pass

async def send_female_voice_guide(update: Update, hi_text: str, user_id: int):
    guide_caption = (
        f"📖 <b>A - Z TECHNICAL GUIDE</b>\n\n"
        f"⚙️ <b>Info:</b> {hi_text}\n\n"
        f"🎙️ <i>(Voice guide...)</i>"
    )
    
    target_message = update.message if update.message else update.callback_query.message
    await target_message.reply_text(guide_caption, parse_mode="HTML")

    v_path = f"downloads/female_guide_{user_id}_{random.randint(1000,9999)}.mp3"
    os.makedirs("downloads", exist_ok=True)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, create_female_voice_guide, hi_text, v_path)
    
    try:
        if os.path.exists(v_path):
            with open(v_path, 'rb') as vf:
                await target_message.reply_voice(voice=vf, caption="🎙️ <b>Voice Guide</b>", parse_mode="HTML")
    except Exception:
        pass
            
    if os.path.exists(v_path):
        try: os.remove(v_path)
        except: pass

def extract_url(text: str):
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(0) if match else None

def safe_cleanup(*filepaths):
    for fp in filepaths:
        if fp and os.path.exists(fp):
            try: os.remove(fp)
            except: pass

def sync_ai_chat(prompt):
    try:
        resp = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=15)
        return resp.text if resp.status_code == 200 else "❌ AI Server Down."
    except: return "❌ AI Connection Failed."

def sync_ytdlp_video(url, status_msg):
    fp = f"downloads/vid_{random.randint(10000,99999)}.mp4"
    os.makedirs("downloads", exist_ok=True)
    
    def hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(status_msg.edit_text(f"📥 <b>Downloading Video...</b> <code>{p}</code>", parse_mode="HTML"))
                loop.close()
            except: pass

    opts = {'outtmpl': fp, 'format': 'best', 'quiet': True, 'progress_hooks': [hook]}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
        return fp
    except: return None

def sync_ytdlp_audio(url, status_msg):
    fp = f"downloads/audio_{random.randint(10000,99999)}.mp3"
    os.makedirs("downloads", exist_ok=True)
    
    def hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').strip()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(status_msg.edit_text(f"🎵 <b>Downloading Audio...</b> <code>{p}</code>", parse_mode="HTML"))
                loop.close()
            except: pass

    opts = {'format': 'bestaudio/best', 'outtmpl': fp, 'noplaylist': True, 'quiet': True, 'progress_hooks': [hook]}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'Audio Track')
    except: return None, None

def sync_universal_direct_link(filepath, status_msg):
    try:
        status_msg.edit_text("📤 <b>Generating Direct Download Link...</b>", parse_mode="HTML")
        with open(filepath, 'rb') as f:
            resp = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=30).text.strip()
            return resp if resp.startswith("http") else "❌ Link Generation Failed"
    except: return "❌ API Error"

def generate_qr_code(data_text):
    fp = f"downloads/qr_{random.randint(10000,99999)}.png"
    os.makedirs("downloads", exist_ok=True)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(fp)
    return fp

def sync_social_footprint(query_str):
    platforms = [
        ("Instagram", f"https://www.instagram.com/{query_str}"),
        ("Twitter/X", f"https://twitter.com/{query_str}"),
        ("GitHub", f"https://github.com/{query_str}"),
        ("Pinterest", f"https://www.pinterest.com/{query_str}"),
        ("Reddit", f"https://www.reddit.com/user/{query_str}"),
        ("TikTok", f"https://www.tiktok.com/@{query_str}")
    ]
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for name, url in platforms:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                results.append(f"🟢 <b>{name}:</b> Active / Registered (`{url}`)")
            else:
                results.append(f"🔴 <b>{name}:</b> Not Found / Available")
        except:
            results.append(f"⚪ <b>{name}:</b> Check Error")
    return "\n".join(results)

def sync_ip_geolocation(ip_or_domain):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_or_domain}", timeout=10).json()
        if r.get("status") == "success":
            return (
                f"🌐 <b>IP / LOCATION API REPORT:</b>\n\n"
                f"🎯 <b>Target:</b> <code>{ip_or_domain}</code>\n"
                f"🌍 <b>Country:</b> {r.get('country')} ({r.get('countryCode')})\n"
                f"🏙️ <b>Region / City:</b> {r.get('regionName')}, {r.get('city')}\n"
                f"🏢 <b>ISP / Organization:</b> {r.get('isp')} / {r.get('org')}\n"
                f"📡 <b>AS Hosting:</b> {r.get('as')}\n"
                f"📍 <b>Coordinates:</b> <code>{r.get('lat')}, {r.get('lon')}</code>"
            )
        else:
            return "❌ Invalid IP or Domain lookup failed."
    except:
        return "❌ Network error during API lookup."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_modes[user_id] = None
    user_states[user_id] = None

    keyboard = [
        [KeyboardButton("🌐 Universal Direct Link"), KeyboardButton("📷 Universal QR Scanner / Maker")],
        [KeyboardButton("🕵️‍♂️ Anonymous Secret Bin"), KeyboardButton("👤 Username Footprint Lookup")],
        [KeyboardButton("🌍 Live IP Geolocation Lookup"), KeyboardButton("⚡ Temporary Mail (Real OTP)")],
        [KeyboardButton("🇮🇳 / 🌐 Virtual Phone (+91 & Global OTP)"), KeyboardButton("🎵 YouTube Audio")],
        [KeyboardButton("📱 YouTube Thumbnail"), KeyboardButton("🎬 Insta Reel Downloader")],
        [KeyboardButton("🤖 AI Chat"), KeyboardButton("🎬 Video Downloader")],
        [KeyboardButton("❌ Cancel / Reset")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    dhamaka_banner = (
        "╔════════════════════════════╗\n"
        "   ☠️ <b>VIP PARVEZ HACKER BOT V49.0</b> ☠️\n"
        "╚════════════════════════════╝\n\n"
        f"⚡ <b>MASTER ONLINE:</b> <code>{update.effective_user.first_name}</code>\n"
        "⚡ <b>STATUS:</b> 🟢 <code>ORIGINAL CORE BUTTONS RESTORED</code>"
    )
    
    hacker_photo_url = "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800"
    try:
        await update.message.reply_photo(photo=hacker_photo_url, caption=dhamaka_banner, reply_markup=reply_markup, parse_mode="HTML")
    except:
        await update.message.reply_text(dhamaka_banner, reply_markup=reply_markup, parse_mode="HTML")

    await send_female_voice_guide(update, "Parvez Hacker bot active hai.", user_id)

async def handle_virtual_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = await update.message.reply_text("⚡ <i>Fetching live virtual number...</i>", parse_mode="HTML")

    loop = asyncio.get_running_loop()
    def fetch_live_phone():
        pool = [
            {"country": "🇮🇳 India (+91)", "number": "+917428723247", "id": "917428723247"},
            {"country": "🇺🇸 United States", "number": "+12065313886", "id": "12065313886"},
            {"country": "🇬🇧 United Kingdom", "number": "+447458196523", "id": "447458196523"},
            {"country": "🇨🇦 Canada", "number": "+16474928641", "id": "16474928641"}
        ]
        return random.choice(pool)

    chosen = await loop.run_in_executor(None, fetch_live_phone)
    user_temp_phones[user_id] = chosen
    await status.delete()

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh SMS & Get Real OTP", callback_data="check_real_sms")],
        [InlineKeyboardButton("🔀 Naya Number Lein", callback_data="get_new_number")]
    ])
    reply_msg = (
        f"📱 <b>LIVE VIRTUAL NUMBER READY!</b>\n\n"
        f"🌐 <b>Country:</b> {chosen['country']}\n"
        f"📞 <b>Phone Number:</b> <code>{chosen['number']}</code>\n\n"
        "👉 Is number ko verification ke liye dalein aur niche button dabakar live OTP dekhein!"
    )
    await update.message.reply_text(reply_msg, reply_markup=btn, parse_mode="HTML")
    await send_female_voice_guide(update, "Virtual number taiyar hai.", user_id)

async def handle_sms_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Scanning live SMS inbox...")
    user_id = query.from_user.id
    phone_data = user_temp_phones.get(user_id)
    if not phone_data:
        await query.message.reply_text("⚠️ Pehle virtual phone button daba kar number lein.")
        return

    phone_num = phone_data['number']
    phone_id = phone_data['id']
    loop = asyncio.get_running_loop()

    def scrape_real_sms():
        try:
            url = f"https://receive-smss.com/sms/{phone_id}/"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.find_all('tr')
                for row in rows[1:6]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        return cols[0].text.strip(), cols[1].text.strip()
        except: pass
        return None, None

    sender, msg_text = await loop.run_in_executor(None, scrape_real_sms)
    if msg_text:
        otp_match = re.search(r'\b(\d{4,8})\b', msg_text)
        otp_code = otp_match.group(1) if otp_match else "SMS Body Dekhein"
        res = f"📬 <b>REAL SMS RECEIVED!</b>\n📞 <b>Number:</b> <code>{phone_num}</code>\n🔑 <b>OTP:</b> <code>{otp_code}</code>\n📝 <b>Text:</b> {msg_text}"
        await query.message.reply_text(res, parse_mode="HTML")
    else:
        await query.message.reply_text(f"📭 Inbox abhi khali hai. 10 second baad dubara try karein.", parse_mode="HTML")

async def handle_temp_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = await update.message.reply_text("⚡ <i>Generating fresh live mailbox...</i>", parse_mode="HTML")
    loop = asyncio.get_running_loop()

    def get_fresh_mailbox():
        try:
            session = requests.Session()
            r = session.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", timeout=10).json()
            return r.get('email_addr'), r.get('sid_token')
        except: return None, None

    email, sid_token = await loop.run_in_executor(None, get_fresh_mailbox)
    await status.delete()

    if email:
        user_temp_mails[user_id] = {'email': email, 'sid': sid_token}
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Inbox & Get Real OTP", callback_data="check_otp_live")]])
        reply_msg = f"⚡ <b>TEMPORARY EMAIL READY!</b>\n📧 <code>{email}</code>\n\nIs email ko sign up ke liye use karein aur niche button se real OTP check karein."
        await update.message.reply_text(reply_msg, reply_markup=btn, parse_mode="HTML")
        await send_female_voice_guide(update, "Temporary email generate ho chuka hai.", user_id)
    else:
        await update.message.reply_text("❌ Server busy hai, dubara try karein.")

async def handle_otp_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Checking inbox...")
    user_id = query.from_user.id
    mail_session = user_temp_mails.get(user_id)
    if not mail_session:
        await query.message.reply_text("⚠️ Pehle Temporary Mail button dabayein.")
        return

    sid = mail_session['sid']
    url = f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={sid}"
    try:
        r = requests.get(url, timeout=10).json()
        list_mails = [m for m in r.get('list', []) if "welcome" not in m.get('mail_subject', '').lower()]
        if not list_mails:
            await query.message.reply_text("📭 Inbox abhi khali hai.", parse_mode="HTML")
            return
        latest = list_mails[0]
        fetch_url = f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={latest.get('mail_id')}&sid_token={sid}"
        mail_body_data = requests.get(fetch_url, timeout=10).json()
        clean_text = re.sub('<[^<]+?>', '', mail_body_data.get('mail_body', ''))
        otp_match = re.search(r'\b(\d{4,8})\b', mail_body_data.get('mail_subject', '') + " " + clean_text)
        otp_code = otp_match.group(1) if otp_match else "Neeche message dekhein"
        res = f"📬 <b>REAL OTP FOUND!</b>\n🔑 <b>OTP:</b> <code>{otp_code}</code>\n📝 <b>Message:</b> {clean_text[:200]}"
        await query.message.reply_text(res, parse_mode="HTML")
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")

async def handle_text_and_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw_text = update.message.text.strip()

    if raw_text == "❌ Cancel / Reset":
        user_modes[user_id] = None
        user_states[user_id] = None
        await update.message.reply_text("🔄 Sabhi modes aur states reset ho gaye.", reply_markup=update.effective_message.reply_markup)
        return

    if raw_text == "⚡ Temporary Mail (Real OTP)":
        await handle_temp_mail(update, context)
        return
    elif raw_text == "🇮🇳 / 🌐 Virtual Phone (+91 & Global OTP)":
        await handle_virtual_phone(update, context)
        return
    elif raw_text == "🌐 Universal Direct Link":
        user_states[user_id] = "UNIVERSAL_LINK"
        await update.message.reply_text("🌐 <b>Universal Direct Link mode activated.</b> Send any photo, video or file.", parse_mode="HTML")
        await send_female_voice_guide(update, "Universal direct link mode active hai.", user_id)
        return
    elif raw_text == "📷 Universal QR Scanner / Maker":
        user_states[user_id] = "QR_MAKER"
        await update.message.reply_text("📷 <b>QR Maker activated.</b> Send text, link, code or email to generate Google Lens readable QR.", parse_mode="HTML")
        await send_female_voice_guide(update, "QR Maker mode active hai.", user_id)
        return
    elif raw_text == "🕵️‍♂️ Anonymous Secret Bin":
        user_states[user_id] = "ANON_BIN"
        await update.message.reply_text("🕵️‍♂️ <b>Anonymous Secret Bin activated.</b> Send any secret text or password to create a browser link.", parse_mode="HTML")
        await send_female_voice_guide(update, "Anonymous secret bin active hai.", user_id)
        return
    elif raw_text == "👤 Username Footprint Lookup":
        user_states[user_id] = "USER_FOOTPRINT"
        await update.message.reply_text("👤 <b>Username Footprint Lookup activated.</b> Send any username or handle to scan active social platforms.", parse_mode="HTML")
        await send_female_voice_guide(update, "Username footprint lookup active hai.", user_id)
        return
    elif raw_text == "🌍 Live IP Geolocation Lookup":
        user_states[user_id] = "IP_LOOKUP"
        await update.message.reply_text("🌍 <b>IP Geolocation Lookup activated.</b> Send any IP address or domain link.", parse_mode="HTML")
        await send_female_voice_guide(update, "IP geolocation lookup active hai.", user_id)
        return
    elif raw_text == "🎵 YouTube Audio":
        user_modes[user_id] = "audio"
        await update.message.reply_text("🎵 <b>YouTube Audio mode active.</b> Send YouTube link.", parse_mode="HTML")
        await send_female_voice_guide(update, "YouTube audio mode active hai.", user_id)
        return
    elif raw_text == "📱 YouTube Thumbnail":
        user_modes[user_id] = "thumb"
        await update.message.reply_text("📱 <b>YouTube Thumbnail mode active.</b> Send video link.", parse_mode="HTML")
        await send_female_voice_guide(update, "YouTube thumbnail mode active hai.", user_id)
        return
    elif raw_text == "🎬 Insta Reel Downloader":
        user_modes[user_id] = "insta"
        await update.message.reply_text("🎬 <b>Insta Reel mode active.</b> Send Instagram link.", parse_mode="HTML")
        await send_female_voice_guide(update, "Instagram reel downloader active hai.", user_id)
        return
    elif raw_text == "🤖 AI Chat":
        user_states[user_id] = "AI"
        await update.message.reply_text("🤖 <b>AI Chat active.</b> Send your question.", parse_mode="HTML")
        await send_female_voice_guide(update, "AI chat active hai.", user_id)
        return
    elif raw_text == "🎬 Video Downloader":
        user_states[user_id] = "VID_DL"
        await update.message.reply_text("🎬 <b>Video Downloader active.</b> Send video link.", parse_mode="HTML")
        await send_female_voice_guide(update, "Video downloader active hai.", user_id)
        return

    state = user_states.get(user_id)
    if state:
        msg = await update.message.reply_text("⏳ Processing request...", parse_mode="HTML")
        if state == "AI":
            resp = await asyncio.to_thread(sync_ai_chat, raw_text)
            await msg.edit_text(resp)
            user_states[user_id] = None
        elif state == "QR_MAKER":
            qr_path = await asyncio.to_thread(generate_qr_code, raw_text)
            if os.path.exists(qr_path):
                with open(qr_path, 'rb') as qf:
                    await update.message.reply_photo(photo=qf, caption="✅ <b>Google Lens 100% Readable QR Ready!</b>", parse_mode="HTML")
                safe_cleanup(qr_path)
                await msg.delete()
            else:
                await msg.edit_text("❌ QR Generation Failed.")
            user_states[user_id] = None
        elif state == "ANON_BIN":
            bin_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            anon_bins[bin_id] = raw_text
            browser_link = f"http://127.0.0.1:5000/note/{bin_id}"
            browser_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open Directly in Chrome / Browser", url=browser_link)]])
            await msg.edit_text(
                f"☠️ <b>CHROME BROWSER VAULT LINK READY!</b>\n\n"
                f"🔗 <b>Browser URL:</b> <code>{browser_link}</code>",
                reply_markup=browser_keyboard,
                parse_mode="HTML"
            )
            user_states[user_id] = None
        elif state == "USER_FOOTPRINT":
            await msg.edit_text("👤 <i>Scanning social footprint across platforms...</i>", parse_mode="HTML")
            report = await asyncio.to_thread(sync_social_footprint, raw_text)
            await update.message.reply_text(f"👤 <b>FOOTPRINT REPORT FOR:</b> <code>{raw_text}</code>\n\n{report}", parse_mode="HTML")
            await msg.delete()
            user_states[user_id] = None
        elif state == "IP_LOOKUP":
            await msg.edit_text("🌍 <i>Tracing IP API geolocation...</i>", parse_mode="HTML")
            report = await asyncio.to_thread(sync_ip_geolocation, raw_text)
            await update.message.reply_text(report, parse_mode="HTML")
            await msg.delete()
            user_states[user_id] = None
        elif state == "VID_DL":
            vid = await asyncio.to_thread(sync_ytdlp_video, raw_text, msg)
            if vid:
                await msg.edit_text("📤 <b>Uploading Video...</b>", parse_mode="HTML")
                with open(vid, 'rb') as vf:
                    await update.message.reply_video(video=vf)
                safe_cleanup(vid)
                await msg.delete()
            else: await msg.edit_text("❌ Download Failed.")
            user_states[user_id] = None
        return

    mode = user_modes.get(user_id)
    detected_url = extract_url(raw_text)

    if mode == "thumb":
        await process_yt_thumbnail(update, context, detected_url or raw_text)
    elif mode == "audio":
        await process_youtube_audio(update, context, detected_url or raw_text)
    elif mode == "insta":
        await process_insta_reel(update, context, detected_url or raw_text)
    else:
        if detected_url:
            if "youtube.com" in detected_url or "youtu.be" in detected_url:
                await process_youtube_audio(update, context, detected_url)
            elif "instagram.com" in detected_url:
                await process_insta_reel(update, context, detected_url)
        else:
            await update.message.reply_text("Kripya menu se option select karein.")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    file_obj = update.message.photo[-1] if update.message.photo else update.message.document
    if not file_obj: return
    
    file = await file_obj.get_file()
    temp_path = f"downloads/in_{random.randint(10000,99999)}"
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(temp_path)
    msg = await update.message.reply_text("⏳ Processing file...", parse_mode="HTML")

    try:
        link = await asyncio.to_thread(sync_universal_direct_link, temp_path, msg)
        if link.startswith("http"):
            if state == "QR_MAKER":
                qr_path = await asyncio.to_thread(generate_qr_code, link)
                with open(qr_path, 'rb') as qf:
                    await update.message.reply_photo(photo=qf, caption=f"✅ <b>Google Lens 100% Readable File QR Ready! Link:</b> <code>{link}</code>", parse_mode="HTML")
                safe_cleanup(qr_path)
                await msg.delete()
                user_states[user_id] = None
            else:
                qr_path = await asyncio.to_thread(generate_qr_code, link)
                reply_msg = f"✅ <b>DIRECT DOWNLOAD LINK READY!</b>\n\n🌐 <code>{link}</code>"
                await update.message.reply_text(reply_msg, parse_mode="HTML")
                with open(qr_path, 'rb') as qf:
                    await update.message.reply_photo(photo=qf, caption="📷 <b>Scan QR with Google Lens!</b>", parse_mode="HTML")
                safe_cleanup(qr_path)
                await msg.delete()
        else:
            await msg.edit_text("❌ Link generation failed.")
    finally:
        safe_cleanup(temp_path)

async def process_yt_thumbnail(update, context, url):
    vid_id = None
    if "youtu.be/" in url: vid_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "watch?v=" in url: vid_id = url.split("watch?v=")[1].split("&")[0]
    else:
        m = re.search(r'([0-9A-Za-z_-]{11})', url)
        if m: vid_id = m.group(1)
    if vid_id:
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
        await update.message.reply_photo(photo=thumb_url, caption="📱 <b>HD Thumbnail Ready!</b>", parse_mode="HTML")
    else: await update.message.reply_text("❌ Invalid YouTube link.")

async def process_youtube_audio(update, context, url):
    status = await update.message.reply_text("⏳ Initializing Audio Download...", parse_mode="HTML")
    try:
        loop = asyncio.get_running_loop()
        f_path, title = await loop.run_in_executor(None, sync_ytdlp_audio, url, status)
        if f_path and os.path.exists(f_path):
            await status.edit_text("📤 <b>Uploading Audio...</b>", parse_mode="HTML")
            with open(f_path, 'rb') as af:
                await update.message.reply_audio(audio=af, title=title)
            safe_cleanup(f_path)
            await status.delete()
        else:
            await status.edit_text("❌ Audio download failed.")
    except Exception as e: await status.edit_text(f"❌ Error: {e}")

async def process_insta_reel(update, context, url):
    chat_id = update.effective_chat.id
    status = await update.message.reply_text("⏳ Initializing Reel Download...", parse_mode="HTML")
    out_file = f"downloads/insta_{chat_id}.mp4"
    try:
        loop = asyncio.get_running_loop()
        def dl():
            def hook(d):
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').strip()
                    try:
                        l = asyncio.new_event_loop()
                        asyncio.set_event_loop(l)
                        l.run_until_complete(status.edit_text(f"📥 <b>Downloading Reel...</b> <code>{p}</code>", parse_mode="HTML"))
                        l.close()
                    except: pass
            with yt_dlp.YoutubeDL({'outtmpl': out_file, 'quiet': True, 'progress_hooks': [hook]}) as ydl: ydl.download([url])
        await loop.run_in_executor(None, dl)
        if os.path.exists(out_file):
            await status.edit_text("📤 <b>Uploading Reel...</b>", parse_mode="HTML")
            with open(out_file, 'rb') as vf:
                await update.message.reply_video(video=vf)
            safe_cleanup(out_file)
            await status.delete()
        else:
            await status.edit_text("❌ Reel download failed.")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")

def main():
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("\n" + "="*60)
    print(" ██████╗  █████╗ ██████╗ ██╗   ██╗███████╗███████╗")
    print(" ██╔══██╗██╔══██╗██╔══██╗██║   ██║██╔════╝╚══███╔╝")
    print(" ██████╔╝███████║██████╔╝██║   ██║█████╗    ███╔╝ ")
    print(" ██╔═══╝ ██╔══██║██╔══██╗╚██╗ ██╔╝██╔══╝   ███╔╝  ")
    print(" ██║     ██║  ██║██║  ██║ ╚████╔╝ ███████╗███████╗")
    print(" ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚══════╝")
    print(" ☠️ PARVEZ HACKER MULTI-TOOL V49.0 ORIGINAL RESTORED ☠️ ")
    print("="*60 + "\n")

    app = ApplicationBuilder().token(BOT_TOKEN).read_timeout(120).write_timeout(120).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_otp_checker, pattern="^check_otp_live$"))
    app.add_handler(CallbackQueryHandler(handle_sms_checker, pattern="^check_real_sms$"))
    app.add_handler(CallbackQueryHandler(handle_virtual_phone, pattern="^get_new_number$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_and_router))

    app.run_polling()

if __name__ == "__main__":
    main()
