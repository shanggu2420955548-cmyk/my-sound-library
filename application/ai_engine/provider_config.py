"""
AI provider configuration helpers.

Centralizes built-in and user-defined OpenAI-compatible LLM providers so UI,
translation, search, and generation tools do not drift into separate hardcoded
model maps.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from transcriptionist_v3.application.ai_engine.base import AIServiceConfig
from transcriptionist_v3.core.config import AppConfig


BUILTIN_AI_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "deepseek",
        "label": "DeepSeek V3 (推荐)",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "requires_key": True,
        "editable": False,
        "local": False,
    },
    {
        "id": "openai",
        "label": "ChatGPT (GPT-4o/mini)",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "requires_key": True,
        "editable": False,
        "local": False,
    },
    {
        "id": "doubao",
        "label": "豆包 (高并发)",
        "provider": "doubao",
        "model": "doubao-pro-4k",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "requires_key": True,
        "editable": False,
        "local": False,
    },
    {
        "id": "local",
        "label": "本地模型 (Ollama/LM Studio)",
        "provider": "local",
        "model": "",
        "base_url": "http://localhost:1234/v1",
        "requires_key": False,
        "editable": True,
        "local": True,
    },
]


def builtin_provider_count() -> int:
    return len(BUILTIN_AI_PROVIDERS)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def get_custom_ai_providers() -> list[dict[str, Any]]:
    raw = AppConfig.get("ai.custom_providers", [])
    if not isinstance(raw, list):
        return []

    providers: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        name = _clean_text(item.get("name") or item.get("label"))
        base_url = _clean_text(item.get("base_url"))
        model = _clean_text(item.get("model"))
        if not name or not base_url or not model:
            continue

        provider_id = _clean_text(item.get("id")) or f"custom-{uuid4().hex[:8]}"
        providers.append(
            {
                "id": provider_id,
                "label": name,
                "provider": _clean_text(item.get("provider")) or "custom",
                "model": model,
                "base_url": base_url,
                "api_key": _clean_text(item.get("api_key")),
                "requires_key": bool(item.get("requires_key", True)),
                "editable": True,
                "local": False,
                "custom": True,
            }
        )
    return providers


def save_custom_ai_providers(providers: list[dict[str, Any]]) -> None:
    cleaned: list[dict[str, Any]] = []
    for item in providers or []:
        if not isinstance(item, dict):
            continue
        name = _clean_text(item.get("name") or item.get("label"))
        base_url = _clean_text(item.get("base_url"))
        model = _clean_text(item.get("model"))
        if not name or not base_url or not model:
            continue
        cleaned.append(
            {
                "id": _clean_text(item.get("id")) or f"custom-{uuid4().hex[:8]}",
                "name": name,
                "provider": _clean_text(item.get("provider")) or "custom",
                "model": model,
                "base_url": base_url,
                "api_key": _clean_text(item.get("api_key")),
                "requires_key": bool(item.get("requires_key", True)),
            }
        )
    AppConfig.set("ai.custom_providers", cleaned)


def get_ai_provider_options() -> list[dict[str, Any]]:
    return [dict(p) for p in BUILTIN_AI_PROVIDERS] + get_custom_ai_providers()


def get_ai_provider_by_index(index: int | str | None) -> dict[str, Any]:
    options = get_ai_provider_options()
    try:
        idx = int(index or 0)
    except (TypeError, ValueError):
        idx = 0
    if idx < 0 or idx >= len(options):
        idx = 0
    provider = dict(options[idx])

    if provider.get("id") == "local":
        provider["base_url"] = _clean_text(AppConfig.get("ai.local_base_url", "")) or provider["base_url"]
        provider["model"] = _clean_text(AppConfig.get("ai.local_model_name", ""))
    return provider


def update_custom_ai_provider(provider_id: str, updates: dict[str, Any]) -> bool:
    providers = get_custom_ai_providers()
    changed = False
    for provider in providers:
        if provider.get("id") == provider_id:
            provider.update(updates or {})
            changed = True
            break
    if changed:
        save_custom_ai_providers(providers)
    return changed


def delete_custom_ai_provider(provider_id: str) -> bool:
    providers = get_custom_ai_providers()
    kept = [p for p in providers if p.get("id") != provider_id]
    if len(kept) == len(providers):
        return False
    save_custom_ai_providers(kept)
    return True


def build_ai_service_config_from_app(
    system_prompt: str = "",
    timeout: int = 30,
    max_tokens: int = 256,
    temperature: float = 0.3,
) -> tuple[Optional[AIServiceConfig], Optional[str], dict[str, Any]]:
    provider = get_ai_provider_by_index(AppConfig.get("ai.model_index", 0))
    provider_id = _clean_text(provider.get("provider")) or "custom"
    label = _clean_text(provider.get("label")) or provider_id
    model_name = _clean_text(provider.get("model"))
    base_url = _clean_text(provider.get("base_url"))

    if provider_id == "local":
        api_key = ""
        if not base_url or not model_name:
            return None, "请在设置中配置本地模型的 Base URL 和模型名称（Ollama / LM Studio）", provider
    elif provider.get("custom"):
        api_key = _clean_text(provider.get("api_key"))
        if bool(provider.get("requires_key", True)) and not api_key:
            return None, f"请在设置中配置 {label} 的 API Key", provider
    else:
        api_key = _clean_text(AppConfig.get("ai.api_key", ""))
        if bool(provider.get("requires_key", True)) and not api_key:
            return None, "请在设置 -> AI 配置 中配置 API 密钥", provider

    config = AIServiceConfig(
        provider_id=provider_id,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        system_prompt=system_prompt,
        timeout=timeout,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return config, None, provider


def uses_max_completion_tokens(provider_id: str, model_name: str) -> bool:
    provider = _clean_text(provider_id).lower()
    model = _clean_text(model_name).lower()
    # GPT-5+/o-series models reject the legacy Chat Completions max_tokens
    # field even when they are configured through a custom OpenAI-compatible
    # provider entry.
    return (
        model.startswith("gpt-5")
        or model.startswith("o1")
        or model.startswith("o3")
        or model.startswith("o4")
    )


def apply_chat_completion_params(
    payload: dict[str, Any],
    provider_id: str,
    model_name: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> None:
    """Apply Chat Completions params compatible with the selected model."""
    try:
        token_limit = int(max_tokens or 0)
    except (TypeError, ValueError):
        token_limit = 0

    if uses_max_completion_tokens(provider_id, model_name):
        if token_limit > 0:
            payload["max_completion_tokens"] = token_limit
        return

    if token_limit > 0:
        payload["max_tokens"] = token_limit
    if temperature is not None:
        payload["temperature"] = temperature
