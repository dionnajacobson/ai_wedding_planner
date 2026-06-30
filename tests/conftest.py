"""Shared pytest configuration for test markers."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Label tests without the api marker as non_api."""
    for item in items:
        if "api" not in item.keywords:
            item.add_marker(pytest.mark.non_api)
