import os
import asyncio
import logging
import hashlib
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineQueryResultArticle, InputTextMessageContent
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
LANG_FILE = os.path.join(BASE_DIR, "users_lang.txt")

LANGUAGES = {
    "uz": "🇺🇿 O'zbek", "ru": "🇷🇺 Русский", "en": "🇺🇸 English",
    "tr": "🇹🇷 Türkçe", "ko": "🇰🇷 한국어", "ja": "🇯🇵 日本語"
}

TEXTS = {
    "uz": {"settings": "Sozlamalar", "help": "Yordam", "stat": "Statistika", "select": "Tilni tanlang 👇", "help_text": "Matn yuboring va tilni tanlang. Bot avtomatik tarjima qiladi."},
    "ru": {"settings": "Настройки", "help": "Помощь", "stat": "Статистика", "select": "Выберите язык 👇", "help_text": "Отправьте текст и выберите язык. Бот переведет автоматически."},
    "en": {"settings": "Settings", "help": "Help", "stat": "Stats", "select": "Select language 👇", "help_text": "Send text and choose language. The bot will translate automatically."},
    "tr": {"settings": "Ayarlar", "help": "Yardım", "stat": "İstatistik", "select": "Dil seçin 👇", "help_text": "Metni gönderin ve dili seçin. Bot otomatik olarak çevirecektir."},
    "ko": {"settings": "설정", "help": "도움말", "stat": "통계", "select": "언어 선택 👇", "help_text": "텍스트를 보내고 언어를 선택하십시오. 봇이 자동으로 번역합니다."},
    "ja": {"settings": "設定", "help": "ヘルプ", "stat": "統計", "select": "言語を選択 👇", "help_text": "テキストを送信して言語を選択します。ボットは自動的に翻訳します。"}
}

# DB Funksiyalari
def add_user(user_id):
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: pass
    with open(DB_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, "a") as f:
            f.write(f"{user_id}\n")

def get_user_lang(user_id):
    if not os.path.exists(LANG_FILE): return "uz"
    try:
        with open(LANG_FILE, "r") as f:
            for line in f:
                if "|" in line:
                    uid, lang = line.strip().split("|")
                    if uid == str(user_id): return lang
    except: pass
    return "uz"

def set_user_lang(user_id, lang):
    lines = []
    found = False
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{user_id}|"):
                    lines.append(f"{user_id}|{lang}\n")
                    found = True
                else: lines.append(line)
    if not found: lines.append(f"{user_id}|{lang}\n")
    with open(LANG_FILE, "w") as f: f.writelines(lines)

# Menyular
def get_main_menu(lang):
    t = TEXTS.get(lang, TEXTS["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"⚙️ {t['settings']}"), KeyboardButton(text=f"❓ {t['help']}")],
            [KeyboardButton(text=f"📊 {t['stat']} (Admin)")]
        ], resize_keyboard=True
    )

def get_lang_inline():
    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.add(InlineKeyboardButton(text=name, callback_data=f"setlang|{code}"))
    builder.adjust(2)
    return builder.as_markup()

# 2. HANDLERLAR
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer("🌐 Choose Language / Tilni tanlang / Выберите язык:", reply_markup=get_lang_inline())

@dp.callback_query(F.data.startswith("setlang|"))
async def set_lang_callback(call: types.CallbackQuery):
    lang = call.data.split("|")[1]
    set_user_lang(call.from_user.id, lang)
    await call.message.delete()
    await call.message.answer(f"✅ {LANGUAGES[lang]}", reply_markup=get_main_menu(lang))
    await call.answer()

# Admin Handler (Emoji orqali aniqlash)
@dp.message(F.text.contains("📊"))
async def admin_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                count = len(f.read().splitlines())
            await message.answer(f"📊 Jami foydalanuvchilar: {count}")
        else:
            await message.answer("📊 Statistika: 0")
    else:
        await message.answer(f"❌ Faqat admin uchun! (Sizning ID: {message.from_user.id})")

# Yordam Handler
@dp.message(F.text.contains("❓"))
async def help_handler(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["help_text"])

# Sozlamalar Handler
@dp.message(F.text.contains("⚙️"))
async def settings_handler(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["select"], reply_markup=get_lang_inline())

# Tarjima Handler
@dp.message(F.text & ~F.text.startswith("/"))
async def translation_handler(message: types.Message):
    if any(x in message.text for x in ["⚙️", "❓", "📊"]): return
    
    user_lang = get_user_lang(message.from_user.id)
    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.add(InlineKeyboardButton(text=name, callback_data=f"tr|{code}"))
    builder.adjust(2)
    await message.reply(TEXTS[user_lang]["select"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("tr|"))
async def process_tr(call: types.CallbackQuery):
    lang = call.data.split("|")[1]
    original = call.message.reply_to_message
    if not original or not original.text:
        return await call.answer("Xato: Matn topilmadi", show_alert=True)
    
    await call.message.edit_text("⏳...")
    try:
        tr = translator.translate(original.text, dest=lang)
        await call.message.edit_text(f"✅ ({LANGUAGES[lang]}):\n\n{tr.text}")
    except:
        await call.message.edit_text("❌ Xatolik yuz berdi.")
    await call.answer()

# 3. RUNNER (Render uchun)
async def handle_web(request): return web.Response(text="Bot Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
