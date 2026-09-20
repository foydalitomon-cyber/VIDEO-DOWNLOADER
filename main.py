import os
import asyncio
import logging
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from yt_dlp import YoutubeDL
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Xatolik: Muhit o'zgaruvchilari (Environment Variables) topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

URL_CACHE = {}

# --- BARCHA TILLAR (Koreys - KR va Xitoy - CN BILAN) ---
LANG_TEXTS = {
    "uz": {
        "welcome": "👋 Xush kelibsiz! Iltimos, tilni tanlang:",
        "choose_qual": "📺 Video sifatini tanlang:",
        "choose_fmt": "📥 Formatni tanlang:",
        "fetching": "🔍 Havola tahlil qilinmoqda, iltimos kuting...",
        "downloading": "⏳ Media yuklab olinmoqda, iltimos kuting...",
        "uploading": "📤 Telegramga yuborilmoqda...",
        "error": "❌ Xatolik yuz berdi.",
        "success_cap": "🎬 Bot orqali yuklab olindi",
        "lang_set": "✅ Til O'zbek tiliga o'zgartirildi! Endi video havolasini yuboring."
    },
    "ru": {
        "welcome": "👋 Добро пожаловать! Пожалуйста, выберите язык:",
        "choose_qual": "📺 Выберите качество видео:",
        "choose_fmt": "📥 Выберите формат:",
        "fetching": "🔍 Анализируем ссылку, пожалуйста подождите...",
        "downloading": "⏳ Загрузка медиа, пожалуйста подождите...",
        "uploading": "📤 Отправка в Telegram...",
        "error": "❌ Произошла ошибка.",
        "success_cap": "🎬 Загружено через бота",
        "lang_set": "✅ Язык изменен на Русский! Теперь отправьте ссылку на видео."
    },
    "en": {
        "welcome": "👋 Welcome! Please choose your language:",
        "choose_qual": "📺 Select video quality:",
        "choose_fmt": "📥 Select format:",
        "fetching": "🔍 Analyzing link, please wait...",
        "downloading": "⏳ Downloading media, please wait...",
        "uploading": "📤 Uploading to Telegram...",
        "error": "❌ An error occurred.",
        "success_cap": "🎬 Downloaded via Bot",
        "lang_set": "✅ Language set to English! Now send a video link."
    },
    "kaz": {
        "welcome": "👋 Қош келдіңіз! Тілді таңлаңыз:",
        "choose_qual": "📺 Бейне сапасын таңдаңыз:",
        "choose_fmt": "📥 Пішінді таңдаңыз:",
        "fetching": "🔍 Сілтеме тексерілуде, күте тұрыңыз...",
        "downloading": "⏳ Медиа жүктелуде, күте тұрыңыз...",
        "uploading": "📤 Telegram-ға жіберілуде...",
        "error": "❌ Қате орын алды.",
        "success_cap": "🎬 Бот арқылы жүктелді",
        "lang_set": "✅ Тіл Қазақ тіліне өзгертілді! Енді видео сілтемесін жіберіңіз."
    },
    "tj": {
        "welcome": "👋 Хуш омадед! Лутфан забоonро интихоб кунед:",
        "choose_qual": "📺 Сифати видеоро интихоб кунед:",
        "choose_fmt": "📥 Форматро интихоб кунед:",
        "fetching": "🔍 Таҳлили истинод, лутфан интизор шавед...",
        "downloading": "⏳ Боргирии медиа, лутфан интизор шавед...",
        "uploading": "📤 Ирсол ба Telegram...",
        "error": "❌ Хатогӣ ба амал омад.",
        "success_cap": "🎬 Тавассути бот зеркашӣ шуд",
        "lang_set": "✅ Забон ба Тоҷикӣ иваз шуд! Акнун истиноди видеоро фиристед."
    },
    "kg": {
        "welcome": "👋 Кош келиңиз! Сураныч, тилди тандаңыз:",
        "choose_qual": "📺 Видео сапасын тандаңыз:",
        "choose_fmt": "📥 Форматты тандаңыз:",
        "fetching": "🔍 Шилтеме текшерилүүдө, күтө туруңуз...",
        "downloading": "⏳ Медиа жүктөлүүдө, күтө туруңуз...",
        "uploading": "📤 Telegram'га жөнөтүлүүдө...",
        "error": "❌ Ката кетти.",
        "success_cap": "🎬 Бот аркылуу жүктөлдү",
        "lang_set": "✅ Тил Кыргыз тилине өзгөртүлдү! Эми видео шилтемесин жөнөтүңүз."
    },
    "vi": {
        "welcome": "👋 Chào mừng! Vui lòng chọn ngôn ngữ của bạn:",
        "choose_qual": "📺 Chọn chất lượng video:",
        "choose_fmt": "📥 Chọn định dạng:",
        "fetching": "🔍 Đang phân tích liên kết, vui lòng đợi...",
        "downloading": "⏳ Đang tải phương tiện, vui lòng đợi...",
        "uploading": "📤 Đang tải lên Telegram...",
        "error": "❌ Đã xảy ra lỗi.",
        "success_cap": "🎬 Đã tải xuống qua Bot",
        "lang_set": "✅ Đã đặt ngôn ngữ thành Tiếng Việt! Bây giờ hãy gửi liên kết video."
    },
    "id": {
        "welcome": "👋 Selamat datang! Silakan pilih bahasa Anda:",
        "choose_qual": "📺 Pilih kualitas video:",
        "choose_fmt": "📥 Pilih format:",
        "fetching": "🔍 Menganalisis tautan, harap tunggu...",
        "downloading": "⏳ Mengunduh media, harap tunggu...",
        "uploading": "📤 Mengunggah ke Telegram...",
        "error": "❌ Terjadi kesalahan.",
        "success_cap": "🎬 Diunduh melalui Bot",
        "lang_set": "✅ Bahasa diatur ke Indonesia! Sekarang kirim tautan video."
    },
    "my": {
        "welcome": "👋 မင်္ဂလာပါ။ ကျေးဇူးပြု၍ ဘာသာစကားကို ရွေးချယ်ပါ -",
        "choose_qual": "📺 ဗီဒီယို အရည်အသွေးကို ရွေးပါ -",
        "choose_fmt": "📥 ဖော်မတ်ကို ရွေးပါ -",
        "fetching": "🔍 လင့်ခ်ကို စစ်ဆေးနေပါသည်၊ ခဏစောင့်ပါ...",
        "downloading": "⏳ မီဒီယာကို ဒေါင်းလုဒ်လုပ်နေသည်၊ ခဏစောင့်ပါ...",
        "uploading": "📤 Telegram သို့ ပို့ဆောင်နေသည်...",
        "error": "❌ အမှားအယွင်း ဖြစ်ပေါ်သွားပါသည်။",
        "success_cap": "🎬 ဘော့တ်မှတဆင့် ဒေါင်းလုဒ်လုပ်ပြီးပါပြီ",
        "lang_set": "✅ မြန်မာဘာသာသို့ ပြောင်းပြီးပါပြီ။ ယခု ဗီဒီယိုလင့်ခ်ကို ပို့ပါ။"
    },
    "jp": {
        "welcome": "👋 ようこそ！言語を選択してください:",
        "choose_qual": "📺 動画の画質を選択してください:",
        "choose_fmt": "📥 フォーマットを選択してください:",
        "fetching": "🔍 リンクを分析中です。しばらくお待ちください...",
        "downloading": "⏳ メディアをダウンロード中です...",
        "uploading": "📤 Telegramに送信しています...",
        "error": "❌ エラーが発生しました。",
        "success_cap": "🎬 ボット経由でダウンロードされました",
        "lang_set": "✅ 言語が日本語に変更されました！動画のリンクを送信してください。"
    },
    "kr": {
        "welcome": "👋 환영합니다! 언어를 선택해주세요:",
        "choose_qual": "📺 동영상 화질을 선택하세요:",
        "choose_fmt": "📥 형식을 선택하세요:",
        "fetching": "🔍 링크 분석 중입니다. 잠시만 기다려주세요...",
        "downloading": "⏳ 미디어 다운로드 중...",
        "uploading": "📤 Telegram으로 전송 중...",
        "error": "❌ 오류가 발생했습니다.",
        "success_cap": "🎬 봇을 통해 다운로드되었습니다",
        "lang_set": "✅ 한국어로 변경되었습니다! 이제 동영상 링크를 보내주세요."
    },
    "cn": {
        "welcome": "👋 欢迎! 请选择您的语言:",
        "choose_qual": "📺 请选择视频清晰度:",
        "choose_fmt": "📥 请选择格式:",
        "fetching": "🔍 正在分析链接，请稍候...",
        "downloading": "⏳ 正在下载媒体，请稍候...",
        "uploading": "📤 正在发送至 Telegram...",
        "error": "❌ 发生错误。",
        "success_cap": "🎬 已通过机器人下载",
        "lang_set": "✅ 语言已更改为中文！现在请发送视频链接。"
    }
}

