from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from rag_engine import get_answer
from config import TELEGRAM_TOKEN
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    user_message = update.message.text.strip()
    if not user_message:
        await update.message.reply_text("Пожалуйста, введите текст.")
        return

    try:
        answer = await get_answer(user_message)
        await update.message.reply_text(answer)
    except Exception as e:
        logging.exception("Ошибка при обработке сообщения:")
        await update.message.reply_text("Произошла ошибка при обработке запроса.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()  # ← здесь используется токен из config
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
