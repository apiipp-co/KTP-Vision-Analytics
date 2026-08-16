from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

import httpx


class OpenRouterError(RuntimeError):
    """Safe application-level OpenRouter error."""


@dataclass
class AIResponse:
    content: str
    model: str
    duration_ms: int
    usage: dict[str, Any]
    request_id: str | None = None


class OpenRouterClient:
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    TRANSIENT_STATUS = {408, 409, 429, 500, 502, 503, 504}

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 90, max_retries: int = 2):
        if not api_key:
            raise OpenRouterError("OPENROUTER_API_KEY belum dikonfigurasi.")
        if not model:
            raise OpenRouterError("OPENROUTER_MODEL belum dikonfigurasi.")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def vision_json(self, image_bytes: bytes, mime_type: str, system_prompt: str, schema_name: str, schema: dict) -> AIResponse:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analisis gambar berikut sesuai instruksi sistem."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
                ]},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
            "provider": {"require_parameters": True},
        }
        return self._post(payload)

    def _post(self, payload: dict[str, Any]) -> AIResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/local/ktp-vision-analytics",
            "X-Title": "KTP Vision Analytics",
        }
        started = time.monotonic()
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(self.API_URL, headers=headers, json=payload)
                if response.status_code in {401, 403}:
                    raise OpenRouterError("API key OpenRouter tidak valid atau tidak memiliki akses.")
                if response.status_code == 400:
                    raise OpenRouterError("Permintaan ditolak model. Periksa dukungan vision dan structured output model.")
                if response.status_code == 402:
                    raise OpenRouterError("Kredit/limit akun OpenRouter tidak mencukupi.")
                if response.status_code == 404:
                    raise OpenRouterError("Model OpenRouter tidak ditemukan atau sedang tidak tersedia.")
                if response.status_code in {413, 415, 422}:
                    raise OpenRouterError("Gambar atau struktur permintaan ditolak; permintaan tidak di-retry.")
                if response.status_code not in self.TRANSIENT_STATUS:
                    if response.is_error:
                        raise OpenRouterError(f"OpenRouter menolak permintaan (HTTP {response.status_code}).")
                elif attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 4))
                    continue
                else:
                    raise OpenRouterError("Layanan OpenRouter sedang sibuk/tidak tersedia. Coba lagi nanti.")
                body = response.json()
                choices = body.get("choices") or []
                if not choices:
                    raise OpenRouterError("OpenRouter tidak mengembalikan hasil model.")
                content = choices[0].get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    raise OpenRouterError("Respons model kosong atau tidak didukung.")
                return AIResponse(
                    content=content,
                    model=str(body.get("model") or self.model),
                    duration_ms=round((time.monotonic() - started) * 1000),
                    usage=body.get("usage") if isinstance(body.get("usage"), dict) else {},
                    request_id=body.get("id"),
                )
            except OpenRouterError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 4))
                    continue
        raise OpenRouterError("Gagal terhubung ke OpenRouter setelah retry terbatas.") from last_error
