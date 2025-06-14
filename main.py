import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- আপনার বটের সেটিংস ---
TOKEN = "7822640248:AAEBnp0nVZYSVeMNMt1-KbM1tR96dmwY9Sc"
ADMIN_ID = 5191483809
AD_URL = "https://www.profitableratecpm.com/v4sjngc9um?key=8c96ee0f99c6bd34c4e97f8f9607c571"
users_file = "users.txt"

# --- ইউজার সেভ ফাংশন ---
def save_user(user_id):
    if not os.path.exists(users_file):
        open(users_file, 'w').close()
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")

# --- /start কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    await update.message.reply_text("👋 হ্যালো! YouTube ভিডিও বা অডিও লিংক পাঠান।")

# --- লিংক হ্যান্ডলার ---
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    keyboard = [
        [InlineKeyboardButton("🎞 ভিডিও ডাউনলোড", callback_data=f"video|{url}")],
        [InlineKeyboardButton("🎧 অডিও ডাউনলোড", callback_data=f"audio|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ফরম্যাট সিলেক্ট করুন:", reply_markup=reply_markup)

# --- বাটন হ্যান্ডলার ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    format_type, url = query.data.split("|")

    ad_button = [[InlineKeyboardButton("📢 Ad দেখুন", url=AD_URL)]]
    await query.message.reply_text("⬇️ নিচের Ad বাটনে ক্লিক করুন এবং 30 সেকেন্ড অপেক্ষা করুন...", reply_markup=InlineKeyboardMarkup(ad_button))

    await asyncio.sleep(30)
    await query.message.reply_text("⏳ ডাউনলোড হচ্ছে...")

    try:
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'bestaudio/best' if format_type == "audio" else 'best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format_type == "audio" else []
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            if format_type == "audio":
                file_name = os.path.splitext(file_name)[0] + ".mp3"

        with open(file_name, 'rb') as f:
            await query.message.reply_document(f)

        os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"❌ ডাউনলোডে সমস্যা হয়েছে: {str(e)}")

# --- ব্রডকাস্ট সিস্টেম ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করতে পারবেন না।")
        return

    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("ব্যবহার করুন:\n`/broadcast আপনার_মেসেজ`", parse_mode='Markdown')
        return

    with open(users_file, "r") as f:
        users = f.read().splitlines()

    success = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            success += 1
            await asyncio.sleep(0.1)
        except:
            continue

    await update.message.reply_text(f"✅ {success} জনকে মেসেজ পাঠানো হয়েছে।")

# --- বট চালানো ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

print("✅ Bot is running...")
app.run_polling()
