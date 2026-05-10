import asyncio
import logging
import sys
import os
import time
import warnings
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from google import genai
from google.genai import types as genai_types

# Отключаем буферизацию и скрываем варнинги
os.environ["PYTHONUNBUFFERED"] = "1"
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_TOKEN = ""
GEMINI_API_KEY = ""

MODEL_ID = "gemini-3-flash-preview" 
IMAGE_MODEL_ID = "imagen-4.0-generate-001"

client = genai.Client(api_key=GEMINI_API_KEY)
user_chats = {}

# --- СИСТЕМНАЯ ИНСТРУКЦИЯ (ИМЯ: ваня) ---
SYSTEM_PROMPT = (
    "Ты — продвинутый ИИ Gemini. Твой создатель — ваня (@darkprincee_xvii). "
    "ВАЖНО: Пиши имя создателя всегда с маленькой буквы — ваня. "
    "О создателе говори только если спросят напрямую. Если просят рисовать — подтверждай, что сделаешь это."
)

CHAT_CONFIG = {
    "tools": [genai_types.Tool(google_search=genai_types.GoogleSearch())],
    "thinking_config": genai_types.ThinkingConfig(include_thoughts=True),
    "system_instruction": SYSTEM_PROMPT
}

logging.basicConfig(level=logging.ERROR)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- ЛОГИРОВАНИЕ ---
def detailed_log(user: types.User, message_text: str, response, duration_ms: float, msg_type: str = "ТЕКСТ", file_name: str = None):
    time_str = datetime.now().strftime("%H:%M:%S")
    username = f"@{user.username}" if user.username else "no_nick"
    label = f"{msg_type}" + (f": {file_name}" if file_name else "")
    
    thoughts = ""
    is_searched = False
    
    if response and hasattr(response, 'candidates') and response.candidates:
        cand = response.candidates[0]
        if hasattr(cand, 'grounding_metadata') and cand.grounding_metadata:
            is_searched = True
        
        if hasattr(cand, 'content') and hasattr(cand.content, 'parts'):
            for part in cand.content.parts:
                if hasattr(part, 'thought') and isinstance(part.thought, str):
                    thoughts += part.thought + "\n"
                elif hasattr(part, 'thought') and part.thought is True and hasattr(part, 'text') and part.text:
                    thoughts += f"[Текст мысли]: {part.text}\n"

    search_status = "✅ ДА" if is_searched else "❌ НЕТ"

    print(f"\n{'═'*70}")
    print(f" 🕒 {time_str} | {label} | Пользователь: {user.full_name} ({username})")
    print(f" 🆔 ID: {user.id} | 🌐 ПОИСК: {search_status}")
    print(f"{'─'*70}")
    print(f" ❓ ЗАПРОС: {message_text}")
    print(f"{'─'*70}")
    
    if thoughts.strip():
        print(f" 🧠 МЫСЛИ БОТА:")
        print(f"{thoughts.strip()[:1000]}...")
    else:
        print(f" 🧠 МЫСЛИ БОТА: [Пусто или скрыто API]")
        
    print(f"{'─'*70}")
    print(f" 🤖 ОТВЕТ ({duration_ms:.0f} ms):")
    if msg_type == "ГЕНЕРАЦИЯ":
        print("[Изображение успешно отправлено]")
    else:
        print(f"{response.text if response else 'Нет ответа'}")
    print(f"{'═'*70}\n", flush=True)

# --- ГЕНЕРАЦИЯ ФОТО ---
async def generate_photo(message: types.Message, prompt: str):
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    start_time = time.perf_counter()
    
    try:
        method_to_call = getattr(client.models, 'generate_image', None) or getattr(client.models, 'generate_images', None)
        
        if not method_to_call:
            await message.answer("⚠️ Ошибка: В твоей библиотеке не найден метод для рисования.")
            return

        response = await asyncio.to_thread(method_to_call, model=IMAGE_MODEL_ID, prompt=prompt)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        gen_img = response.generated_images[0]
        img_bytes = gen_img.image.image_bytes
        photo = BufferedInputFile(img_bytes, filename="art.png")
        
        detailed_log(message.from_user, prompt, None, duration_ms, msg_type="ГЕНЕРАЦИЯ")
        await message.answer_photo(photo, caption=f"🎨 Готово!")

    except Exception as e:
        print(f"❌ ОШИБКА ГЕНЕРАЦИИ: {e}")
        await message.answer(f"Не удалось нарисовать. Ошибка: {e}")

