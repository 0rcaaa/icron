"""MCP (Model Context Protocol) client integration for icron.

This module enables icron to connect to MCP servers and use their tools.
MCP is an open protocol for connecting AI assistants to external data sources and tools.

Example:
    from icron.mcp import MCPClient

    client = MCPClient()
    await client.connect_to_server("filesystem", "/path/to/server.py")
    tools = await client.get_all_tools()
"""

try:
    from icron.mcp.client import MCPClient
    from icron.mcp.tool_adapter import MCPToolAdapter
    __all__ = ["MCPClient", "MCPToolAdapter"]
except ImportError as e:
    # MCP not installed
    import warnings
    warnings.warn(
        "MCP support not available. Install with: pip install icron-ai[mcp]",
        ImportWarning,
        stacklevel=2
    )
    MCPClient = None  # type: ignore
    MCPToolAdapter = None  # type: ignore
    __all__ = []
