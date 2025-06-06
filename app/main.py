import asyncio
import logging
from openai import OpenAI
import os
import re
from config import TOKEN, GPT_MODEL, OPENAI_API_KEY, SYSTEM_PROMPT
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart
from file_utils import extract_text_from_docx, extract_text_from_pdf
from database import init_db, get_user_session, save_user_session, reset_user_session

client = OpenAI(api_key=OPENAI_API_KEY)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Создаем кнопки
button1 = KeyboardButton(text="📌 О нас")
button2 = KeyboardButton(text="📞 Связаться с нами")
button3 = KeyboardButton(text="📚 Полезные материалы")
button4 = KeyboardButton(text="📖 Инструкция")
button5 = KeyboardButton(text="⭐ Купить подписку")
button6 = KeyboardButton(text="🧹 Очистить историю")

# Создаем клавиатуру
keyboard = ReplyKeyboardMarkup(
    keyboard=[[button6],[button2], [button4]],  # Кнопки передаются списком списков
    resize_keyboard=True  # Уменьшаем размер клавиатуры
)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Здравствуйте! Отправьте мне договор в формате .docx или .pdf, и я начну анализ.",  reply_markup=keyboard)

# 📞 Связаться с нами
@dp.message(lambda message: message.text == "📞 Связаться с нами")
async def contact_support(message: types.Message):
    await message.answer("Вы всегда можете связаться через поддержку: @MARINA_HMA")

# 🧹 Очистить историю
@dp.message(lambda message: message.text == "🧹 Очистить историю")
async def contact_support(message: types.Message):
    reset_user_session(message.from_user.id)
    await message.answer("История чата очищена ✅\nГотов принимать новые документы")

# 📖 Инструкция (пример запроса)
@dp.message(lambda message: message.text == "📖 Инструкция")
async def send_instruction(message: types.Message):
    instruction_text = (
        "📌 <b>Прикрепите или перешлите в меня файл для анализа:</b>\n"
        "Система проанализирует договор и найдет потенциальные риски для исполнителя"
    )
    await message.answer(instruction_text, parse_mode="HTML")

@dp.message(F.content_type == "document")
async def handle_document(message: Message):
    doc = message.document
    if not doc:
        await message.answer("Файл не найден.")
        return

    file_ext = doc.file_name.split(".")[-1].lower()

    if file_ext not in ["docx", "pdf"]:
        await message.answer("Пожалуйста, отправь файл в формате .docx или .pdf.")
        return

    file_path = f"downloads/{doc.file_name}"
    os.makedirs("downloads", exist_ok=True)

    await bot.download(file=doc.file_id, destination=file_path)

    try:
        if file_ext == "docx":
            text = extract_text_from_docx(file_path)
        elif file_ext == "pdf":
            text = extract_text_from_pdf(file_path)

        await message.answer("🔍 Анализирую договор, это может занять немного времени...")
        # Отправляем эффект "печатает..."
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        analysis = await analyze_contract(message.from_user.id, text)
        htmlText = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', analysis)
        htmlText = re.sub(r'\*(.*?)\*', r'<i>\1</i>', htmlText)
        await send_long_message(message, f"📋 Рекомендации по договору:\n\n{htmlText}")

    except Exception as e:
        logging.exception("Ошибка при извлечении текста:")
        await message.answer("Произошла ошибка при обработке файла. Проверь формат и попробуй снова.")

# Обработчик сообщений
@dp.message()
async def handle_message(message: Message):
    text = message.text
    user_id = message.from_user.id

    # Отправляем эффект "печатает..."
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    analysis = await analyze_contract(user_id, text)
    htmlText = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', analysis)
    htmlText = re.sub(r'\*(.*?)\*', r'<i>\1</i>', htmlText)
    await message.answer(htmlText, parse_mode="HTML")

async def analyze_contract(user_id, text: str) -> str:
    session = await get_user_session(user_id)

    if not session:
        session = [{"role": "system", "content": SYSTEM_PROMPT}]

    session.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=session,
        temperature=0.7
    )
    reply = response.choices[0].message.content.strip()
    session.append({"role": "assistant", "content": reply})

    await save_user_session(user_id, session)
    return reply

async def send_long_message(message: Message, text: str, chunk_size: int = 4000):
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        await message.answer(chunk, parse_mode="HTML")


async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())