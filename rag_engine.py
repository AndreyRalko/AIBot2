from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

from config import OPENAI_API_KEY
from db.crud import get_cached_answer, save_answer
from db.async_session import get_session


def get_qa_chain():
    loader = TextLoader("data/knowledge.txt", encoding='utf-8')
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = FAISS.from_documents(split_docs, embeddings)
    retriever = vectordb.as_retriever()

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY)
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)


qa_chain = get_qa_chain()


async def get_answer(query: str) -> str:
    async for session in get_session():
        cached = await get_cached_answer(query, session)
        if cached:
            return cached

        # Вызов асинхронного метода arun для получения ответа
        result = await qa_chain.arun(query)

        await save_answer(query, result, session)
        if not result:
            print("⚠️ Получен пустой ответ от LLM.")
            return "Извините, не удалось найти ответ."
        return result
