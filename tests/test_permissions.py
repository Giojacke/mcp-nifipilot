import pytest

from nifi_mcp.security.permissions import _CONTROL_TOOLS, _WRITE_TOOLS, require_permission


def test_readonly_blocks_write_tool(monkeypatch):
    monkeypatch.setenv("MCP_MODE", "readonly")
    # Re-import settings to pick up the new env var.
    import importlib
    import nifi_mcp.config as cfg
    importlib.reload(cfg)
    import nifi_mcp.security.permissions as perms
    importlib.reload(perms)

    with pytest.raises(PermissionError, match="readonly"):
        perms.require_permission("create_processor")


def test_readonly_blocks_control_tool(monkeypatch):
    monkeypatch.setenv("MCP_MODE", "readonly")
    import importlib
    import nifi_mcp.config as cfg
    importlib.reload(cfg)
    import nifi_mcp.security.permissions as perms
    importlib.reload(perms)

    with pytest.raises(PermissionError):
        perms.require_permission("start_processor")


def test_full_mode_allows_write_tool(monkeypatch):
    monkeypatch.setenv("MCP_MODE", "full")
    import importlib
    import nifi_mcp.config as cfg
    importlib.reload(cfg)
    import nifi_mcp.security.permissions as perms
    importlib.reload(perms)

    perms.require_permission("create_processor")  # must not raise


def test_read_tool_always_allowed():
    require_permission("get_process_groups")  # must not raise


def test_write_tools_set_is_not_empty():
    assert len(_WRITE_TOOLS) > 0


def test_control_tools_set_is_not_empty():
    assert len(_CONTROL_TOOLS) > 0
