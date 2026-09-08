from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    username = models.CharField("Username", max_length=255, blank=True)
    first_name = models.CharField("Имя", max_length=255, blank=True)
    last_name = models.CharField("Фамилия", max_length=255, blank=True)
    created_at = models.DateTimeField("Первый визит", auto_now_add=True)
    last_seen_at = models.DateTimeField("Последний визит", auto_now=True)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        return self.username or self.first_name or str(self.telegram_id)


class ChatMessage(models.Model):
    ROLE_HUMAN = "human"
    ROLE_AI = "ai"
    ROLE_CHOICES = (
        (ROLE_HUMAN, "Пользователь"),
        (ROLE_AI, "Бот"),
    )

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Пользователь",
    )
    role = models.CharField("Роль", max_length=16, choices=ROLE_CHOICES)
    content = models.TextField("Текст")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Сообщение диалога"
        verbose_name_plural = "Сообщения диалога"

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"


class QuestionLog(models.Model):
    SOURCE_CACHE = "cache"
    SOURCE_RAG = "rag"
    SOURCE_UNANSWERED = "unanswered"
    SOURCE_CHOICES = (
        (SOURCE_CACHE, "Кэш"),
        (SOURCE_RAG, "RAG"),
        (SOURCE_UNANSWERED, "Без ответа"),
    )

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
        verbose_name="Пользователь",
    )
    question = models.TextField("Вопрос")
    question_ru = models.TextField("Вопрос (ru)", blank=True)
    answer = models.TextField("Ответ", blank=True)
    language = models.CharField("Язык", max_length=8, default="ru")
    source = models.CharField("Источник", max_length=16, choices=SOURCE_CHOICES, default=SOURCE_RAG)
    is_unanswered = models.BooleanField("Без ответа", default=False)
    created_at = models.DateTimeField("Задан", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_unanswered"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return self.question[:80]


class AnswerCache(models.Model):
    question = models.CharField("Вопрос", max_length=512, unique=True)
    answer = models.TextField("Ответ")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Кэш ответа"
        verbose_name_plural = "Кэш ответов"

    def __str__(self):
        return self.question[:80]
