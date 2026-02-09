from langchain_ollama import ChatOllama

from app.core.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL


def get_chat_llm():
    return ChatOllama(model=OLLAMA_CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)
