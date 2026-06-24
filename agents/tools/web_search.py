"""Web search tool backed by the Tavily API."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolName, ToolResult


class WebSearchInput(BaseModel):
    """Input schema for the web_search tool."""

    query: str = Field(description="Search query for current wedding planning information.")


class WebSearchDefinition(ToolDefinition):
    """Schema exposed to the LLM for the web_search tool."""

    name: ToolName = ToolName.WEB_SEARCH
    description: str = (
        "Search the web for current information about venues, vendors, "
        "pricing, trends, and other wedding planning topics."
    )
    params_model: type[BaseModel] = WebSearchInput


class WebSearchExecutor(ToolExecutor):
    """Search the web for current wedding planning information."""

    def __init__(self, client: AsyncTavilyClient | None = None) -> None:
        """Initialize the executor with an optional Tavily client."""
        self._client = client or AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run a Tavily search for the requested query."""
        search_input = WebSearchInput.model_validate(tool_call.arguments)
        content = await self._search(search_input.query)
        result = ToolResult(tool_call_id=tool_call.id, content=content)
        return result

    async def _search(self, query: str) -> str:
        """Run a Tavily web search and return formatted results."""
        response = await self._client.search(query=query, max_results=5)
        text = self._format_search_results(response)
        return text

    def _format_search_results(self, response: dict[str, Any]) -> str:
        """Format Tavily search results as text for the LLM."""
        lines: list[str] = []

        answer = response.get("answer")
        if answer:
            lines.append(f"Answer: {answer}")

        for result in response.get("results", []):
            title = result.get("title", "Untitled")
            content = result.get("content", "")
            url = result.get("url", "")
            line = f"- {title}: {content}"
            if url:
                line = f"{line} ({url})"
            lines.append(line)

        if not lines:
            text = "No results found."
            return text

        text = "\n".join(lines)
        return text
