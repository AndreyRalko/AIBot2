from asgiref.sync import sync_to_async
from django.conf import settings

from .models import AnswerCache, ChatMessage, QuestionLog, TelegramUser


def touch_telegram_user(telegram_id, username="", first_name="", last_name=""):
    user, _created = TelegramUser.objects.update_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": username or "",
            "first_name": first_name or "",
            "last_name": last_name or "",
        },
    )
    return user


async def atouch_telegram_user(telegram_id, username="", first_name="", last_name=""):
    return await sync_to_async(touch_telegram_user)(
        telegram_id, username, first_name, last_name
    )


def get_cached_answer(question_ru: str):
    row = AnswerCache.objects.filter(question=question_ru).first()
    return row.answer if row else None


def save_cached_answer(question_ru: str, answer: str):
    AnswerCache.objects.update_or_create(
        question=question_ru,
        defaults={"answer": answer},
    )


def get_chat_history(user: TelegramUser, limit=None):
    limit = limit or settings.CHAT_HISTORY_LIMIT
    qs = ChatMessage.objects.filter(user=user).order_by("-created_at")[:limit]
    return list(reversed(list(qs)))


def append_chat_history(user: TelegramUser, role: str, content: str):
    ChatMessage.objects.create(user=user, role=role, content=content)
    extra = (
        ChatMessage.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("id", flat=True)[settings.CHAT_HISTORY_LIMIT :]
    )
    if extra:
        ChatMessage.objects.filter(id__in=list(extra)).delete()


def log_question(**kwargs):
    return QuestionLog.objects.create(**kwargs)
