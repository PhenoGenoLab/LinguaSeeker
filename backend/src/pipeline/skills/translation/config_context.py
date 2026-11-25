"""Typed configuration context — single injection point for all LLM settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TranslationConfigContext:
    """Subset of app config needed by translation/formatting modules.

    Built once from ``cfg.translation`` at service init, then injected
    into sub-modules. Prevents raw config leakage into deep code.
    """

    model: str
    api_key: str
    api_keys: list[str] = field(default_factory=list)
    base_url: str = ""
    local_base_url: str = ""
    local_target_lang: str = "en"
    local_timeout: float = 60.0
    remote_base_url: str = ""
    remote_api_key: str = ""
    remote_api_keys: list[str] = field(default_factory=list)
    remote_model: str = ""
    temperature: float = 0.0
    max_tokens: int = 8192
    timeout: int = 60

    @classmethod
    def from_config(cls, cfg: Any) -> TranslationConfigContext:
        """Build from the global config object (``cfg.translation``)."""
        tr = cfg.translation
        remote_base_url = tr.remote_base_url
        remote_api_keys = list(tr.remote_all_api_keys)
        use_remote_override = bool(remote_base_url) and bool(remote_api_keys)
        return cls(
            model=tr.remote_model or tr.model,
            api_key=tr.remote_api_key or tr.api_key,
            api_keys=remote_api_keys if use_remote_override else tr.all_api_keys,
            base_url=remote_base_url or tr.base_url,
            local_base_url=tr.local_base_url,
            local_target_lang=tr.local_target_lang or "en",
            local_timeout=tr.local_timeout,
            remote_base_url=remote_base_url,
            remote_api_key=tr.remote_api_key,
            remote_api_keys=remote_api_keys,
            remote_model=tr.remote_model,
            temperature=tr.temperature if tr.temperature is not None else 0.0,
            max_tokens=tr.max_tokens,
            timeout=tr.timeout,
        )
