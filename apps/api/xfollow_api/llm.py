from __future__ import annotations

import json
import time
from typing import Any

import httpx

from .config import RuntimeConfig, load_runtime_config


class LlmError(RuntimeError):
    def __init__(self, message: str, *, transient: bool) -> None:
        super().__init__(message)
        self.transient = transient


_STATUS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _base_url(config: RuntimeConfig) -> str:
    return config.llm_base_url.rstrip("/")


def _headers(config: RuntimeConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if config.llm_api_key:
        headers["Authorization"] = f"Bearer {config.llm_api_key}"
    return headers


def status(config: RuntimeConfig | None = None, *, refresh: bool = False) -> dict[str, Any]:
    config = config or load_runtime_config()
    metadata = {"context_window": config.llm_context_window}
    if not config.llm_base_url or not config.llm_model:
        return {
            "configured": False,
            "available": False,
            "model": config.llm_model or None,
            "error": "llm_not_configured",
            **metadata,
        }
    key = f"{_base_url(config)}:{config.llm_model}"
    now = time.monotonic()
    cached = _STATUS_CACHE.get(key)
    if cached and not refresh and now - cached[0] < 10:
        return cached[1]
    try:
        with httpx.Client(timeout=min(config.llm_timeout_seconds, 8)) as client:
            response = client.get(f"{_base_url(config)}/models", headers=_headers(config))
            response.raise_for_status()
        payload = response.json()
        model_ids = {str(item.get("id")) for item in payload.get("data", []) if isinstance(item, dict)}
        available = config.llm_model in model_ids
        result = {
            "configured": True,
            "available": available,
            "model": config.llm_model,
            "error": None if available else "model_not_served",
            **metadata,
        }
    except httpx.HTTPError as exc:
        result = {
            "configured": True,
            "available": False,
            "model": config.llm_model,
            "error": f"llm_unavailable:{exc.__class__.__name__}",
            **metadata,
        }
    except (TypeError, ValueError):
        result = {
            "configured": True,
            "available": False,
            "model": config.llm_model,
            "error": "llm_invalid_models_response",
            **metadata,
        }
    _STATUS_CACHE[key] = (now, result)
    return result


def chat_text(messages: list[dict[str, str]], *, max_tokens: int | None = None, config: RuntimeConfig | None = None) -> str:
    config = config or load_runtime_config()
    current = status(config)
    if not current["available"]:
        raise LlmError(str(current["error"]), transient=True)
    payload = {
        "model": config.llm_model,
        "messages": messages,
        "temperature": config.llm_temperature,
        "max_tokens": min(max_tokens or config.llm_max_output_tokens, config.llm_max_output_tokens),
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        with httpx.Client(timeout=config.llm_timeout_seconds) as client:
            response = client.post(f"{_base_url(config)}/chat/completions", headers=_headers(config), json=payload)
        if response.status_code >= 500 or response.status_code in {408, 409, 429}:
            raise LlmError(f"llm_http_{response.status_code}", transient=True)
        if response.status_code >= 400:
            raise LlmError(f"llm_http_{response.status_code}", transient=False)
        data = response.json()
    except httpx.TimeoutException as exc:
        raise LlmError(f"llm_timeout:{exc.__class__.__name__}", transient=True) from exc
    except httpx.RequestError as exc:
        raise LlmError(f"llm_unavailable:{exc.__class__.__name__}", transient=True) from exc
    except ValueError as exc:
        raise LlmError("llm_invalid_response", transient=False) from exc
    try:
        content = data["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("llm_missing_content", transient=False) from exc
    if not isinstance(content, str) or not content.strip():
        raise LlmError("llm_missing_content", transient=False)
    return content.strip()


def chat_json(messages: list[dict[str, str]], *, max_tokens: int | None = None, config: RuntimeConfig | None = None) -> Any:
    content = chat_text(messages, max_tokens=max_tokens, config=config)
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.rstrip().endswith("```"):
            content = content.rstrip()[:-3]
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise LlmError("llm_invalid_json", transient=False) from exc
