"""Typed errors for LLM client and provider adapters."""


class LLMError(Exception):
    """Base error for LLM client failures."""


class LLMAuthError(LLMError):
    """Authentication or authorization failed for the provider API."""


class LLMRateLimitError(LLMError):
    """Provider rate limit exceeded."""


class LLMProviderError(LLMError):
    """Generic provider API error."""


def map_openai_error(exc: Exception) -> LLMError:
    """Map OpenAI SDK exceptions to normalized LLM errors."""
    from openai import APIStatusError, AuthenticationError, RateLimitError

    if isinstance(exc, AuthenticationError):
        error = LLMAuthError(str(exc))
        return error
    if isinstance(exc, RateLimitError):
        error = LLMRateLimitError(str(exc))
        return error
    if isinstance(exc, APIStatusError):
        error = LLMProviderError(str(exc))
        return error
    error = LLMProviderError(str(exc))
    return error


def map_anthropic_error(exc: Exception) -> LLMError:
    """Map Anthropic SDK exceptions to normalized LLM errors."""
    from anthropic import APIStatusError, AuthenticationError, RateLimitError

    if isinstance(exc, AuthenticationError):
        error = LLMAuthError(str(exc))
        return error
    if isinstance(exc, RateLimitError):
        error = LLMRateLimitError(str(exc))
        return error
    if isinstance(exc, APIStatusError):
        error = LLMProviderError(str(exc))
        return error
    error = LLMProviderError(str(exc))
    return error
