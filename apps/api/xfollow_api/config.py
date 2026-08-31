from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    app_env: str = "local"
    default_locale: str = "es"
    supported_locales: list[str] = Field(default_factory=lambda: ["es", "ca"])
    postgres_dsn: str = ""
    db_required: bool = False
    db_connect_timeout: int = 3
    integrations_enabled: bool = True
    object_storage_endpoint: str = "http://host.docker.internal:8333"
    object_storage_bucket: str = "procureai"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
    object_storage_region: str = "eu-west-1"
    llm_base_url: str = "http://vllm:8000/v1"
    llm_model: str = "ver_modelo_real_en_destino"
    llm_api_key: str = ""
    llm_context_window: int = 128000
    llm_max_output_tokens: int = 8192
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 300
    ai_worker_poll_seconds: int = 3
    ai_retry_max_seconds: int = 300
    ai_source_max_chars: int = 12000
    ai_source_total_chars: int = 60000
    upload_max_bytes: int = 25 * 1024 * 1024
    auth_mode: str = "development_headers"
    auth_bearer_token: str = ""
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3100", "http://127.0.0.1:3100"])
    force_memory: bool = False


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _get(values: dict[str, str], key: str, default: str) -> str:
    return os.environ.get(key) or values.get(key) or default


def _get_int(values: dict[str, str], key: str, default: int) -> int:
    raw = _get(values, key, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(values: dict[str, str], key: str, default: float) -> float:
    raw = _get(values, key, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


def _get_bool(values: dict[str, str], key: str, default: bool) -> bool:
    raw = _get(values, key, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "infra" / "postgres" / "001_xfollow_schema.sql").exists():
            return parent
    return Path.cwd()


def load_runtime_config(env_path: str | Path | None = None) -> RuntimeConfig:
    path = Path(env_path) if env_path else repo_root() / ".env.local"
    values = _read_env_file(path)
    supported = _get(values, "APP_SUPPORTED_LOCALES", "es,ca")
    cors = _get(values, "CORS_ORIGINS", "http://localhost:3100,http://127.0.0.1:3100")
    return RuntimeConfig(
        app_env=_get(values, "APP_ENV", "local"),
        default_locale=_get(values, "APP_DEFAULT_LOCALE", "es"),
        supported_locales=[item.strip() for item in supported.split(",") if item.strip()],
        postgres_dsn=_get(values, "POSTGRES_DSN", RuntimeConfig().postgres_dsn),
        db_required=_get_bool(values, "XFOLLOW_DB_REQUIRED", _get(values, "APP_ENV", "local").lower() in {"production", "prod"}),
        db_connect_timeout=_get_int(values, "XFOLLOW_DB_CONNECT_TIMEOUT", 3),
        integrations_enabled=_get_bool(values, "XFOLLOW_INTEGRATIONS_ENABLED", True),
        object_storage_endpoint=_get(values, "OBJECT_STORAGE_ENDPOINT", RuntimeConfig().object_storage_endpoint),
        object_storage_bucket=_get(values, "OBJECT_STORAGE_BUCKET", RuntimeConfig().object_storage_bucket),
        object_storage_access_key=_get(values, "OBJECT_STORAGE_ACCESS_KEY", ""),
        object_storage_secret_key=_get(values, "OBJECT_STORAGE_SECRET_KEY", ""),
        object_storage_region=_get(values, "OBJECT_STORAGE_REGION", "eu-west-1"),
        llm_base_url=_get(values, "LLM_BASE_URL", RuntimeConfig().llm_base_url),
        llm_model=_get(values, "LLM_MODEL", RuntimeConfig().llm_model),
        llm_api_key=_get(values, "LLM_API_KEY", ""),
        llm_context_window=_get_int(values, "LLM_CONTEXT_WINDOW", 128000),
        llm_max_output_tokens=_get_int(values, "LLM_MAX_OUTPUT_TOKENS", 8192),
        llm_temperature=_get_float(values, "LLM_TEMPERATURE", 0.2),
        llm_timeout_seconds=_get_int(values, "LLM_TIMEOUT_SECONDS", 300),
        ai_worker_poll_seconds=max(1, _get_int(values, "XFOLLOW_AI_WORKER_POLL_SECONDS", 3)),
        ai_retry_max_seconds=max(15, _get_int(values, "XFOLLOW_AI_RETRY_MAX_SECONDS", 300)),
        ai_source_max_chars=max(1000, _get_int(values, "XFOLLOW_AI_SOURCE_MAX_CHARS", 12000)),
        ai_source_total_chars=max(4000, _get_int(values, "XFOLLOW_AI_SOURCE_TOTAL_CHARS", 60000)),
        upload_max_bytes=max(1024, _get_int(values, "XFOLLOW_UPLOAD_MAX_BYTES", 25 * 1024 * 1024)),
        auth_mode=_get(values, "AUTH_MODE", "development_headers"),
        auth_bearer_token=_get(values, "API_AUTH_BEARER_TOKEN", ""),
        cors_origins=[item.strip() for item in cors.split(",") if item.strip()],
        force_memory=_get_bool(values, "XFOLLOW_FORCE_MEMORY", False),
    )


def sanitized_config(config: RuntimeConfig) -> dict[str, Any]:
    data = config.model_dump()
    data["postgres_dsn"] = _redact_dsn(config.postgres_dsn)
    data["llm_api_key"] = "***" if config.llm_api_key else ""
    data["auth_bearer_token"] = "***" if config.auth_bearer_token else ""
    data["object_storage_access_key"] = "***" if config.object_storage_access_key else ""
    data["object_storage_secret_key"] = "***" if config.object_storage_secret_key else ""
    return data


def _redact_dsn(value: str) -> str:
    if "@" not in value or "://" not in value:
        return value
    scheme, rest = value.split("://", 1)
    _, host = rest.rsplit("@", 1)
    return f"{scheme}://***:***@{host}"
