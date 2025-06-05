import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from redis.asyncio import Redis
from arq.connections import create_pool,RedisSettings

from config import TELEGRAM_TOKEN, REDIS_URL
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

parsed = urlparse(REDIS_URL)

redis_settings = RedisSettings(
    host=parsed.hostname,
    port=parsed.port or 6379,
    password=parsed.password,
    database=int(parsed.path[1:]) if parsed.path else 0,
)

@dp.message()
async def handle_message(message: Message):
    """Обрабатывает входящие сообщения и ставит их в очередь."""
    user_id = message.chat.id
    user_message = message.text.strip()

    logger.info(f"📥 Получен запрос от {user_id}: {user_message}")

    redis = await create_pool(redis_settings)
    await redis.enqueue_job("process_query", user_id, user_message)

    await message.answer("⏳ Ваш вопрос принят. Ответ будет отправлен, как только будет готов.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
