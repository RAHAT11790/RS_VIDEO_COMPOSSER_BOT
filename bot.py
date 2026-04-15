import os, asyncio, time, re, subprocess, threading, math
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image

# ========= CONFIG =========
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", 8080))

DIR = "/tmp/"
os.makedirs(DIR, exist_ok=True)

bot = Client("rsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

thumbs = {}
videos = {}

# ========= FLASK FOR RENDER =========
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ RS VIDEO COMPRESSOR BOT IS RUNNING!"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

threading.Thread(target=run_web, daemon=True).start()

# ========= STYLISH BOX DESIGN =========
def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} GB"

def format_time(seconds):
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"

def format_speed(speed_mb):
    if speed_mb > 999:
        return f"{speed_mb/1024:.1f}GB/s"
    return f"{speed_mb:.1f}MB/s"

def get_download_box(percent, current_size, total_size, speed, eta):
    return f"""┏━━━━━━━━◉😇◉━━━━━━━━━┓
┃  😈 𝕽𝕾 𝕻𝕽𝕺𝕮𝕰𝕾𝕾𝕴𝕹𝕲...❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ 📦 𝗦𝗜𝗭𝗘: {format_size(current_size)} | {format_size(total_size)}
┣⪼  𝗗𝗢𝗡𝗘: {percent:.1f}%
┣⪼ 🚀 𝗦𝗣𝗘𝗘𝗗: {format_speed(speed)}/s
┣⪼ ⏰ 𝗘𝗧𝗔: {eta}
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""

def get_compress_box(resolution, percent, current, total, speed_x, eta, current_size, total_size):
    return f"""┏━━━━━━━━◉⚡◉━━━━━━━━━┓
┃  🔥 𝕽𝕾 ℂ𝕆𝕄ℙℝ𝔼𝕊𝕊𝕀ℕ𝔾...❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ 🎬 𝗤𝗨𝗔𝗟𝗜𝗧𝗬: {resolution}p
┣⪼ 📦 𝗦𝗜𝗭𝗘: {format_size(current_size)} | {format_size(total_size)}
┣⪼  𝗗𝗢𝗡𝗘: {percent:.1f}%
┣⪼ 🚀 𝗦𝗣𝗘𝗘𝗗: {speed_x:.1f}x
┣⪼ ⏰ 𝗧𝗜𝗠𝗘: {current}/{total}
┣⪼ ⏳ 𝗘𝗧𝗔: {eta}
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""

def get_upload_box(percent, current_size, total_size, speed, eta):
    return f"""┏━━━━━━━━◉📤◉━━━━━━━━━┓
┃  📤 𝕽𝕾 𝕌ℙ𝕃𝕆𝔸𝔻𝕀ℕ𝔾...❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ 📦 𝗦𝗜𝗭𝗘: {format_size(current_size)} | {format_size(total_size)}
┣⪼  𝗗𝗢𝗡𝗘: {percent:.1f}%
┣⪼ 🚀 𝗦𝗣𝗘𝗘𝗗: {format_speed(speed)}/s
┣⪼ ⏰ 𝗘𝗧𝗔: {eta}
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""

def get_done_box(process, resolution=None):
    if resolution:
        return f"""┏━━━━━━━━◉✅◉━━━━━━━━━┓
┃  ✅ 𝕽𝕾 {process} 𝔻𝕆ℕ𝔼! ❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ 🎬 {resolution}p Compression Complete!
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""
    else:
        return f"""┏━━━━━━━━◉✅◉━━━━━━━━━┓
┃  ✅ 𝕽𝕾 {process} 𝔻𝕆ℕ𝔼! ❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""

def get_waiting_box(process):
    return f"""┏━━━━━━━━◉⏳◉━━━━━━━━━┓
