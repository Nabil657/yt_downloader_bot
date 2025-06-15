

import telebot
import subprocess
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keep_alive import keep_alive

# Start the web server to keep Replit alive
keep_alive()

BOT_TOKEN = "7822640248:AAEBnp0nVZYSVeMNMt1-KbM1tR96dmwY9Sc"
ADMIN_ID = 5191483809
AD_LINK = "https://www.profitableratecpm.com/v4sjngc9um?key=8c96ee0f99c6bd34c4e97f8f9607c571"

bot = telebot.TeleBot(BOT_TOKEN)
user_wait = {}

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    bot.send_message(user_id, "🎬 ইউটিউব ভিডিও ডাউনলোড করতে লিংক পাঠাও।")

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(msg, "📢 মেসেজ দিন: /broadcast আপনার_মেসেজ")
        return
    with open("users.txt", "r") as f:
        ids = f.read().splitlines()
    for uid in ids:
        try:
            bot.send_message(uid, f"📢 {text}")
        except:
            continue
    bot.reply_to(msg, "✅ ব্রডকাস্ট সম্পন্ন।")

@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    user_id = msg.chat.id
    url = msg.text.strip()

    # Save user if not already
    with open("users.txt", "a+") as f:
        f.seek(0)
        if str(user_id) not in f.read():
            f.write(str(user_id) + "\n")

    if not ("youtube.com" in url or "youtu.be" in url):
        bot.send_message(user_id, "❌ সঠিক ইউটিউব লিংক দিন।")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Ad দেখে ডাউনলোড করুন", url=AD_LINK))
    bot.send_message(user_id, "🕐 আগে এই বিজ্ঞাপনটি দেখে আসুন, ৩০ সেকেন্ড অপেক্ষা করুন তারপর ডাউনলোড শুরু হবে।", reply_markup=markup)
    user_wait[user_id] = url
    time.sleep(30)
    bot.send_message(user_id, "⬇️ ডাউনলোড শুরু হচ্ছে... অডিও বা ভিডিও বেছে নিন:", reply_markup=choose_format())

def choose_format():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎵 অডিও", callback_data="audio"),
        InlineKeyboardButton("🎞️ ভিডিও", callback_data="video")
    )
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    url = user_wait.get(user_id)
    if not url:
        bot.send_message(user_id, "❌ কোনো ভিডিও পাওয়া যায়নি।")
        return

    format = call.data
    output = f"{user_id}.mp4" if format == "video" else f"{user_id}.mp3"
    command = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "-f", "bestaudio" if format == "audio" else "best",
        "-o", output,
        url
    ]

    try:
        subprocess.run(command, check=True)
        with open(output, 'rb') as f:
            if format == "audio":
                bot.send_audio(user_id, f)
            else:
                bot.send_video(user_id, f)
        os.remove(output)
    except Exception as e:
        bot.send_message(user_id, f"❌ ডাউনলোডে সমস্যা হয়েছে: {e}")

bot.infinity_polling()
