from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from knowledge.models import KnowledgeDocument
from rag.indexer import rebuild_index

INSTRUCTION_MARKERS = ("[[NO_ANSWER]]", "Давай ответы только")


class Command(BaseCommand):
    help = "Импортирует data/knowledge.txt в базу знаний и собирает индекс"

    def handle(self, *args, **options):
        path = Path(settings.BASE_DIR) / "data" / "knowledge.txt"
        if not path.exists():
            self.stderr.write(f"Файл не найден: {path}")
            return

        text = path.read_text(encoding="utf-8").strip()
        lines = text.splitlines()
        if lines and any(marker in lines[0] for marker in INSTRUCTION_MARKERS):
            text = "\n".join(lines[1:]).strip()

        doc, created = KnowledgeDocument.objects.update_or_create(
            title="Поступление и общежитие КГУ",
            defaults={"content": text, "original_name": "knowledge.txt", "is_active": True},
        )
        result = rebuild_index()
        action = "создан" if created else "обновлён"
        if result["ok"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Документ {action}, индекс собран ({result['chunks']} фрагментов)."
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"Документ {action}, индекс: {result['error']}"))