┃  ⏳ 𝕽𝕾 {process}...❱━➣  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ Waiting...
┗━━━━━━━━◉🔥◉━━━━━━━━━┛"""

async def safe_edit(msg, text):
    try:
        await msg.edit_text(f"`{text}`")
    except Exception as e:
        print(f"Edit error: {e}")

# ========= GET VIDEO INFO =========
def get_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.stdout.strip():
            return float(result.stdout.strip())
        return 1.0
    except:
        return 1.0

def get_file_size(file_path):
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0

def extract_thumbnail(video_path, thumb_path):
    try:
        cmd = ["ffmpeg", "-i", video_path, "-ss", "00:00:01", "-vframes", "1", "-vf", "scale=320:-1", "-y", thumb_path]
        subprocess.run(cmd, capture_output=True, timeout=30)
        return os.path.exists(thumb_path)
    except:
        return False

# ========= DOWNLOAD =========
async def download_video(msg, path, status_msg):
    last = 0
    start = time.time()
    total_size = msg.video.file_size if msg.video else 0
    
    async def prog(cur, tot):
        nonlocal last
        if time.time() - last > 1.0:
            last = time.time()
            pct = (cur / tot) * 100
            elapsed = time.time() - start
            speed = cur / (1024*1024) / elapsed if elapsed > 0 else 0
            eta = (tot - cur) / (cur / elapsed) if cur > 0 else 0
            
            box = get_download_box(pct, cur, tot, speed, format_time(eta))
            await safe_edit(status_msg, box)
    
    return await msg.download(file_name=path, progress=prog)

# ========= SUPER FAST COMPRESS =========
async def compress_video(input_path, output_path, resolution, status_msg):
    duration = get_duration(input_path)
    input_size = get_file_size(input_path)
    
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-2:{resolution},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "96k",
        "-ar", "44100",
        "-ac", "2",
        "-threads", "2",
        "-progress", "pipe:1",
        "-y", output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    start_time = time.time()
    last_update = 0
    current_time = 0
    
    await safe_edit(status_msg, get_compress_box(resolution, 0, "00:00", format_time(duration), 0, format_time(0), 0, input_size))
    
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        line_text = line.decode('utf-8', errors='ignore').strip()
        
        if line_text.startswith("out_time_ms="):
            try:
                time_ms = int(line_text.split("=")[1])
                current_time = time_ms / 1000000.0
                
                if time.time() - last_update > 0.8 and current_time > 0:
                    last_update = time.time()
                    
                    pct = min((current_time / duration) * 100, 99)
                    elapsed = time.time() - start_time
                    speed = current_time / elapsed if elapsed > 0 else 0
                    eta = (duration - current_time) / speed if speed > 0 else 0
                    
                    output_size = int(input_size * (1 - pct/100 * 0.7)) if pct > 0 else input_size
                    
                    box = get_compress_box(
                        resolution, pct,
                        format_time(current_time), format_time(duration),
                        speed, format_time(eta),
                        output_size, input_size
                    )
                    await safe_edit(status_msg, box)
                    
            except Exception as e:
                print(f"Parse error: {e}")
        
        elif line_text == "progress=end":
            break
    
    await process.wait()
    await safe_edit(status_msg, get_done_box("COMPRESS", resolution))
    await asyncio.sleep(1)

# ========= UPLOAD =========
async def upload_video(client, chat_id, path, status_msg, thumb_path, resolution):
    total_size = get_file_size(path)
    last = 0
    start = time.time()
    
    async def prog(cur, tot):
        nonlocal last
        if time.time() - last > 1.0:
            last = time.time()
            pct = (cur / tot) * 100
            elapsed = time.time() - start
            speed = cur / (1024*1024) / elapsed if elapsed > 0 else 0
            eta = (tot - cur) / (cur / elapsed) if cur > 0 else 0
            
            box = get_upload_box(pct, cur, tot, speed, format_time(eta))
            await safe_edit(status_msg, box)
    
    return await client.send_video(
        chat_id, path,
        caption=f"✅ **𝕽𝕾 ℂ𝕠𝕞𝕡𝕣𝕖𝕤𝕤𝕖𝕕**\n▸ Quality: {resolution}p\n▸ Ready for Telegram! 🚀",
        thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
        duration=int(get_duration(path)),
        supports_streaming=True,
        progress=prog
    )

# ========= START COMMAND =========
@bot.on_message(filters.command("start"))
async def start_cmd(_, msg):
    start_text = """
