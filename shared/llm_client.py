"""
shared/llm_client.py
--------------------
Single entry point for model calls across the course.

Supports Anthropic, OpenAI, or side-by-side comparison mode while preserving the
simple ask(system, user, model, max_tokens) interface used by the exercises.
"""

import json
import os
import re
from typing import Any


ANTHROPIC_DEFAULT_MODEL = "claude-opus-4-5-20251101"
OPENAI_DEFAULT_MODEL = "gpt-5.4-mini"

_anthropic_client = None
_openai_client = None


def _sanitize_json(raw: str) -> str:
    """
    Replace literal newlines and other control characters inside JSON string
    values with proper escape sequences.
    """
    result = []
    in_string = False
    escape_next = False
    for ch in raw:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == "\\" and in_string:
            result.append(ch)
            escape_next = True
        elif ch == '"':
            result.append(ch)
            in_string = not in_string
        elif in_string and ch == "\n":
            result.append("\\n")
        elif in_string and ch == "\r":
            result.append("\\r")
        elif in_string and ch == "\t":
            result.append("\\t")
        else:
            result.append(ch)
    return "".join(result)


def _parse_json_response(raw: str, provider: str) -> dict:
    raw = raw.strip()

    # Strip markdown code fences if present.
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence_match:
        raw = fence_match.group(1).strip()
    elif raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).strip()

    raw = _sanitize_json(raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{provider} response could not be parsed as JSON.\n"
            f"Raw response:\n{raw}\n\nError: {e}"
        ) from e


def _normalize_provider(provider: str | None = None) -> str:
    selected = (provider or os.environ.get("AI_PROVIDER") or "auto").strip().lower()
    aliases = {
        "claude": "anthropic",
        "anthropic": "anthropic",
        "openai": "openai",
        "codex": "openai",
        "both": "both",
        "compare": "both",
        "comparison": "both",
    }
    if selected == "auto":
        if os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
            return "openai"
        return "anthropic"
    if selected not in aliases:
        raise ValueError(
            f"Unsupported AI_PROVIDER={selected!r}. Use anthropic, openai, or both."
        )
    return aliases[selected]


def _looks_like_anthropic_model(model: str | None) -> bool:
    return bool(model and model.startswith("claude-"))


def _looks_like_openai_model(model: str | None) -> bool:
    return bool(model and (model.startswith("gpt-") or model.startswith("o")))


def _model_for_provider(provider: str, requested: str | None) -> str:
    if provider == "anthropic":
        env_model = os.environ.get("ANTHROPIC_MODEL")
        if env_model:
            return env_model
        if requested and not _looks_like_openai_model(requested):
            return requested
        return ANTHROPIC_DEFAULT_MODEL

    env_model = os.environ.get("OPENAI_MODEL")
    if env_model:
        return env_model
    if requested and not _looks_like_anthropic_model(requested):
        return requested
    return OPENAI_DEFAULT_MODEL


def _get_anthropic_client() -> Any:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Run: export ANTHROPIC_API_KEY=your_key_here"
            )
        import anthropic

        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def _get_openai_client() -> Any:
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Run: export OPENAI_API_KEY=your_key_here"
            )
        from openai import OpenAI

        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _ask_anthropic(system: str, user: str, model: str, max_tokens: int) -> dict:
    client = _get_anthropic_client()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = message.content[0].text.strip()
    return _parse_json_response(raw, "Anthropic")


def _openai_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    if chunks:
        return "".join(chunks)

    return str(response)


def _ask_openai(system: str, user: str, model: str, max_tokens: int) -> dict:
    client = _get_openai_client()
    request: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_output_tokens": max_tokens,
    }

    # JSON mode is useful for these exercises, but OpenAI requires "JSON" to
    # appear in context before enabling it.
    if "json" in f"{system}\n{user}".lower():
        request["text"] = {"format": {"type": "json_object"}}

    response = client.responses.create(**request)
    raw = _openai_output_text(response).strip()
    return _parse_json_response(raw, "OpenAI")


def compare(
    system: str,
    user: str,
    model: str | None = None,
    max_tokens: int = 1024,
) -> dict:
    """
    Run the same prompt against Anthropic and OpenAI and return both results.

    Missing API keys are reported as skipped entries so comparison mode can still
    show partial output while someone is wiring up credentials.
    """
    comparison = {}
    for provider in ("anthropic", "openai"):
        model_name = _model_for_provider(provider, model)
        key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        if not os.environ.get(key_name):
            comparison[provider] = {
                "status": "skipped",
                "model": model_name,
                "error": f"{key_name} is not set",
            }
            continue

        try:
            comparison[provider] = {
                "status": "ok",
                "model": model_name,
                "result": ask(
                    system=system,
                    user=user,
                    model=model_name,
                    max_tokens=max_tokens,
                    provider=provider,
                ),
            }
        except Exception as exc:  # Keep side-by-side runs useful even if one fails.
            comparison[provider] = {
                "status": "error",
                "model": model_name,
                "error": f"{type(exc).__name__}: {exc}",
            }

    return comparison


def ask(
    system: str,
    user: str,
    model: str | None = None,
    max_tokens: int = 1024,
    provider: str | None = None,
) -> dict:
    """
    Call one provider, or both providers with AI_PROVIDER=both, and return JSON.
    """
    selected = _normalize_provider(provider)
    if selected == "both":
        return compare(system=system, user=user, model=model, max_tokens=max_tokens)

    model_name = _model_for_provider(selected, model)
    if selected == "anthropic":
        return _ask_anthropic(system, user, model_name, max_tokens)
    if selected == "openai":
        return _ask_openai(system, user, model_name, max_tokens)

    raise ValueError(f"Unsupported provider: {selected}")
