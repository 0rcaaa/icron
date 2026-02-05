"""LLM provider abstraction module."""

from icron.providers.base import LLMProvider, LLMResponse

__all__ = ["LLMProvider", "LLMResponse", "LiteLLMProvider", "LazyLLMProvider"]

# Optional providers: avoid importing hard dependencies at package import time.
try:
    from icron.providers.lazyllm_provider import LazyLLMProvider
except Exception:  # pragma: no cover
    LazyLLMProvider = None

try:
    from icron.providers.litellm_provider import LiteLLMProvider
except Exception:  # pragma: no cover
    LiteLLMProvider = None