# --- TIL TANLASH KEYBOARDLARI (Barcha yangi tillar bilan) ---
def build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang|uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang|ru")
        ],
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang|en"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang|kaz")
        ],
        [
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang|tj"),
            InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang|kg")
        ],
        [
            InlineKeyboardButton(text="🇻🇳 Tiếng Việt", callback_data="lang|vi"),
            InlineKeyboardButton(text="🇮🇩 Indonesia", callback_data="lang|id")
        ],
        [
            InlineKeyboardButton(text="🇲🇲 မြန်မာစာ", callback_data="lang|my"),
            InlineKeyboardButton(text="🇯🇵 日本語", callback_data="lang|jp")
        ],
        [
            InlineKeyboardButton(text="🇰🇷 한국어", callback_data="lang|kr"),
            InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang|cn")
        ]
    ])

# --- DATABASE FUNKSIYALARI ---
def get_user_lang(user_id: int) -> str:
    try:
        res = supabase.table("users").select("language").eq("user_id", user_id).execute()
        if res.data and res.data[0].get("language"):
            return res.data[0]["language"]
    except:
        pass
    return "uz"

def save_user_to_db(user_id: int, username: str, first_name: str):
    try:
        existing = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
        if not existing.data:
            supabase.table("users").insert({
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "is_active": True,
                "language": "uz"
            }).execute()
    except Exception as e:
        logging.error(f"DB Error: {e}")

