import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googletrans import Translator

# 1. SOZLAMALAR
TOKEN = "8671591234:AAHjv_nSjBrXRW9oFvnj9ady_6lUdL__Jzo"
ADMIN_ID = 8665041091
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

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

# Asosiy menyu tugmalari
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="❓ Yordam")],
        [KeyboardButton(text="📊 Statistika (Admin)")]
    ],
    resize_keyboard=True
)

async def handle(request):
    return web.Response(text="Perfect Translator is Live!")

# 2. KOMANDALAR
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n\n"
        "🌐 **Mukammal Tarjimon Botga xush kelibsiz.**\n"
        "Menga matn yuboring yoki menyudan foydalaning!",
        reply_markup=main_menu,
        parse_mode="Markdown"
    )

@dp.message(F.text == "❓ Yordam")
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = (
        "📖 **Botdan foydalanish bo'yicha qo'llanma:**\n\n"
        "1. Botga istalgan tilda matn yuboring.\n"
        "2. Kelib chiqqan tugmalardan tarjima qilinishi kerak bo'lgan tilni tanlang.\n"
        "3. Bot sizga bir necha soniyada tarjimani yuboradi.\n\n"
        "Muammo yuzaga kelsa: @admin_username ga yozing."
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(F.text == "⚙️ Sozlamalar")
@dp.message(Command("settings"))
async def settings_cmd(message: types.Message):
    await message.answer(
        "⚙️ **Sozlamalar bo'limi:**\n\n"
        "Hozircha bot avtomatik rejimda ishlamoqda.\n"
        "Yaqin orada bu yerga yangi funksiyalar qo'shiladi!",
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Statistika (Admin)")
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        with open(DB_FILE, "r") as f:
            count = len(f.readlines())
        await message.answer(f"📊 **Statistika:**\n\n👤 Foydalanuvchilar: {count} ta")
    else:
        await message.answer(f"❌ Bu bo'lim faqat admin uchun!")

# 3. TARJIMA QISMI
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: types.Message):
    # Agar foydalanuvchi menyu tugmalarini bosmagan bo'lsa tarjima qiladi
    if message.text in ["⚙️ Sozlamalar", "❓ Yordam", "📊 Statistika (Admin)"]:
        return

    add_user(message.from_user.id)
    builder = InlineKeyboardBuilder()
    languages = [
        ("🇺🇿 O'zbek", "uz"), ("🇷🇺 Rus", "ru"),
        ("🇺🇸 Ingliz", "en"), ("🇹🇷 Turk", "tr"),
        ("🇰🇷 Koreys", "ko"), ("🇯🇵 Yapon", "ja"),
        ("🇩🇪 Nemis", "de"), ("🇫🇷 Fransuz", "fr")
    ]
    for text, lang in languages:
        builder.add(InlineKeyboardButton(text=text, callback_data=f"tr|{lang}"))
    builder.adjust(2)
    
    await message.reply("🌐 Qaysi tilga tarjima qilamiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("tr|"))
async def process_translation(call: types.CallbackQuery):
    _, lang = call.data.split("|")
    original_message = call.message.reply_to_message
    
    if not original_message:
        await call.message.edit_text("❌ Asl matn topilmadi.")
        return

    status_msg = await call.message.edit_text("⏳ Tarjima qilinmoqda...")

    try:
        translated = translator.translate(original_message.text, dest=lang)
        flags = {"uz":"🇺🇿", "ru":"🇷🇺", "en":"🇺🇸", "tr":"🇹🇷", "ko":"🇰🇷", "ja":"🇯🇵", "de":"🇩🇪", "fr":"🇫🇷"}
        flag = flags.get(lang, "📝")
        await call.message.edit_text(f"{flag} **Natija:**\n\n`{translated.text}`", parse_mode="Markdown")
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi.")
    await call.answer()

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
