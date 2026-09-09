import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.conf import settings

from qa.services import atouch_telegram_user, get_chat_history
from rag.engine import get_answer
from rag.indexer import ensure_index

logger = logging.getLogger(__name__)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Здравствуйте! Я помогу с поступлением в КГУ и заявкой на общежитие.\n"
        "Напишите вопрос на русском или казахском языке."
    )


@dp.message(F.text.in_({"/context", "/контекст"}))
async def cmd_context(message: Message):
    user = await atouch_telegram_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or "",
    )
    history = await sync_to_async(get_chat_history)(user)
    if not history:
        await message.answer("Контекст диалога пуст.")
        return
    parts = []
    for item in history:
        role = "Вы" if item.role == "human" else "Бот"
        parts.append(f"{role}:\n{item.content}")
    text = "\n\n".join(parts)
    for i in range(0, len(text), 4000):
        await message.answer(text[i : i + 4000])


@dp.message(F.text)
async def handle_text(message: Message):
    query = (message.text or "").strip()
    if not query:
        return

    user = await atouch_telegram_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or "",
    )
    status = await message.answer("Вопрос принят. Готовлю ответ…")
    try:
        answer = await get_answer(query, user)
    except Exception:
        logger.exception("Failed to answer telegram query")
        answer = "Не удалось получить ответ. Попробуйте ещё раз через минуту."
    await status.edit_text(answer)


async def _run():
    if not settings.TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан. Укажите его в файле .env")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан. Без него база знаний не работает.")
    vectordb = await sync_to_async(ensure_index)()
    if vectordb is None:
        raise RuntimeError(
            "Не собран индекс базы знаний. Проверьте OPENAI_API_KEY и выполните: python manage.py seed_knowledge"
        )
    logger.info("Knowledge index is ready")
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    await dp.start_polling(bot)


def run():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())