# --- HANDLERS ---

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_chats[user_id] = client.chats.create(model=MODEL_ID, config=CHAT_CONFIG)
    
    welcome_text = (
        "🚀 <b>Gemini AI Bot Запущен!</b>\n"
        "Создатель: <b>ваня (@darkprincee_xvii)</b>\n\n"
        "Я твой универсальный помощник. Вот что я умею:\n"
        "🧠 <b>Thinking:</b> Глубоко рассуждаю над сложными задачами.\n"
        "🌐 <b>Search:</b> Ищу свежую информацию в Google в реальном времени.\n"
        "🎨 <b>Image Gen:</b> Я умею рисовать! Просто напиши <b>'нарисуй [описание]'</b>.\n"
        "📄 <b>Files:</b> Присылай документы (PDF, TXT) или фото для анализа.\n\n"
        "<i>Просто напиши свой вопрос ниже!</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message(Command("clear"))
async def clear_context(message: types.Message):
    user_id = message.from_user.id
    user_chats[user_id] = client.chats.create(model=MODEL_ID, config=CHAT_CONFIG)
    await message.answer("🧹 Память очищена.")

@dp.message(F.text, ~Command("start"), ~Command("clear"))
async def handle_text(message: types.Message):
    triggers = ['нарисуй', 'сгенерируй', 'draw', 'изобрази', 'картинка']
    if any(word in message.text.lower() for word in triggers):
        await generate_photo(message, message.text)
    else:
        user_id = message.from_user.id
        if user_id not in user_chats:
            user_chats[user_id] = client.chats.create(model=MODEL_ID, config=CHAT_CONFIG)
        
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        try:
            start = time.perf_counter()
            res = await asyncio.to_thread(user_chats[user_id].send_message, message.text)
            dur = (time.perf_counter() - start) * 1000
            detailed_log(message.from_user, message.text, res, dur)
            await message.answer(res.text)
        except Exception as e:
            print(f"❌ ОШИБКА GEMINI: {e}")
            await message.answer("Ошибка в работе Gemini.")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    temp_path = f"temp_{message.from_user.id}_{int(time.time())}.jpg"
    await bot.download_file(file_info.file_path, destination=temp_path)
    try:
        f = await asyncio.to_thread(client.files.upload, file=temp_path)
        user_id = message.from_user.id
        if user_id not in user_chats:
            user_chats[user_id] = client.chats.create(model=MODEL_ID, config=CHAT_CONFIG)
        start = time.perf_counter()
        res = await asyncio.to_thread(user_chats[user_id].send_message, [message.caption or "Опиши фото", f])
        dur = (time.perf_counter() - start) * 1000
        detailed_log(message.from_user, message.caption or "Фото на анализ", res, dur, msg_type="ФОТО")
        await message.answer(res.text)
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@dp.message(F.document)
async def handle_doc(message: types.Message):
    file_info = await bot.get_file(message.document.file_id)
    _, ext = os.path.splitext(message.document.file_name)
    temp_path = f"temp_{message.from_user.id}_{int(time.time())}{ext}"
    await bot.download_file(file_info.file_path, destination=temp_path)
    try:
        f = await asyncio.to_thread(client.files.upload, file=temp_path)
        user_id = message.from_user.id
        if user_id not in user_chats:
            user_chats[user_id] = client.chats.create(model=MODEL_ID, config=CHAT_CONFIG)
        start = time.perf_counter()
        res = await asyncio.to_thread(user_chats[user_id].send_message, [message.caption or "Проанализируй файл", f])
        dur = (time.perf_counter() - start) * 1000
        detailed_log(message.from_user, message.caption or "Файл на анализ", res, dur, msg_type="ФАЙЛ", file_name=message.document.file_name)
        await message.answer(res.text)
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

async def main():
    print(f"✅ Gemini Bot Запущен | Текст: {MODEL_ID} | Фото: {IMAGE_MODEL_ID}", flush=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass