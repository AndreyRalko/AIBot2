from django.contrib import admin

from .models import AnswerCache, ChatMessage, QuestionLog, TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "last_seen_at")
    search_fields = ("telegram_id", "username", "first_name")


@admin.register(QuestionLog)
class QuestionLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "language", "source", "is_unanswered", "question")
    list_filter = ("language", "source", "is_unanswered")
    search_fields = ("question", "answer")
    date_hierarchy = "created_at"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "role")
    list_filter = ("role",)


@admin.register(AnswerCache)
class AnswerCacheAdmin(admin.ModelAdmin):
    list_display = ("question", "updated_at")
    search_fields = ("question", "answer")
