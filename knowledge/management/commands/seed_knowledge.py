from django.core.management.base import BaseCommand, CommandError

from knowledge.bootstrap import DEFAULT_TITLE, read_default_knowledge_text
from knowledge.models import KnowledgeDocument
from rag.indexer import rebuild_index


class Command(BaseCommand):
    help = "Импортирует data/knowledge.txt в базу знаний и собирает индекс"

    def handle(self, *args, **options):
        text = read_default_knowledge_text()
        if not text:
            raise CommandError("Файл data/knowledge.txt не найден или пуст.")

        _doc, created = KnowledgeDocument.objects.update_or_create(
            title=DEFAULT_TITLE,
            defaults={"content": text, "original_name": "knowledge.txt", "is_active": True},
        )
        result = rebuild_index()
        action = "создан" if created else "обновлён"
        if not result["ok"]:
            raise CommandError(f"Документ {action}, индекс не собран: {result['error']}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Документ {action}, индекс собран ({result['chunks']} фрагментов)."
            )
        )
