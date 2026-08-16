import sqlite3

import pytest

from src.ai.openrouter_client import AIResponse, OpenRouterClient, OpenRouterError
from src.database.connection import Database
from src.ai.prompts import CLASSIFICATION_SYSTEM_PROMPT, OCR_SYSTEM_PROMPT


def test_missing_api_key_fails_safely():
    with pytest.raises(OpenRouterError, match="belum dikonfigurasi"):
        OpenRouterClient("", "fake/model")


def test_database_connection_error_is_not_silently_ignored(tmp_path):
    directory_instead_of_file = tmp_path / "db-directory"
    directory_instead_of_file.mkdir()
    with pytest.raises(sqlite3.OperationalError):
        Database(directory_instead_of_file).initialize()


def test_bad_request_is_not_retried(monkeypatch):
    calls = {"count": 0}
    captured = {}

    class Response:
        status_code = 400
        is_error = True

    class Client:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, url, **kwargs):
            calls["count"] += 1
            captured["url"] = url
            captured["headers"] = kwargs["headers"]
            return Response()

    monkeypatch.setattr("src.ai.openrouter_client.httpx.Client", Client)
    client = OpenRouterClient("key", "fake/model", max_retries=3)
    with pytest.raises(OpenRouterError, match="Permintaan ditolak"):
        client._post({})
    assert calls["count"] == 1
    assert captured["url"] == OpenRouterClient.API_URL
    assert captured["headers"]["Authorization"] == "Bearer key"


def test_timeout_is_retried_with_limit_and_fails_safely(monkeypatch):
    calls = {"count": 0}

    class Client:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, *_args, **_kwargs):
            calls["count"] += 1
            raise __import__("httpx").TimeoutException("timeout")

    monkeypatch.setattr("src.ai.openrouter_client.httpx.Client", Client)
    monkeypatch.setattr("src.ai.openrouter_client.time.sleep", lambda *_: None)
    client = OpenRouterClient("key", "fake/model", max_retries=2)
    with pytest.raises(OpenRouterError, match="retry"):
        client._post({})
    assert calls["count"] == 3


def test_invalid_key_response_fails_safely_without_retry(monkeypatch):
    calls = {"count": 0}

    class Response:
        status_code = 401
        is_error = True

    class Client:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, *_args, **_kwargs):
            calls["count"] += 1
            return Response()

    monkeypatch.setattr("src.ai.openrouter_client.httpx.Client", Client)
    with pytest.raises(OpenRouterError, match="tidak valid"):
        OpenRouterClient("invalid", "fake/model", max_retries=2)._post({})
    assert calls["count"] == 1


def test_vision_request_contains_base64_schema_and_required_provider_parameters():
    captured = {}

    class Client(OpenRouterClient):
        def _post(self, payload):
            captured.update(payload)
            return AIResponse("{}", self.model, 1, {})

    client = Client("key", "vision/model")
    client.vision_json(b"image-bytes", "image/jpeg", "system", "schema_name", {"type": "object"})
    assert OpenRouterClient.API_URL == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["model"] == "vision/model"
    assert captured["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["strict"] is True
    assert captured["provider"]["require_parameters"] is True
    assert captured["max_tokens"] == 2048
    assert captured["reasoning"] == {"effort": "none"}


def test_classification_request_uses_compact_output_budget():
    captured = {}

    class Client(OpenRouterClient):
        def _post(self, payload):
            captured.update(payload)
            return AIResponse("{}", self.model, 1, {})

    client = Client("key", "vision/model")
    client.vision_json(b"image-bytes", "image/jpeg", "system", "ktp_classification", {"type": "object"})
    assert captured["max_tokens"] == 384


def test_prompts_treat_document_text_as_untrusted_and_forbid_guessing():
    assert "DATA TIDAK TEPERCAYA" in CLASSIFICATION_SYSTEM_PROMPT
    assert "DATA TIDAK TEPERCAYA" in OCR_SYSTEM_PROMPT
    assert "Jangan menebak" in OCR_SYSTEM_PROMPT
    assert "null" in OCR_SYSTEM_PROMPT
