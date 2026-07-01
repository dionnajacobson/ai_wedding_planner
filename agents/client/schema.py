"""JSON schema helpers for LLM provider adapters."""

from __future__ import annotations

from typing import Any


class OpenAIFunctionSchema:
    """Prepare external JSON schemas for OpenAI function tool parameters."""

    _COMBINATORS = ("allOf", "anyOf", "oneOf")

    def __init__(self, schema: dict[str, Any]) -> None:
        """Initialize with a raw JSON schema."""
        self._schema = dict(schema)

    def normalize(self) -> dict[str, Any]:
        """Return an OpenAI-compatible copy of the schema."""
        return self._normalize_node(self._schema)

    def _normalize_node(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Recursively enforce OpenAI-compatible object schema constraints."""
        normalized = dict(schema)
        schema_type = normalized.get("type")

        if schema_type == "object" or "properties" in normalized:
            normalized["type"] = "object"
            normalized["additionalProperties"] = False
            properties = normalized.get("properties")
            if isinstance(properties, dict):
                normalized["properties"] = {
                    key: self._normalize_node(value) if isinstance(value, dict) else value
                    for key, value in properties.items()
                }

        if schema_type == "array":
            items = normalized.get("items")
            if isinstance(items, dict):
                normalized["items"] = self._normalize_node(items)

        for combinator in self._COMBINATORS:
            variants = normalized.get(combinator)
            if isinstance(variants, list):
                normalized[combinator] = [
                    self._normalize_node(variant) if isinstance(variant, dict) else variant
                    for variant in variants
                ]

        return normalized
