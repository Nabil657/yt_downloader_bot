import logging
from aiogram import Bot, Dispatcher, executor, types
import yt_dlp
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables (if any)
load_dotenv()

# Constants
API_TOKEN = '7822640248:AAEBnp0nVZYSVeMNMt1-KbM1tR96dmwY9Sc'
ADMIN_ID = 5191483809
AD_LINK = "https://www.profitableratecpm.com/v4sjngc9um?key=8c96ee0f99c6bd34c4e97f8f9607c571"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# In-memory storage for user states
user_states = {}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("🎬 YouTube Downloader Bot\n\n🎥 ভিডিও লিংক দিন এবং আপনি চাইলে ভিডিও বা অডিও আকারে ডাউনলোড করতে পারবেন।")

@dp.message_handler(commands=['broadcast'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.reply("Usage: /broadcast Your Message")
        return
    msg = text[1]
    for user_id in user_states.keys():
        try:
            await bot.send_message(user_id, f"📢 {msg}")
        except:
            continue
    await message.reply("✅ Broadcast completed.")

@dp.message_handler()
async def handle_url(message: types.Message):
    if "youtube.com" not in message.text and "youtu.be" not in message.text:
        await message.reply("❌ দয়া করে একটি বৈধ YouTube লিংক দিন।")
        return

    user_id = message.from_user.id
    user_states[user_id] = {"url": message.text}

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🎬 ভিডিও", callback_data="video"))
    keyboard.add(types.InlineKeyboardButton(text="🎧 অডিও", callback_data="audio"))
    await message.reply("আপনি কীভাবে ডাউনলোড করতে চান?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in ['video', 'audio'])
async def process_download(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_choice = call.data
    if user_id not in user_states:
        await call.answer("Session expired. Please send the link again.")
        return

    url = user_states[user_id]["url"]
    user_states[user_id]["format"] = user_choice

    ad_button = types.InlineKeyboardMarkup()
    ad_button.add(
        types.InlineKeyboardButton(text="📢 এড দেখুন এবং ডাউনলোড করুন", url=AD_LINK)
    )
    await call.message.edit_text("🎯 প্রথমে এড দেখুন। ৩০ সেকেন্ড পর ডাউনলোড শুরু হবে।", reply_markup=ad_button)

    await asyncio.sleep(30)
    await download_and_send(bot, call.message.chat.id, url, user_choice)

async def download_and_send(bot, chat_id, url, format_type):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestaudio/best' if format_type == 'audio' else 'bestvideo+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format_type == 'audio' else [],
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            with open(filename, 'rb') as f:
                if format_type == 'audio':
                    await bot.send_audio(chat_id, f, title=info.get("title", "Audio"))
                else:
                    await bot.send_video(chat_id, f, caption=info.get("title", "Video"))
            os.remove(filename)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ ডাউনলোডে সমস্যা হয়েছে: {str(e)}")

# Dummy HTTP server for Render (prevent timeout)
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_http_server).start()

# Start polling
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)