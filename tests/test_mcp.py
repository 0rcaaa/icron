"""Tests for MCP client and tool adapter."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPClient:
    """Tests for MCPClient class."""

    def test_init(self):
        """Test MCPClient initialization."""
        from icron.mcp.client import MCPClient

        client = MCPClient()
        assert client.connections == {}
        assert client._transports == {}
        assert client._closed is False

    def test_get_all_tools_empty(self):
        """Test get_all_tools with no connections."""
        from icron.mcp.client import MCPClient

        client = MCPClient()
        tools = client.get_all_tools()
        assert tools == []

    def test_get_server_status_empty(self):
        """Test get_server_status with no connections."""
        from icron.mcp.client import MCPClient

        client = MCPClient()
        status = client.get_server_status()
        assert status == []

    def test_get_server_status_with_connections(self):
        """Test get_server_status with mock connections."""
        from icron.mcp.client import MCPClient, MCPServerConnection

        client = MCPClient()

        # Create mock connection
        mock_session = MagicMock()
        mock_tools = [
            {"name": "tool1", "description": "Test tool 1", "input_schema": {}},
            {"name": "tool2", "description": "Test tool 2", "input_schema": {}},
        ]
        conn = MCPServerConnection("test-server", mock_session, mock_tools)
        client.connections["test-server"] = conn

        status = client.get_server_status()
        assert len(status) == 1
        assert status[0]["name"] == "test-server"
        assert status[0]["status"] == "connected"
        assert status[0]["toolCount"] == 2
        assert status[0]["tools"] == ["tool1", "tool2"]


class TestMCPManager:
    """Tests for MCPManager class."""

    def test_init(self):
        """Test MCPManager initialization."""
        from icron.mcp.tool_adapter import MCPManager

        manager = MCPManager()
        assert manager._initialized is False
        assert manager._tools == []

    def test_get_tools_empty(self):
        """Test get_tools with no initialization."""
        from icron.mcp.tool_adapter import MCPManager

        manager = MCPManager()
        tools = manager.get_tools()
        assert tools == []

    def test_get_tool_not_found(self):
        """Test get_tool when tool doesn't exist."""
        from icron.mcp.tool_adapter import MCPManager

        manager = MCPManager()
        tool = manager.get_tool("nonexistent")
        assert tool is None

    def test_get_status_not_initialized(self):
        """Test get_status when not initialized."""
        from icron.mcp.tool_adapter import MCPManager

        manager = MCPManager()
        status = manager.get_status()
        assert status["initialized"] is False
        assert status["totalTools"] == 0
        assert status["servers"] == []

    def test_get_status_initialized(self):
        """Test get_status after initialization."""
        from icron.mcp.tool_adapter import MCPManager

        manager = MCPManager()
        manager._initialized = True

        # Mock the client
        manager._client = MagicMock()
        manager._client.get_server_status.return_value = [
            {"name": "test", "status": "connected", "toolCount": 3, "tools": ["a", "b", "c"]}
        ]

        # Add mock tools
        manager._tools = [MagicMock(), MagicMock(), MagicMock()]

        status = manager.get_status()
        assert status["initialized"] is True
        assert status["totalTools"] == 3
        assert len(status["servers"]) == 1


class TestMCPSecurity:
    """Tests for MCP security validation."""

    def test_validate_command_safe(self):
        """Test validation of safe commands."""
        from icron.mcp.security import validate_command

        # Test safe commands
        is_valid, error = validate_command("python", ["script.py"])
        assert is_valid is True

        is_valid, error = validate_command("npx", ["-y", "@mcp/server"])
        assert is_valid is True

        is_valid, error = validate_command("node", ["server.js"])
        assert is_valid is True

    def test_validate_command_unsafe(self):
        """Test validation of unsafe commands."""
        from icron.mcp.security import validate_command

        # Test unsafe command
        is_valid, error = validate_command("rm", ["-rf", "/"])
        assert is_valid is False
        assert "not in whitelist" in error.lower()

    def test_validate_sse_url_valid(self):
        """Test validation of valid SSE URLs."""
        from icron.mcp.security import validate_sse_url

        is_valid, error = validate_sse_url("https://mcp.example.com/sse")
        assert is_valid is True

        is_valid, error = validate_sse_url("https://api.anthropic.com/mcp")
        assert is_valid is True

    def test_validate_sse_url_invalid(self):
        """Test validation of invalid SSE URLs."""
        from icron.mcp.security import validate_sse_url

        # File URL should be rejected
        is_valid, error = validate_sse_url("file:///etc/passwd")
        assert is_valid is False

        # Invalid URL
        is_valid, error = validate_sse_url("not-a-url")
        assert is_valid is False

        # Localhost blocked (SSRF protection)
        is_valid, error = validate_sse_url("http://localhost:8000/sse")
        assert is_valid is False
        assert "localhost" in error.lower()


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter class."""

    def test_adapter_name_prefix(self):
        """Test that adapter adds mcp_ prefix to tool names."""
        from icron.mcp.tool_adapter import MCPToolAdapter

        mock_client = MagicMock()
        tool_def = {
            "name": "test_tool",
            "full_name": "server:test_tool",
            "description": "A test tool",
            "input_schema": {"type": "object", "properties": {}},
        }

        adapter = MCPToolAdapter(mock_client, "server:test_tool", tool_def)
        assert adapter.name == "mcp_server_test_tool"

    def test_adapter_description(self):
        """Test that adapter includes server prefix in description."""
        from icron.mcp.tool_adapter import MCPToolAdapter

        mock_client = MagicMock()
        tool_def = {
            "name": "test_tool",
            "full_name": "server:test_tool",
            "description": "[server] A test tool",
            "input_schema": {"type": "object", "properties": {}},
        }

        adapter = MCPToolAdapter(mock_client, "server:test_tool", tool_def)
        assert "[server]" in adapter.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
