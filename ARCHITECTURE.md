# Architecture — NiFiPilot

## C4 diagrams

### C1 — System context

```mermaid
graph TD
    Dev["Developer / AI Agent<br/>(Claude Code, VS Code, Cursor)"]
    MCP["NiFiPilot MCP Server<br/>Python · FastMCP · 17 tools<br/>SSE :8000 / stdio"]
    NiFi["Apache NiFi 2.2.0<br/>localhost:8443<br/>JWT auth · TLS"]
    Audit["Audit Log<br/>logs/audit.log<br/>JSON lines"]
    Docker["Docker<br/>nifi-mcp-net"]

    Dev -->|"MCP stdio / SSE"| MCP
    MCP -->|"HTTPS REST API"| NiFi
    MCP -->|"writes"| Audit
    Docker -.->|"hosts"| MCP
    Docker -.->|"hosts"| NiFi
```

### C2 — Containers (docker-compose stack)

```mermaid
graph TD
    subgraph docker["docker-compose · nifi-mcp-net"]
        subgraph mcp_container["nifi-mcp container (:8000)"]
            server["server.py — FastMCP entry"]
            tools["tools/ — 17 MCP tools"]
            security["security/ — auth · audit"]
            client_mod["client/ — nipyapi wrapper"]
            config["config.py — env vars"]
        end
        subgraph nifi_container["nifi container (:8443)"]
            nifi_app["apache/nifi:2.2.0<br/>single-user auth · HTTPS"]
        end
    end

    mcp_container -->|"HTTPS"| nifi_container
    mcp_container -->|"writes"| audit_log["audit.log"]
```

### C3 — Components (nifi-mcp internals)

```mermaid
graph TD
    server_py["server.py"]
    read["tools/read.py<br/>5 tools"]
    write["tools/write.py<br/>6 tools"]
    control["tools/control.py<br/>6 tools"]
    auth["security/auth.py<br/>login + ensure_authenticated"]
    perms["security/permissions.py<br/>require_permission"]
    audit_mod["security/audit.py<br/>log_call"]
    nifi_client["client/nifi_client.py<br/>NiFiClient singleton<br/>configures nipyapi host"]
    config_py["config.py<br/>pydantic-settings<br/>env vars &gt; .env"]
    nipyapi["nipyapi<br/>NiFi REST client"]

    server_py -->|"imports"| read
    server_py -->|"imports"| write
    server_py -->|"imports"| control
    server_py -->|"imports"| nifi_client

    read -->|"ensure_authenticated()"| auth
    write -->|"ensure_authenticated()"| auth
    control -->|"ensure_authenticated()"| auth

    write -->|"require_permission()"| perms
    control -->|"require_permission()"| perms

    read -->|"log_call()"| audit_mod
    write -->|"log_call()"| audit_mod
    control -->|"log_call()"| audit_mod

    auth -->|"nipyapi.security"| nipyapi
    read -->|"nipyapi.nifi.*Api()"| nipyapi
    write -->|"nipyapi.nifi.*Api()"| nipyapi
    control -->|"nipyapi.nifi.*Api()"| nipyapi
    nifi_client -->|"sets host + SSL"| nipyapi

    config_py -.->|"settings"| server_py
    config_py -.->|"settings"| auth
    config_py -.->|"settings"| nifi_client
    config_py -.->|"settings"| perms
    config_py -.->|"settings"| audit_mod
```

---

## Design decisions

### ADR-001 — Auth: per-tool ensure_authenticated (Option B over Option A)

**Context:** Tools call nipyapi directly. NiFiClient exists but is not yet the façade.

**Decision:** Each tool calls `ensure_authenticated()` as its first line instead of routing all calls through `NiFiClient` methods.

**Why B over A:** Refactoring all tools to go through the client would require touching every tool file plus the client, with no safety net of integration tests against a live NiFi. Option B adds auth protection in one small, auditable change per file, keeps the blast radius small, and leaves the architecture free to evolve.

**Trade-off accepted:** `ensure_authenticated()` is duplicated in every tool rather than enforced in one place. This is conscious technical debt — see ADR-003.

---

### ADR-002 — Lazy auth (first real call, not startup)

**Context:** The MCP server starts before NiFi is ready, especially in Docker Compose where `depends_on` with healthcheck means NiFi may still be initializing when the MCP container boots.

**Decision:** `NiFiClient.__init__` does not call `login()`. Auth happens on the first tool invocation via `ensure_authenticated()`.

**Why:** Calling `login()` at import/startup would fail and prevent the server from starting at all, even though NiFi would be reachable seconds later. Lazy auth makes the server resilient to NiFi startup order.

---

### ADR-003 — NiFiClient as real façade (planned refactor)

**Current state:** Tools call nipyapi directly. `NiFiClient` configures the nipyapi host at startup (via the import in `server.py`) but is not used by tools for actual API calls.

**Planned refactor** (when integration tests exist):

1. Move each nipyapi call into a typed method on `NiFiClient`.
2. Decorate those methods with `@_with_auth` (already in place).
3. Tools call `client.<method>()` — auth, logging, and error handling in one place.
4. Remove per-tool `ensure_authenticated()` calls.

Until that refactor happens, Option B (ADR-001) provides equivalent protection.

---

### ADR-004 — nipyapi host initialization via server.py import

**Problem discovered:** nipyapi has `https://localhost:9443` as its internal default host. If `NiFiClient` is not instantiated before a tool call, nipyapi uses that default and all calls fail.

**Solution:** `server.py` imports `client` from `nifi_client.py` at startup. This triggers `NiFiClient.__init__`, which overwrites the nipyapi host with the value from `NIFI_URL`. Import order guarantees this runs before any tool is called.

**Why not in config.py or auth.py:** Those modules don't know about nipyapi. The responsibility belongs to the client layer.

---

### ADR-005 — Healthcheck uses HTTP status codes 200 and 401

**Context:** NiFi 2.x requires authentication for `/nifi-api/system-diagnostics`. The curl-based healthcheck in docker-compose was failing because `-f` (fail on error) treats 401 as failure.

**Decision:** The healthcheck accepts both 200 and 401 as signals that NiFi is alive and responding.

```yaml
test: ["CMD-SHELL", "curl -sk -o /dev/null -w '%{http_code}' https://nifi:8443/nifi-api/system-diagnostics | grep -qE '(200|401)' || exit 1"]
```

**Why:** A 401 means NiFi is up and enforcing auth — that's healthy. The MCP server authenticates separately via JWT, not via the healthcheck endpoint.

---

## Known technical debt

| Item | Priority | Notes |
|------|----------|-------|
| Rate limiting not enforced | Medium | `MCP_RATE_LIMIT` config exists but no middleware applies it |
| `NiFiClient` not used by tools | Medium | See ADR-003 — planned refactor when integration tests exist |
| No integration tests | Medium | Tests mock nipyapi; no tests against live NiFi |
| `test_auth.py` covers auth module only | Low | Tool-level auth path not covered by tests |

---

## Stack

| Layer | Technology |
|-------|-----------|
| MCP framework | fastmcp 3.4.2 |
| NiFi client | nipyapi 1.5.1 + httpx |
| Config | pydantic-settings |
| Tests | pytest + unittest.mock |
| Lint | ruff |
| Packaging | hatchling |
| Runtime | Python 3.11 · Docker · docker-compose |
