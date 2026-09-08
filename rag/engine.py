from asgiref.sync import sync_to_async
from django.conf import settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langdetect import DetectorFactory, LangDetectException, detect

from qa.models import ChatMessage, TelegramUser
from qa.services import (
    append_chat_history,
    get_cached_answer,
    get_chat_history,
    log_question,
    save_cached_answer,
)
from rag.indexer import load_vectordb

DetectorFactory.seed = 0

NO_ANSWER_TOKEN = "[[NO_ANSWER]]"

SYSTEM_PROMPT = """Ты консультант приёмной комиссии университета (КГУ).
Отвечай по переданному контексту из базы знаний.
Если в контексте есть нужные факты — обязательно используй их, даже если ранее бот писал, что данных нет.
Если в контексте действительно нет ответа — вежливо скажи, что информации нет, и добавь {token}.
Не выдумывай сроки, баллы, документы и процедуры.
Пиши кратко, по шагам, на русском языке.
""".format(token=NO_ANSWER_TOKEN)


def detect_language(text: str) -> str:
    sample = (text or "").strip()
    if not sample:
        return "ru"
    try:
        code = detect(sample)
    except LangDetectException:
        code = "ru"
    if code in {"kk", "kz"}:
        return "kk"
    return "ru"


async def translate_text(text: str, target_lang: str) -> str:
    to = "русский" if target_lang == "ru" else "казахский"
    llm = ChatOpenAI(
        openai_api_key=settings.OPENAI_API_KEY,
        model=settings.CHAT_MODEL,
        temperature=0,
    )
    resp = await llm.ainvoke(
        [HumanMessage(content=f"Переведи на {to} язык, точно и кратко, без пояснений:\n{text}")]
    )
    return (resp.content or "").strip()


def _history_messages(rows):
    messages = []
    for row in rows:
        if row.role == ChatMessage.ROLE_HUMAN:
            messages.append(HumanMessage(content=row.content))
        else:
            messages.append(AIMessage(content=row.content))
    return messages


def _normalize_query(text: str) -> str:
    replacements = {
        "атестат": "аттестат",
        "атестата": "аттестата",
        "коледж": "колледж",
        "закнчили": "закончили",
        "насельнный": "населённый",
    }
    out = text
    lower = text.lower()
    for src, dst in replacements.items():
        idx = lower.find(src)
        while idx != -1:
            out = out[:idx] + dst + out[idx + len(src) :]
            lower = out.lower()
            idx = lower.find(src, idx + len(dst))
    return out


def _retrieve(query_ru: str):
    vectordb = load_vectordb()
    if vectordb is None:
        return None, True, "empty_index"
    query = _normalize_query(query_ru)
    pairs = vectordb.similarity_search_with_score(query, k=5)
    if not pairs:
        return [], True, "no_hits"
    # Всегда отдаём ближайшие чанки модели: жёсткий порог L2 отсекал верные ответы.
    return pairs[:4], False, "ok"


async def generate_answer(query_ru: str, history_rows, context_text: str) -> str:
    llm = ChatOpenAI(
        openai_api_key=settings.OPENAI_API_KEY,
        model=settings.CHAT_MODEL,
        temperature=0,
    )
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_history_messages(history_rows))
    messages.append(
        HumanMessage(
            content=(
                f"Контекст из базы знаний:\n{context_text}\n\n"
                f"Вопрос абитуриента:\n{query_ru}"
            )
        )
    )
    resp = await llm.ainvoke(messages)
    return (resp.content or "").strip()


def _fallback_unanswered() -> str:
    return (
        "К сожалению, в базе знаний нет информации по этому вопросу. "
        f"Обратитесь в приёмную комиссию: {settings.SUPPORT_WHATSAPP}"
    )


async def get_answer(query: str, user: TelegramUser) -> str:
    original = query.strip()
    lang = detect_language(original)
    query_ru = await translate_text(original, "ru") if lang == "kk" else original
    query_ru = _normalize_query(query_ru)

    cached = await sync_to_async(get_cached_answer)(query_ru)
    if cached:
        await sync_to_async(log_question)(
            user=user,
            question=original,
            question_ru=query_ru,
            answer=cached,
            language=lang,
            source="cache",
            is_unanswered=False,
        )
        return await translate_text(cached, "kk") if lang == "kk" else cached

    history = await sync_to_async(get_chat_history)(user)
    pairs, is_unanswered, reason = await sync_to_async(_retrieve)(query_ru)

    if is_unanswered:
        answer_ru = _fallback_unanswered()
        await sync_to_async(log_question)(
            user=user,
            question=original,
            question_ru=query_ru,
            answer=answer_ru,
            language=lang,
            source="unanswered",
            is_unanswered=True,
        )
        return await translate_text(answer_ru, "kk") if lang == "kk" else answer_ru

    context_text = "\n\n".join(doc.page_content for doc, _score in pairs)
    answer_ru = await generate_answer(query_ru, history, context_text)
    no_answer = NO_ANSWER_TOKEN in answer_ru
    answer_ru = answer_ru.replace(NO_ANSWER_TOKEN, "").strip() or _fallback_unanswered()

    await sync_to_async(log_question)(
        user=user,
        question=original,
        question_ru=query_ru,
        answer=answer_ru,
        language=lang,
        source="unanswered" if no_answer else "rag",
        is_unanswered=no_answer,
    )
    if not no_answer:
        await sync_to_async(save_cached_answer)(query_ru, answer_ru)

    await sync_to_async(append_chat_history)(user, ChatMessage.ROLE_HUMAN, query_ru)
    await sync_to_async(append_chat_history)(user, ChatMessage.ROLE_AI, answer_ru)
    return await translate_text(answer_ru, "kk") if lang == "kk" else answer_ru
