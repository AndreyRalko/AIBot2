from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from db.models import Answer
import logging
import os


async def get_cached_answer(query: str, session) -> str | None:
    result = await session.execute(
        select(Answer).where(Answer.question == query)
    )
    entry = result.scalar_one_or_none()
    return entry.answer if entry else None

async def save_answer(question: str, answer: str, session) -> None:
    new_entry = Answer(question=question, answer=answer)
    session.add(new_entry)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