def update_user_lang(user_id: int, lang: str):
    try:
        supabase.table("users").update({"language": lang}).eq("user_id", user_id).execute()
    except Exception as e:
        logging.error(f"Lang Update Error: {e}")

def log_download_to_db(user_id: int, platform: str, format_type: str):
    try:
        supabase.table("downloads").insert({
            "user_id": user_id,
            "platform": platform,
            "format_type": format_type
        }).execute()
    except Exception as e:
        logging.error(f"Download DB Error: {e}")

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    save_user_to_db(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "👋 **Welcome! Please choose your language / Tilni tanlang / 🌐 Language:**",
        reply_markup=build_language_keyboard()
    )

@dp.callback_query(F.data.startswith("lang|"))
async def set_language_callback(callback: types.CallbackQuery):
    _, lang = callback.data.split("|")
    update_user_lang(callback.from_user.id, lang)
    
    texts = LANG_TEXTS.get(lang, LANG_TEXTS["uz"])
    await callback.answer()
    await callback.message.edit_text(texts["lang_set"])

@dp.message(Command("stat"))
async def stat_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        users_res = supabase.table("users").select("user_id", count="exact").execute()
        downloads_res = supabase.table("downloads").select("id", count="exact").execute()
        
        total_users = users_res.count if hasattr(users_res, 'count') else len(users_res.data)
        total_downloads = downloads_res.count if hasattr(downloads_res, 'count') else len(downloads_res.data)
        
        await message.answer(f"📊 **Statistika:**\n\n👥 Users: `{total_users}`\n📥 Downloads: `{total_downloads}`")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

@dp.message(Command("reklama"))
async def broadcast_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text_to_send = message.text.replace("/reklama", "").strip()
    if not text_to_send:
        await message.answer("⚠️ Reklama matnini kiriting: `/reklama Matn`")
        return
    
    users = supabase.table("users").select("user_id", "is_active").execute().data
    success, blocked = 0, 0
    status_msg = await message.answer("📢 Reklama tarqatilmoqda...")
    
    for user in users:
        uid = user['user_id']
        try:
            await bot.send_message(uid, text_to_send)
            success += 1
            await asyncio.sleep(0.05)
        except:
            blocked += 1
            supabase.table("users").update({"is_active": False}).eq("user_id", uid).execute()
            
    await status_msg.edit_text(f"✅ Tugadi!\nMuvaffaqiyatli: {success}\nBloklaganlar: {blocked}")

