from fastmcp import FastMCP

from nifi_mcp.config import settings

mcp = FastMCP(
    name="nifi-mcp",
    instructions=(
        "MCP server for Apache NiFi 2.2.0. "
        f"Current mode: {settings.mcp_mode}. "
        "Lets AI agents inspect and control NiFi flows in a safe, auditable way."
    ),
)

# Tools register themselves when their module is imported.
from nifi_mcp.tools import control, read, write  # noqa: F401


def main() -> None:
    if settings.mcp_transport == "sse":
        mcp.run(transport="sse", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
