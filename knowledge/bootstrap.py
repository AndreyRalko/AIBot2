from pathlib import Path

from django.conf import settings

from knowledge.models import KnowledgeDocument

INSTRUCTION_MARKERS = ("[[NO_ANSWER]]", "Давай ответы только")
DEFAULT_TITLE = "Поступление и общежитие КГУ"


def knowledge_file_path() -> Path:
    return Path(settings.BASE_DIR) / "data" / "knowledge.txt"


def read_default_knowledge_text() -> str:
    path = knowledge_file_path()
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    if lines and any(marker in lines[0] for marker in INSTRUCTION_MARKERS):
        text = "\n".join(lines[1:]).strip()
    return text


def ensure_default_document():
    """Load data/knowledge.txt into the DB if there is no active knowledge."""
    if KnowledgeDocument.objects.filter(is_active=True).exclude(content="").exists():
        return False
    text = read_default_knowledge_text()
    if not text:
        return False
    KnowledgeDocument.objects.update_or_create(
        title=DEFAULT_TITLE,
        defaults={"content": text, "original_name": "knowledge.txt", "is_active": True},
    )
    return True
