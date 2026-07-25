from __future__ import annotations

import os
from typing import Any

from .types import ModelCard


def build_provider(model: ModelCard):
    """Constrói LLMProvider a partir do ModelCard."""
    if model.provider == "mock":
        raise ValueError("provider mock usa run_mock_agent; defina provider litellm/ollama")

    if model.provider == "litellm":
        from harness_core.providers.litellm_provider import LiteLLMProvider

        if not model.model:
            raise ValueError("ModelCard.model é obrigatório para provider litellm")
        api_key_env = model.metadata.get("api_key_env")
        api_key = os.environ.get(api_key_env) if api_key_env else None
        return LiteLLMProvider(
            model.model,
            api_key=api_key,
            temperature=float(model.metadata.get("temperature", 0.0)),
            max_tokens=int(model.metadata.get("max_tokens", 4096)),
        )

    if model.provider == "ollama":
        from harness_core.providers.litellm_provider import LiteLLMProvider

        model_name = model.model or "ollama/llama3.2"
        if not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"
        return LiteLLMProvider(
            model_name,
            temperature=float(model.metadata.get("temperature", 0.0)),
            max_tokens=int(model.metadata.get("max_tokens", 4096)),
            api_base=model.metadata.get("api_base", "http://127.0.0.1:11434"),
        )

    raise ValueError(f"provider desconhecido: {model.provider}")
