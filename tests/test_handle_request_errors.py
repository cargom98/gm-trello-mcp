"""Unit tests for the handle_request_errors decorator.

Tests each exception type and HTTP status code mapping to verify
the decorator returns the exact error messages from the design spec.
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure TRELLO_API_KEY is set before importing server
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"

import pytest
import requests


def _get_handle_request_errors():
    """Import handle_request_errors from server, patching FastMCP to avoid decorator errors."""
    # If server is already imported (and worked), just grab it
    if "server" in sys.modules:
        return sys.modules["server"].handle_request_errors

    # Patch FastMCP so that tool() returns an identity decorator
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_instance.tool.return_value = lambda fn: fn

    original_fastmcp = None
    try:
        from mcp.server.fastmcp import FastMCP as OrigFastMCP
        original_fastmcp = OrigFastMCP
    except ImportError:
        pass

    with patch("mcp.server.fastmcp.FastMCP", return_value=mock_fastmcp_instance):
        # Remove cached module if a previous import attempt failed
        sys.modules.pop("server", None)
        import server
        return server.handle_request_errors


handle_request_errors = _get_handle_request_errors()


# --- Helper ---

def make_raising_func(exc):
    """Return a decorated async function that raises the given exception."""
    @handle_request_errors
    async def _func():
        raise exc
    return _func


def _make_http_error(status_code):
    """Build a requests.exceptions.HTTPError with a mocked response."""
    response = requests.models.Response()
    response.status_code = status_code
    response._content = b"error body"
    return requests.exceptions.HTTPError(response=response)


# --- HTTPError status-code tests ---

@pytest.mark.asyncio
async def test_http_401():
    result = await make_raising_func(_make_http_error(401))()
    assert result == "Error: Authentication failed. Please check your credentials."


@pytest.mark.asyncio
async def test_http_403():
    result = await make_raising_func(_make_http_error(403))()
    assert result == "Error: Permission denied. You don't have access to this resource."


@pytest.mark.asyncio
async def test_http_404():
    result = await make_raising_func(_make_http_error(404))()
    assert result == "Error: Resource not found. Please check the ID."


@pytest.mark.asyncio
async def test_http_429():
    result = await make_raising_func(_make_http_error(429))()
    assert result == "Error: Rate limit exceeded. Please try again later."


@pytest.mark.asyncio
async def test_http_500_other_status():
    result = await make_raising_func(_make_http_error(500))()
    assert result == "Error: API request failed (status 500)."


# --- Other exception types ---

@pytest.mark.asyncio
async def test_timeout():
    result = await make_raising_func(requests.exceptions.Timeout())()
    assert result == "Error: Request timed out. Please try again."


@pytest.mark.asyncio
async def test_connection_error():
    result = await make_raising_func(requests.exceptions.ConnectionError())()
    assert result == "Error: Cannot connect to Trello API. Please check your network."


@pytest.mark.asyncio
async def test_value_error():
    result = await make_raising_func(ValueError("Invalid ID"))()
    assert result == "Validation Error: Invalid ID"


@pytest.mark.asyncio
async def test_generic_exception():
    result = await make_raising_func(Exception("something"))()
    assert result == "Error: An unexpected error occurred. Please try again."


# --- Positive path ---

@pytest.mark.asyncio
async def test_no_exception_passthrough():
    """When no exception is raised, the return value passes through unchanged."""
    @handle_request_errors
    async def _ok():
        return "all good"

    assert await _ok() == "all good"
