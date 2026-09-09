import logging
from pathlib import Path

from django.conf import settings
from filelock import FileLock
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from knowledge.bootstrap import ensure_default_document
from knowledge.models import IndexBuild, KnowledgeDocument
from qa.models import AnswerCache

logger = logging.getLogger(__name__)


def _embeddings():
    return OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model=settings.EMBEDDING_MODEL,
    )


def load_vectordb():
    index_dir = Path(settings.FAISS_INDEX_DIR)
    if not (index_dir / "index.faiss").exists():
        return None
    return FAISS.load_local(
        str(index_dir),
        _embeddings(),
        allow_dangerous_deserialization=True,
    )


def ensure_index():
    """Return FAISS index, seeding knowledge and rebuilding if the files are missing."""
    vectordb = load_vectordb()
    if vectordb is not None:
        return vectordb

    index_dir = Path(settings.FAISS_INDEX_DIR)
    index_dir.mkdir(parents=True, exist_ok=True)
    with FileLock(str(index_dir / "rebuild.lock")):
        vectordb = load_vectordb()
        if vectordb is not None:
            return vectordb
        seeded = ensure_default_document()
        if seeded:
            logger.info("Loaded default knowledge from data/knowledge.txt")
        result = rebuild_index()
        if not result["ok"]:
            logger.error("Failed to build FAISS index: %s", result.get("error"))
            return None
        logger.info("FAISS index built: %s chunks", result.get("chunks"))
        return load_vectordb()


def rebuild_index():
    if not settings.OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY не задан.", "chunks": 0}

    docs = list(KnowledgeDocument.objects.filter(is_active=True).exclude(content=""))
    if not docs:
        IndexBuild.objects.create(
            document_count=0,
            chunk_count=0,
            embed_model=settings.EMBEDDING_MODEL,
            success=False,
            error="Нет активных документов с текстом.",
        )
        return {"ok": False, "error": "Нет активных документов с текстом.", "chunks": 0}

    langchain_docs = [
        Document(page_content=item.content, metadata={"title": item.title, "id": item.id})
        for item in docs
    ]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=80,
        separators=["\n## ", "\n\n", "\n", " ", ""],
    )
    split_docs = splitter.split_documents(langchain_docs)

    try:
        vectordb = FAISS.from_documents(split_docs, _embeddings())
        index_dir = Path(settings.FAISS_INDEX_DIR)
        index_dir.mkdir(parents=True, exist_ok=True)
        vectordb.save_local(str(index_dir))
    except Exception as exc:
        IndexBuild.objects.create(
            document_count=len(docs),
            chunk_count=len(split_docs),
            embed_model=settings.EMBEDDING_MODEL,
            success=False,
            error=str(exc),
        )
        return {"ok": False, "error": str(exc), "chunks": len(split_docs)}

    IndexBuild.objects.create(
        document_count=len(docs),
        chunk_count=len(split_docs),
        embed_model=settings.EMBEDDING_MODEL,
        success=True,
    )
    AnswerCache.objects.all().delete()
    return {"ok": True, "chunks": len(split_docs), "documents": len(docs)}
