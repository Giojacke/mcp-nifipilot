# Architecture decisions

## Auth: per-tool ensure_authenticated (Option B)

Each tool calls `ensure_authenticated()` as its first line instead of routing
all calls through `NiFiClient` methods (Option A).

**Why B over A:** At this stage, the tools call nipyapi directly and `NiFiClient`
is not yet a real façade. Refactoring all tools to go through the client would
require touching every tool file plus the client, with no safety net of integration
tests against a live NiFi. Option B adds auth protection in one small, auditable
change per file, keeps the blast radius small, and leaves the architecture free to
evolve without a forced big-bang refactor.

**Trade-off accepted:** `ensure_authenticated()` is duplicated in every tool rather
than being enforced in one place. This is conscious technical debt — see roadmap below.

---

## Auth: lazy (first real call) instead of __init__

`NiFiClient.__init__` does not call `login()`. Auth happens on the first tool
invocation via `ensure_authenticated()`.

**Why:** The MCP server starts before NiFi is ready (especially in Docker Compose).
Calling `login()` at import/startup would fail and prevent the server from starting
at all, even though NiFi will be reachable seconds later.

---

## Roadmap: NiFiClient as real façade

The current split (tools → nipyapi directly, `NiFiClient` unused by tools) is
intentional for now. The planned refactor, when integration tests exist, is:

1. Move each nipyapi call into a typed method on `NiFiClient`.
2. Decorate those methods with `@_with_auth` (already in place).
3. Tools call `client.<method>()` — auth, logging, and error handling live in one place.
4. Remove the per-tool `ensure_authenticated()` calls.

Until that refactor happens, Option B provides equivalent protection without the risk.
