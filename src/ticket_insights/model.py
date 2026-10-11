import os
from urllib.parse import urlsplit

from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
LOCAL_OLLAMA_HOSTS = {"localhost", "127.0.0.1", "::1"}


def get_ollama_base_url() -> str:
    """Return a local endpoint or require explicit authorization for a remote one."""
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    hostname = urlsplit(base_url).hostname
    allow_remote = os.getenv("ALLOW_REMOTE_OLLAMA", "").lower() == "true"

    if hostname in LOCAL_OLLAMA_HOSTS or allow_remote:
        return base_url

    raise ValueError(
        "OLLAMA_BASE_URL must use localhost, 127.0.0.1, or ::1. "
        "To explicitly authorize a remote endpoint, set "
        "ALLOW_REMOTE_OLLAMA=true."
    )


def create_chat_model() -> ChatOllama:
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct"),
        base_url=get_ollama_base_url(),
        temperature=0,
        reasoning=False,
        num_predict=256,
    )


def summarize_ticket(ollama_model: ChatOllama, ticket_text: str) -> AIMessage:
    messages: list[tuple[str, str]] = [
        (
            "system",
            "Restate only explicit claims from the ticket. "
            "Start exactly with 'The user reports that '. "
            "Do not explain or interpret error codes. "
            "Do not mention causes, permissions, systems, websites, or data that is absent.",
        ),
        (
            "human",
            ticket_text,
        ),
    ]
    return ollama_model.invoke(messages)
