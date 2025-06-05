# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import QuestionAnswer

engine = create_engine("sqlite:///qa_cache.db", echo=False)
Session = sessionmaker(bind=engine)

def get_cached_answer(question: str) -> str | None:
    session = Session()
    try:
        row = session.query(QuestionAnswer).filter_by(question=question).first()
        return row.answer if row else None
    finally:
        session.close()

def save_answer(question: str, answer: str) -> None:
    session = Session()
    try:
        qa = QuestionAnswer(question=question, answer=answer)
        session.merge(qa)  # merge: вставка или обновление
        session.commit()
    finally:
        session.close()
