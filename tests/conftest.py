import os
from unittest.mock import patch

# Set env vars BEFORE any nifi_mcp module is imported at collection time.
# pydantic-settings reads these once when Settings() is instantiated.
os.environ.setdefault("NIFI_URL", "https://localhost:8443")
os.environ.setdefault("NIFI_USERNAME", "test")
os.environ.setdefault("NIFI_PASSWORD", "test")
os.environ.setdefault("MCP_MODE", "full")
os.environ.setdefault("MCP_AUDIT_LOG", "false")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _bypass_ensure_authenticated(request):
    # test_auth.py tests ensure_authenticated directly — don't intercept it there.
    if request.fspath.basename == "test_auth.py":
        yield
    else:
        # Patch at source (covers modules reloaded mid-test via importlib.reload)
        # AND at each tool module's binding (covers already-imported references).
        with patch("nifi_mcp.auth.ensure_authenticated"), \
             patch("nifi_mcp.tools.read.ensure_authenticated"), \
             patch("nifi_mcp.tools.write.ensure_authenticated"), \
             patch("nifi_mcp.tools.control.ensure_authenticated"):
            yield


@pytest.fixture
def nifi_env(monkeypatch):
    """Override env vars for tests that need non-default settings."""
    monkeypatch.setenv("NIFI_URL", "https://localhost:8443")
    monkeypatch.setenv("NIFI_USERNAME", "test")
    monkeypatch.setenv("NIFI_PASSWORD", "test")
    monkeypatch.setenv("MCP_MODE", "full")
    monkeypatch.setenv("MCP_AUDIT_LOG", "false")