┏━━━━━━━━◉🎬◉━━━━━━━━━┓
┃  🎬 𝕽𝕾 𝕍𝕀𝔻𝔼𝕆 ℂ𝕆𝕄ℙℝ𝔼𝕊𝕊𝕆ℝ  
┗━━━━━━━━◉🖥️◉━━━━━━━━━┛
┣⪼ ⚡ 10x-20x Super Fast!
┣⪼ ✅ 100% Telegram Ready
┣⪼ 🎬 No Black Screen
┣⪼ 🔊 Audio + Video Perfect
┣━━━━━━━━◉📌◉━━━━━━━━━┛
┣⪼ 1️⃣ Send Thumbnail (opt)
┣⪼ 2️⃣ Send Your Video
┣⪼ 3️⃣ Select Quality
┣⪼ 4️⃣ Get Compressed!
┗━━━━━━━━◉🔥◉━━━━━━━━━┛

🚀 Send a video now to start!
"""
    await msg.reply_text(f"`{start_text}`")

# ========= THUMBNAIL =========
@bot.on_message(filters.photo)
async def save_thumb(_, msg):
    uid = msg.from_user.id
    path = f"{DIR}thumb_{uid}.jpg"
    await msg.download(file_name=path)
    try:
        img = Image.open(path)
        img.thumbnail((320, 320))
        img.save(path, "JPEG")
        thumbs[uid] = path
        await msg.reply_text("✅ **Thumbnail saved!**\nNow send your video.")
    except Exception as e:
        await msg.reply_text(f"❌ Error: {e}")

# ========= VIDEO HANDLER =========
@bot.on_message(filters.video)
async def video_handler(_, msg):
    videos[msg.id] = msg
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"240_{msg.id}"),
         InlineKeyboardButton("🎬 360p", callback_data=f"360_{msg.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"480_{msg.id}"),
         InlineKeyboardButton("⭐ 720p", callback_data=f"720_{msg.id}")],
        [InlineKeyboardButton("🔥 1080p", callback_data=f"1080_{msg.id}")]
    ])
    await msg.reply_text("🎯 **Select Quality**\n\n🚀 Super Fast Compression (10x-20x speed)!", reply_markup=kb)

# ========= CALLBACK HANDLER =========
@bot.on_callback_query()
async def callback_handler(client, cb: CallbackQuery):
    try:
        res, mid = cb.data.split("_")
        mid = int(mid)
        orig = videos.get(mid)
        
        if not orig:
            await cb.answer("❌ Video not found!", show_alert=True)
            return
        
        await cb.answer(f"🚀 Starting {res}p super fast compression...")
        
        status_msg = await cb.message.reply_text("`" + get_waiting_box("STARTING") + "`")
        await cb.message.delete()
        
        inp = f"{DIR}in_{mid}.mp4"
        out = f"{DIR}out_{mid}.mp4"
        
        await download_video(orig, inp, status_msg)
        await safe_edit(status_msg, get_done_box("DOWNLOAD"))
        await asyncio.sleep(0.5)
        
        await compress_video(inp, out, res, status_msg)
        
        thumb = thumbs.get(cb.from_user.id)
        if not thumb or not os.path.exists(thumb):
            thumb = f"{DIR}thumb_ext_{mid}.jpg"
            extract_thumbnail(out, thumb)
        
        await upload_video(client, cb.message.chat.id, out, status_msg, thumb, res)
        
        await status_msg.delete()
        
        for f in [inp, out]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
                
    except Exception as e:
        print(f"ERROR: {e}")
        await status_msg.edit_text(f"❌ **Error!**\n\n`{str(e)[:200]}`")

# ========= RUN =========
if __name__ == "__main__":
    print("🚀 RS VIDEO COMPRESSOR - DEPLOYED ON RENDER")
    print(f"✅ Web server running on port {PORT}")
    print("✅ Bot is alive and waiting for messages")
    bot.run()
