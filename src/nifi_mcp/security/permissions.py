from nifi_mcp.config import settings

_WRITE_TOOLS: frozenset[str] = frozenset({
    "create_process_group",
    "create_processor",
    "update_processor",
    "create_connection",
    "delete_processor",
})

_CONTROL_TOOLS: frozenset[str] = frozenset({
    "start_processor",
    "stop_processor",
    "start_process_group",
    "stop_process_group",
    "purge_queue",
})


def require_permission(tool_name: str) -> None:
    """Raise PermissionError when MCP_MODE=readonly and a write/control tool is invoked.

    Call this at the top of every write and control tool.
    """
    if settings.mcp_mode == "readonly" and (
        tool_name in _WRITE_TOOLS or tool_name in _CONTROL_TOOLS
    ):
        raise PermissionError(
            f"Tool '{tool_name}' requires MCP_MODE=full (current mode: readonly)"
        )
