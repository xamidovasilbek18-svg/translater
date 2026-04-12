import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googletrans import Translator

# 1. SOZLAMALAR
TOKEN = "8671591234:AAHjv_nSjBrXRW9oFvnj9ady_6lUdL__Jzo" # <--- YANGI TOKENNI SHU YERGA QO'YING
ADMIN_ID = 8665041091
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

# Fayl yo'lini aniqlash
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.txt")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: pass

def add_user(user_id):
    with open(DB_FILE, "r") as f:
        users = [line.strip() for line in f.readlines()]
    if str(user_id) not in users:
        with open(DB_FILE, "a") as f:
            f.write(f"{user_id}\n")

# Render uchun soxta port
async def handle(request):
    return web.Response(text="Perfect Translator is Live!")

# 2. START VA ADMIN
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n\n"
        "🌐 **Mukammal Tarjimon Botga xush kelibsiz.**\n"
        "Menga istalgan tilda matn yuboring, men uni siz tanlagan tilga tarjima qilaman!",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        with open(DB_FILE, "r") as f:
            count = len(f.readlines())
        await message.answer(f"📊 **Statistika:**\n\n👤 Foydalanuvchilar: {count} ta")
    else:
        await message.answer(f"❌ Admin emassiz! ID: `{message.from_user.id}`")

# 3. TARJIMA QISMI (TUGMALAR BILAN)
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: types.Message):
    add_user(message.from_user.id)
    
    # Tilni tanlash uchun tugmalar
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data=f"tr|uz|{message.message_id}"),
        InlineKeyboardButton(text="🇷🇺 Rus", callback_data=f"tr|ru|{message.message_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🇺🇸 Ingliz", callback_data=f"tr|en|{message.message_id}"),
        InlineKeyboardButton(text="🇹🇷 Turk", callback_data=f"tr|tr|{message.message_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🇰🇷 Koreys", callback_data=f"tr|ko|{message.message_id}"),
        InlineKeyboardButton(text="🇯🇵 Yapon", callback_data=f"tr|ja|{message.message_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🇩🇪 Nemis", callback_data=f"tr|de|{message.message_id}"),
        InlineKeyboardButton(text="🇫🇷 Fransuz", callback_data=f"tr|fr|{message.message_id}")
    )
    
    await message.reply("🌐 Qaysi tilga tarjima qilamiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("tr|"))
async def process_translation(call: types.CallbackQuery):
    _, lang, _ = call.data.split("|")
    original_message = call.message.reply_to_message
    
    if not original_message:
        await call.message.edit_text("❌ Asl matn topilmadi. Iltimos, matnni qayta yuboring.")
        return

    status_msg = await call.message.edit_text("⏳ Tarjima qilinmoqda...")

    try:
        translated = translator.translate(original_message.text, dest=lang)
        
        # Bayroqlarni aniqlash
        flags = {"uz":"🇺🇿", "ru":"🇷🇺", "en":"🇺🇸", "tr":"🇹🇷", "ko":"🇰🇷", "ja":"🇯🇵", "de":"🇩🇪", "fr":"🇫🇷"}
        flag = flags.get(lang, "📝")

        res_text = (
            f"{flag} **Natija ({lang}):**\n\n"
            f"`{translated.text}`"
        )
        await call.message.edit_text(res_text, parse_mode="Markdown")
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik: {str(e)}")
    await call.answer()

# 4. ISHGA TUSHIRISH
async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print("Mukammal Tarjimon ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
