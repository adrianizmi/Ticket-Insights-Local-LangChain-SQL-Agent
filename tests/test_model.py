import pytest

from ticket_insights.model import get_ollama_base_url


def test_local_ollama_url_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.delenv("ALLOW_REMOTE_OLLAMA", raising=False)

    assert get_ollama_base_url() == "http://localhost:11434"


def test_remote_ollama_url_requires_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.example.com")
    monkeypatch.delenv("ALLOW_REMOTE_OLLAMA", raising=False)

    with pytest.raises(ValueError, match="ALLOW_REMOTE_OLLAMA=true"):
        get_ollama_base_url()


def test_remote_ollama_url_can_be_explicitly_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.example.com")
    monkeypatch.setenv("ALLOW_REMOTE_OLLAMA", "true")

    assert get_ollama_base_url() == "https://ollama.example.com"
