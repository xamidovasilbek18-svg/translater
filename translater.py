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

# Tillarni sozlash
LANGUAGES = {
    "uz": "🇺🇿 O'zbek", "ru": "🇷🇺 Русский", "en": "🇺🇸 English",
    "tr": "🇹🇷 Türkçe", "ko": "🇰🇷 한국어", "ja": "🇯🇵 日本語"
}

TEXTS = {
    "uz": {"welcome": "Salom! Bot tilini tanlang:", "settings": "Sozlamalar: Tilni o'zgartirish", "help": "Yordam", "stat": "Statistika", "select": "Tilni tanlang 👇"},
    "ru": {"welcome": "Привет! Выберите язык бота:", "settings": "Настройки: Изменить язык", "help": "Помощь", "stat": "Статистика", "select": "Выберите язык 👇"},
    "en": {"welcome": "Hello! Choose bot language:", "settings": "Settings: Change language", "help": "Help", "stat": "Stats", "select": "Select language 👇"},
    "tr": {"welcome": "Merhaba! Bot dilini seçin:", "settings": "Ayarlar: Dili değiştir", "help": "Yardım", "stat": "İstatistik", "select": "Dil seçin 👇"},
    "ko": {"welcome": "안녕하세요! 봇 언어를 선택하세요:", "settings": "설정: 언어 변경", "help": "도움말", "stat": "통계", "select": "언어 선택 👇"},
    "ja": {"welcome": "こんにちは！ボットの言語を選択してください:", "settings": "設定：言語変更", "help": "ヘルプ", "stat": "統計", "select": "言語を選択 👇"}
}

# Ma'lumotlar bazasi funksiyalari
def get_user_lang(user_id):
    if not os.path.exists(LANG_FILE): return "uz"
    with open(LANG_FILE, "r") as f:
        for line in f:
            uid, lang = line.strip().split("|")
            if uid == str(user_id): return lang
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
            [KeyboardButton(text="⚙️ " + t["settings"]), KeyboardButton(text="❓ " + t["help"])],
            [KeyboardButton(text="📊 " + t["stat"] + " (Admin)")]
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
    await message.answer("🇺🇿 Bot tilini tanlang / 🇷🇺 Выберите язык бота / 🇺🇸 Choose language:", reply_markup=get_lang_inline())

@dp.callback_query(F.data.startswith("setlang|"))
async def set_lang_callback(call: types.CallbackQuery):
    lang = call.data.split("|")[1]
    set_user_lang(call.from_user.id, lang)
    t = TEXTS[lang]
    await call.message.delete()
    await call.message.answer(f"✅ {LANGUAGES[lang]} tanlandi!", reply_markup=get_main_menu(lang))

@dp.message(F.text.contains("Sozlamalar") | F.text.contains("Settings") | F.text.contains("Настройки") | F.text.contains("Ayarlar") | F.text.contains("설정") | F.text.contains("設定"))
async def settings_cmd(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["select"], reply_markup=get_lang_inline())

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_translation(message: types.Message):
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
        return await call.answer("Xato: Matn topilmadi")
    
    await call.message.edit_text("⏳...")
    tr = translator.translate(original.text, dest=lang)
    await call.message.edit_text(f"✅ ({LANGUAGES[lang]}):\n\n{tr.text}")

# Inline Mode
@dp.inline_query()
async def inline_tr(query: types.InlineQuery):
    text = query.query.strip()
    if not text: return
    results = []
    for code, name in LANGUAGES.items():
        tr = translator.translate(text, dest=code)
        results.append(InlineQueryResultArticle(
            id=hashlib.md5(f"{code}{text}".encode()).hexdigest(),
            title=f"To {name}",
            input_message_content=InputTextMessageContent(message_text=f"🌐 {name}:\n{tr.text}")
        ))
    await query.answer(results, cache_time=5)

# 3. RUNNER
async def handle_web(request): return web.Response(text="Bot Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
