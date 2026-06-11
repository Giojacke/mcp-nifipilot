![NiFiPilot Logo](docs/assets/logo.png)

# NiFiPilot — AI Copilot for Apache NiFi

MCP (Model Context Protocol) server for Apache NiFi 2.2.0. Lets AI agents — Claude Code, VS Code Copilot, Cursor, Windsurf — inspect and control NiFi flows safely and auditably via 16 ready-to-use tools.

## Features

- **16 tools** across three categories: read (5), write (5), control (6)
- **Readonly mode** — write and control tools are blocked; safe for production read access
- **Dry-run mode** — preview write/control actions without executing them
- **Structured audit log** — every tool call is written to a JSON log file
- **Rate limiting** — configurable call budget per minute
- **Transports** — stdio (local clients) and SSE (Docker/remote)

---

## Quick start with Docker Compose

The bundled compose file starts NiFi 2.2.0 and the MCP server together.

```bash
# 1. Copy and edit the env file
cp .env.example .env
# Edit NIFI_PASSWORD and set MCP_MODE=full to allow write/control

# 2. Start both services
docker compose up --build

# 3. NiFi UI: https://localhost:8443  (first start takes ~2 min)
#    MCP SSE:  http://localhost:8000
```

Connect Cursor or Claude Code to the SSE endpoint:

```json
{
  "mcpServers": {
    "nifi-mcp": { "url": "http://localhost:8000/sse" }
  }
}
```

---

## Manual installation

**Requirements:** Python 3.11+

```bash
pip install nifi-mcp
```

Or from source:

```bash
git clone https://github.com/Giojacke/mcp-apache-nifi
cd mcp-apache-nifi
pip install .
```

Run in stdio mode (used by Claude Code, VS Code, Cursor):

```bash
NIFI_URL=https://localhost:8443 \
NIFI_USERNAME=admin \
NIFI_PASSWORD=your-password \
NIFI_VERIFY_SSL=false \
MCP_MODE=readonly \
nifi-mcp
```

---

## Configuration

All settings come from environment variables (or a `.env` file in the working directory).

| Variable             | Default                | Description                                      |
|----------------------|------------------------|--------------------------------------------------|
| `NIFI_URL`           | `https://localhost:8443` | NiFi base URL                                  |
| `NIFI_USERNAME`      | `admin`                | NiFi username                                    |
| `NIFI_PASSWORD`      | _(required)_           | NiFi password                                    |
| `NIFI_VERIFY_SSL`    | `false`                | Verify TLS certificate (`true` in production)    |
| `MCP_MODE`           | `readonly`             | `readonly` — read tools only; `full` — all tools |
| `MCP_AUDIT_LOG`      | `true`                 | Write JSON audit log                             |
| `MCP_AUDIT_LOG_PATH` | `./logs/audit.log`     | Path for the audit log file                      |
| `MCP_RATE_LIMIT`     | `60`                   | Max tool calls per minute                        |
| `MCP_DRY_RUN`        | `false`                | Describe write/control actions without executing |
| `MCP_TRANSPORT`      | `stdio`                | `stdio` for local clients; `sse` for Docker      |
| `MCP_HOST`           | `0.0.0.0`              | Bind host when `MCP_TRANSPORT=sse`               |
| `MCP_PORT`           | `8000`                 | Port when `MCP_TRANSPORT=sse`                    |

---

## Tool reference

### Read tools _(always available)_

| Tool | Description |
|------|-------------|
| `get_process_groups(group_id)` | List direct child process groups |
| `get_processors(group_id)` | List processors in a group |
| `get_connections(group_id)` | List connections in a group |
| `get_flow_status(group_id)` | Running/stopped/invalid counts and throughput |
| `get_system_diagnostics()` | NiFi version, heap, CPU, uptime |

### Write tools _(require `MCP_MODE=full`)_

| Tool | Description |
|------|-------------|
| `create_process_group(name, parent_group_id, x, y)` | Create a new process group |
| `create_processor(name, processor_type, group_id, x, y)` | Add a processor (`processor_type` = full Java class name) |
| `update_processor(processor_id, name?, properties?, scheduling_period?)` | Update processor config |
| `create_connection(source_id, destination_id, group_id, relationships?, ...)` | Connect two components |
| `delete_processor(processor_id)` | Delete a stopped processor |

### Control tools _(require `MCP_MODE=full`)_

| Tool | Description |
|------|-------------|
| `start_processor(processor_id)` | Start a processor |
| `stop_processor(processor_id)` | Stop a processor |
| `start_process_group(group_id)` | Start all processors in a group |
| `stop_process_group(group_id)` | Stop all processors in a group |
| `get_queue_status(connection_id)` | Queue depth and throughput for a connection |
| `purge_queue(connection_id)` | Drop all flowfiles from a queue |

---

## Client setup

### Claude Code

Copy `.mcp.json` to your project root (already included) and fill in your password:

```jsonc
// .mcp.json
{
  "mcpServers": {
    "nifi-mcp": {
      "command": "nifi-mcp",
      "env": {
        "NIFI_URL": "https://localhost:8443",
        "NIFI_USERNAME": "admin",
        "NIFI_PASSWORD": "YOUR_PASSWORD",
        "NIFI_VERIFY_SSL": "false",
        "MCP_MODE": "readonly"
      }
    }
  }
}
```

### VS Code

Copy `.vscode/mcp.json` (already included) and fill in your password. The file uses the VS Code MCP server format.

### Cursor / Windsurf

Use the same format as Claude Code. Place it at `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project).

### SSE mode (Docker or remote server)

```jsonc
{
  "mcpServers": {
    "nifi-mcp": { "url": "http://localhost:8000/sse" }
  }
}
```

---

## Security model

| Concern | Mitigation |
|---------|-----------|
| Credential exposure | All secrets come from env vars — never hardcoded |
| Accidental writes | `MCP_MODE=readonly` blocks all write and control tools |
| Runaway changes | `MCP_DRY_RUN=true` describes actions without executing |
| Auditability | Every tool call writes a JSON entry to the audit log |
| Rate limiting | `MCP_RATE_LIMIT` caps calls per minute |
| SSL in production | Set `NIFI_VERIFY_SSL=true` with a valid certificate |

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"        # if using pip
# or
uv sync --all-groups           # if using uv

# Run tests
pytest

# Lint and format
ruff check src tests
ruff format src tests
```

Tests mock nipyapi at the API class level — no live NiFi required. Integration tests against a real NiFi instance can be added in `tests/integration/` (excluded from the default test run).

---

## License

MIT
