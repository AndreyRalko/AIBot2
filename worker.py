from arq import cron
from arq.connections import RedisSettings
from aiogram import Bot
from config import TELEGRAM_TOKEN
from rag_engine import get_answer
from db.async_session import get_session

bot = Bot(token=TELEGRAM_TOKEN)


async def process_query(ctx, chat_id: int, query: str):
    """Фоновая задача обработки запроса."""
    async for session in get_session():
        answer = await get_answer(query)
        await bot.send_message(chat_id, f"✅ Ответ:\n{answer}")


class WorkerSettings:
    redis_settings = RedisSettings()
    functions = [process_query]