@dp.message(F.text.regexp(r'(https?://)?(www\.|vt\.|vm\.|m\.)?(youtube\.com|youtu\.be|instagram\.com|tiktok\.com|facebook\.com|pin.it)/.+'))
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    texts = LANG_TEXTS.get(lang, LANG_TEXTS["uz"])
    
    url = message.text.strip()
    status_msg = await message.answer(texts["fetching"])

    ydl_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }
    loop = asyncio.get_event_loop()
    
    try:
        info = await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).extract_info(url, download=False))
        if not info:
            await status_msg.edit_text(texts["error"])
            return

        cache_id = str(uuid.uuid4())[:8]
        URL_CACHE[cache_id] = url
        extractor = info.get('extractor', '').lower()

        if 'youtube' in extractor:
            available_formats = []
            seen_heights = set()
            if 'formats' in info:
                for f in info['formats']:
                    height = f.get('height')
                    ext = f.get('ext', 'mp4')
                    if height and height >= 144 and height not in seen_heights and f.get('vcodec') != 'none':
                        seen_heights.add(height)
                        available_formats.append({'height': height, 'format_id': f['format_id'], 'ext': ext})
            
            available_formats = sorted(available_formats, key=lambda x: x['height'], reverse=True)[:5]
            
            buttons = []
            for fmt in available_formats:
                buttons.append([InlineKeyboardButton(text=f"🎬 {fmt['height']}p ({fmt['ext'].upper()})", callback_data=f"yt|{cache_id}|{fmt['format_id']}")])
            buttons.append([InlineKeyboardButton(text="🎵 MP3 / Audio", callback_data=f"yt|{cache_id}|audio")])
            
            await status_msg.edit_text(texts["choose_qual"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        else:
            buttons = [
                [InlineKeyboardButton(text="📥 Video (MP4)", callback_data=f"soc|{cache_id}|video")],
                [InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"soc|{cache_id}|audio")]
            ]
            await status_msg.edit_text(texts["choose_fmt"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    except Exception as e:
        await status_msg.edit_text(f"{texts['error']}: {str(e)}")

@dp.callback_query(F.data.startswith("yt|") | F.data.startswith("soc|"))
async def process_download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    texts = LANG_TEXTS.get(lang, LANG_TEXTS["uz"])
    
    data_parts = callback.data.split("|")
    prefix, cache_id, action = data_parts[0], data_parts[1], data_parts[2]
    
    url = URL_CACHE.get(cache_id)
    if not url:
        await callback.answer("Session expired / Sessiya eskirdi", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(texts["downloading"])

    output_template = f"downloads/{uuid.uuid4()}.%(ext)s"
    
    common_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    if action == "audio":
        ydl_opts = {**common_opts, 'format': 'bestaudio/best'}
        is_audio = True
        format_type = "mp3"
    else:
        if prefix == "yt":
            ydl_opts = {**common_opts, 'format': f"{action}+ba/b[ext=mp4]/best"}
            format_type = f"{action}p"
        else:
            ydl_opts = {**common_opts, 'format': 'best/best'}
            format_type = "mp4"
        is_audio = False

    loop = asyncio.get_event_loop()
    try:
        def download():
            with YoutubeDL(ydl_opts) as ydl:
                inf = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(inf)
        
        file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            await callback.message.edit_text(texts["uploading"])
            media_file = FSInputFile(file_path)
            
            platform = "youtube" if "youtube" in url or "youtu.be" in url else ("instagram" if "instagram" in url else "tiktok")
            log_download_to_db(user_id, platform, format_type)

            if is_audio:
                await callback.message.answer_audio(audio=media_file, caption=texts["success_cap"])
            else:
                await callback.message.answer_video(video=media_file, caption=texts["success_cap"])
            
            await callback.message.delete()
        else:
            await callback.message.edit_text(texts["error"])
    except Exception as e:
        await callback.message.edit_text(f"{texts['error']}: {str(e)}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

async def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())