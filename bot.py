import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()  # خواندن متغیرها از فایل .env

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("لطفاً متغیرهای API_ID، API_HASH و BOT_TOKEN را در فایل .env تنظیم کنید.")

BASE_DIR = "downloads"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")  # آدرس عمومی سرور یا localhost

app = Client("my_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

def make_progress_bar(percent: int) -> str:
    filled = int(percent / 10)
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    return f"📥 در حال دریافت فایل:\n[{bar}] {percent}%"

def progress_factory(message):
    last_percent = 0

    async def progress(current, total):
        nonlocal last_percent
        percent = int(current * 100 / total)
        if percent - last_percent >= 5 or percent == 100:
            last_percent = percent
            try:
                await message.edit_text(make_progress_bar(percent))
            except Exception as e:
                print("خطا در به‌روزرسانی پیام پیشرفت:", e)
    return progress

@app.on_message(filters.private)
async def handle_file(client, message: Message):
    try:
        print("📥 پیامی دریافت شد...")

        if message.text and message.text.lower().startswith("/start"):
            first_name = getattr(message.from_user, "first_name", "کاربر")
            await message.reply(f"سلام {first_name}! 👋 فایل مورد نظرت رو بفرست تا لینک بسازم.")
            return

        media = message.document or message.video or message.audio or message.photo or None

        if not media:
            print("❌ فایل شناسایی نشد")
            await message.reply("⛔️ لطفاً فقط فایل، عکس، ویدیو یا صدا بفرست.")
            return

        print("✅ فایل شناسایی شد")

        # نام‌گذاری فایل
        if hasattr(media, "file_name"):
            filename = media.file_name
        elif message.photo:
            filename = f"{message.photo.file_id}.jpg"
        elif message.video:
            filename = f"{message.video.file_id}.mp4"
        elif message.audio:
            filename = f"{message.audio.file_id}.mp3"
        else:
            filename = f"{media.file_id}.bin"

        save_path = os.path.join(BASE_DIR, str(message.from_user.id))
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)

        print(f"⬇️ در حال دانلود فایل در مسیر: {full_path}")

        progress_message = await message.reply(make_progress_bar(0))

        await client.download_media(message, full_path, progress=progress_factory(progress_message))

        print("✅ فایل با موفقیت دانلود شد")
        await progress_message.delete()

        download_link = f"{BASE_URL}/{message.from_user.id}/{filename}"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("باز کردن لینک", url=download_link)]]
        )

        await message.reply_text(
            "برای دانلود فایل روی دکمه زیر کلیک کنید.",
            reply_markup=keyboard
        )

    except Exception as e:
        print("❌ خطای ناشناخته:", e)
        await message.reply("❌ یک خطای ناشناخته رخ داد.")

print("🤖 ربات روشن است...")
app.run()