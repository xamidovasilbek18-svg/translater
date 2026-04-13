import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googletrans import Translator

# 1. SOZLAMALAR
TOKEN = "8671591234:AAHjv_nSjBrXRW9oFvnj9ady_6lUdL__Jzo"
ADMIN_ID = 8665041091

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.txt")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: pass

def add_user(user_id):
    try:
        with open(DB_FILE, "r") as f:
            users = [line.strip() for line in f.readlines()]
        if str(user_id) not in users:
            with open(DB_FILE, "a") as f:
                f.write(f"{user_id}\n")
    except Exception as e:
        logging.error(f"DB Error: {e}")

# Tugmalar
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="❓ Yordam")],
        [KeyboardButton(text="📊 Statistika (Admin)")]
    ],
    resize_keyboard=True
)

# Render uchun web server handleri
async def handle(request):
    return web.Response(text="Bot is running smoothly!")

# 2. KOMANDALAR
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n\n"
        "🌐 Men guruhlarda va shaxsiyda matnlarni tarjima qilaman.\n"
        "Menga matn yuboring va tilni tanlang!",
        reply_markup=main_menu
    )

@dp.message(F.text == "❓ Yordam")
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "📖 Qo'llanma:\n\n"
        "1. Matn yuboring.\n"
        "2. Til tugmasini bosing.\n"
        "3. Guruhda ishlatish uchun botni guruhga qo'shing va xabarga 'Reply' qilib tilni tanlang."
    )

@dp.message(F.text == "📊 Statistika (Admin)")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        with open(DB_FILE, "r") as f:
            count = len(f.readlines())
        await message.answer(f"📊 Jami foydalanuvchilar: {count}")

# 3. TARJIMA MANTIQI (Guruh va Shaxsiy uchun)
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: types.Message):
    # Menyudagi tugmalar bo'lsa javob bermaydi
    if message.text in ["⚙️ Sozlamalar", "❓ Yordam", "📊 Statistika (Admin)"]:
        return

    # Tugmalar generatori
    builder = InlineKeyboardBuilder()
    languages = [
        ("🇺🇿 UZ", "uz"), ("🇷🇺 RU", "ru"),
        ("🇺🇸 EN", "en"), ("🇹🇷 TR", "tr"),
        ("🇰🇷 KO", "ko"), ("🇯🇵 JA", "ja")
    ]
    for text, lang in languages:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"tr|{lang}"))
    
    builder.row(InlineKeyboardButton(text="📢 Ulashish", switch_inline_query=f"{message.text[:20]}..."))
    builder.adjust(2)
    
    await message.reply("🌐 Qaysi tilga tarjima qilamiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("tr|"))
async def process_translation(call: types.CallbackQuery):
    _, lang = call.data.split("|")
    
    # Guruhlarda yoki shaxsiyda reply-to xabarni topish
    original_message = call.message.reply_to_message
    
    if not original_message or not original_message.text:
        await call.answer("Asl matn topilmadi ❌", show_alert=True)
        return

    await call.message.edit_text("⏳...")

    try:
        translated = translator.translate(original_message.text, dest=lang)
        flags = {"uz":"🇺🇿", "ru":"🇷🇺", "en":"🇺🇸", "tr":"🇹🇷", "ko":"🇰🇷", "ja":"🇯🇵"}
        flag = flags.get(lang, "📝")
        
        await call.message.edit_text(f"{flag} Tarjima:\n\n{translated.text}")
    except Exception as e:
        logging.error(f"Error: {e}")
        await call.message.edit_text("❌ Xatolik yuz berdi.")
    
    await call.answer()

# 4. ISHGA TUSHIRISH
async def main():
    # Web serverni fonda ishga tushirish (Render uchun)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print("Bot Renderda ishga tushdi...")
    
    # Bot pollingni boshlash
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
