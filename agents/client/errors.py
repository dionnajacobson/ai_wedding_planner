"""Typed errors for LLM client and provider adapters."""

from anthropic import APIStatusError as AnthropicAPIStatusError
from anthropic import AuthenticationError as AnthropicAuthenticationError
from anthropic import RateLimitError as AnthropicRateLimitError
from openai import APIStatusError as OpenAIAPIStatusError
from openai import AuthenticationError as OpenAIAuthenticationError
from openai import RateLimitError as OpenAIRateLimitError


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
    if isinstance(exc, OpenAIAuthenticationError):
        error = LLMAuthError(str(exc))
        return error
    if isinstance(exc, OpenAIRateLimitError):
        error = LLMRateLimitError(str(exc))
        return error
    if isinstance(exc, OpenAIAPIStatusError):
        error = LLMProviderError(str(exc))
        return error
    error = LLMProviderError(str(exc))
    return error


def map_anthropic_error(exc: Exception) -> LLMError:
    """Map Anthropic SDK exceptions to normalized LLM errors."""
    if isinstance(exc, AnthropicAuthenticationError):
        error = LLMAuthError(str(exc))
        return error
    if isinstance(exc, AnthropicRateLimitError):
        error = LLMRateLimitError(str(exc))
        return error
    if isinstance(exc, AnthropicAPIStatusError):
        error = LLMProviderError(str(exc))
        return error
    error = LLMProviderError(str(exc))
    return error
