from __future__ import annotations

"""Fuzz deterministico do funil publico de sanitizacao do decision_core."""

from random import Random
from typing import Any

from app.decision_core.projection import extract_optional_policy_fields

FORBIDDEN_TOKENS = (
    "source_ref",
    "minio",
    "job_id",
    "key=",
    "/tmp",
    "token",
    "secret",
    "authorization",
    "bearer ",
    "akia",
    "-----begin",
    "/app/",
    "/etc/",
    "?token=",
    "?key=",
)


def _flatten_strings(value: Any) -> list[str]:
    """Percorre recursivamente dict/list e coleta apenas strings do output."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for key, inner in value.items():
            if isinstance(key, str):
                out.append(key)
            out.extend(_flatten_strings(inner))
    elif isinstance(value, list):
        for item in value:
            out.extend(_flatten_strings(item))
    return out


def _assert_no_forbidden_tokens(value: Any) -> None:
    """Falha explicitamente com o token e o campo vazado no output achatado."""
    for item in _flatten_strings(value):
        lowered = item.lower()
        for token in FORBIDDEN_TOKENS:
            assert token not in lowered, f"forbidden token leaked: {token!r} in {item!r}"


def _random_scalar(rng: Random) -> Any:
    pool: list[Any] = [
        None,
        True,
        False,
        0,
        1,
        3.14,
        "ok",
        "collector_failed=1",
        "safe_value",
        "unicode_\u200b_ok",
        "contains source_ref=https://secret.example/?token=abc",
        "videos-raw/file.wav",
        "/tmp/file.wav",
        "Authorization: Bearer abc",
        "-----BEGIN PRIVATE KEY-----",
    ]
    return pool[rng.randrange(len(pool))]


def _random_key(rng: Random) -> str:
    pool = [
        "collector_failed",
        "collector_success",
        "retryable_failures",
        "source_ref",
        "minio_path",
        "job_id",
        "query_key",
        "token_value",
        "safe_key",
        "nested",
    ]
    return pool[rng.randrange(len(pool))]


def _generate_signals_dict(rng: Random) -> dict[str, Any]:
    signals: dict[str, Any] = {}
    for _ in range(rng.randint(1, 6)):
        key = _random_key(rng)
        mode = rng.randint(0, 4)
        if mode == 0:
            signals[key] = _random_scalar(rng)
        elif mode == 1:
            signals[key] = [_random_scalar(rng) for _ in range(rng.randint(0, 4))]
        elif mode == 2:
            signals[key] = {"inner": _random_scalar(rng), "source_ref": "http://x?token=y"}
        elif mode == 3:
            signals[key] = [{"job_id": "123"}]
        else:
            signals[key] = object()
    return signals


def _generate_signals_list(rng: Random) -> list[Any]:
    items: list[Any] = []
    for _ in range(rng.randint(1, 8)):
        mode = rng.randint(0, 3)
        if mode == 0:
            items.append(_random_scalar(rng))
        elif mode == 1:
            items.append("source_ref=https://secret.example/?token=abc")
        elif mode == 2:
            items.append("/app/private/path.txt")
        else:
            items.append("collector_error_type:http_4xx=2")
    return items


def _make_policy(signals: Any) -> dict[str, Any]:
    return {
        "version": "v0.2",
        "score": 42,
        "state": "action_required",
        "decision": "investigate_now",
        "signals": signals,
    }


def test_sanitization_fuzz_dict_mode_no_leaks() -> None:
    """Signals em dict malicioso nao devem vazar tokens proibidos no output."""
    rng = Random(1337)

    for _ in range(200):
        out = extract_optional_policy_fields({"policy": _make_policy(_generate_signals_dict(rng))})
        assert isinstance(out, dict)
        if "signals" in out:
            assert isinstance(out["signals"], dict)
        _assert_no_forbidden_tokens(out)


def test_sanitization_fuzz_list_mode_no_leaks() -> None:
    """Signals em list[str] malicioso devem sair filtrados ou omitidos."""
    rng = Random(1337)

    for _ in range(100):
        out = extract_optional_policy_fields({"policy": _make_policy(_generate_signals_list(rng))})
        assert isinstance(out, dict)
        if "signals" in out:
            assert isinstance(out["signals"], dict)
            assert "items" in out["signals"]
        _assert_no_forbidden_tokens(out)


def test_sanitization_fuzz_invalid_types_do_not_raise() -> None:
    """Tipos invalidos devem ser descartados sem excecao e sem leak."""
    out = extract_optional_policy_fields(
        {
            "policy": _make_policy(
                {
                    "nested": {"source_ref": "https://secret.example/?token=abc"},
                    "bytes": b"secret-token",
                    "obj": object(),
                    "bad_list": [{"job_id": "123"}],
                    "ok": 1,
                }
            )
        }
    )

    assert isinstance(out, dict)
    assert out["decision_state"] == "action_required"
    assert out["decision_action"] == "investigate_now"
    assert out["score"] == 42
    assert out["signals"]["ok"] == 1
    _assert_no_forbidden_tokens(out)
