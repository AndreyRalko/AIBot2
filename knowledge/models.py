from django.conf import settings
from django.db import models


class KnowledgeDocument(models.Model):
    title = models.CharField("Название", max_length=255)
    original_name = models.CharField("Имя файла", max_length=255, blank=True)
    file = models.FileField("Файл", upload_to="knowledge/", blank=True, null=True)
    content = models.TextField("Текст")
    is_active = models.BooleanField("Участвует в индексе", default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Загрузил",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Документ знаний"
        verbose_name_plural = "Документы знаний"

    def __str__(self):
        return self.title

    @property
    def char_count(self):
        return len(self.content or "")


class IndexBuild(models.Model):
    built_at = models.DateTimeField("Собран", auto_now_add=True)
    document_count = models.PositiveIntegerField("Документов")
    chunk_count = models.PositiveIntegerField("Фрагментов")
    embed_model = models.CharField("Модель эмбеддингов", max_length=128)
    success = models.BooleanField("Успешно", default=True)
    error = models.TextField("Ошибка", blank=True)

    class Meta:
        ordering = ["-built_at"]
        verbose_name = "Сборка индекса"
        verbose_name_plural = "Сборки индекса"

    def __str__(self):
        status = "ok" if self.success else "ошибка"
        return f"{self.built_at:%Y-%m-%d %H:%M} ({status})"
