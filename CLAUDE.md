# NiFi MCP Server — Contexto del Proyecto

## Qué es esto
MCP (Model Context Protocol) server en Python para interactuar con Apache NiFi 2.2.0
via REST API. Permite que agentes de IA (Claude Code, VS Code, Cursor/Windsurf) puedan
ver, crear, modificar y controlar flujos de NiFi de forma segura y auditable.

Proyecto open source, construido con buenas prácticas de seguridad desde el día uno.
Repositorio: github.com/Giojacke/mcp-apache-nifi  ← actualizar cuando esté creado

---

## Stack tecnológico
- Python 3.11+
- fastmcp — framework MCP server (transporte stdio y SSE)
- nipyapi — cliente Python para NiFi REST API
- httpx — llamadas HTTP directas cuando nipyapi no alcance
- pydantic — validación de parámetros de cada tool
- pytest — testing unitario e integración
- ruff — linting y formato de código

---

## Arquitectura de carpetas

```
mcp_apache_nifi/
├── CLAUDE.md                  ← este archivo, contexto permanente
├── ARCHITECTURE.md            ← decisiones de diseño y ADRs
├── README.md                  ← documentación pública
├── .env.example               ← plantilla de variables de entorno
├── .gitignore                 ← incluye .env, logs/, __pycache__
├── pyproject.toml             ← dependencias y metadata del proyecto
├── docker-compose.yml         ← orquestación NiFi + MCP server
├── Dockerfile                 ← imagen del MCP server (python:3.11-slim)
├── src/
│   └── nifi_mcp/
│       ├── __init__.py
│       ├── server.py          ← entry point, registra todas las tools
│       ├── config.py          ← lee env vars, nunca valores hardcoded
│       ├── auth.py            ← autenticación JWT con NiFi
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── read.py        ← tools de solo lectura (ver flujos, diagnosticar)
│       │   ├── write.py       ← tools de escritura (crear/modificar procesadores)
│       │   └── control.py     ← tools de control (start/stop, monitoreo de colas)
│       ├── security/
│       │   ├── __init__.py
│       │   ├── audit.py       ← log de cada tool call (quién, qué, cuándo, resultado)
│       │   └── permissions.py ← permisos granulares por tool según MCP_MODE
│       └── client/
│           ├── __init__.py
│           └── nifi_client.py ← wrapper del REST client (nipyapi + httpx)
└── tests/
    ├── conftest.py            ← fixtures compartidos, mock de NiFi
    ├── test_read.py
    ├── test_write.py
    ├── test_control.py
    ├── test_auth.py
    └── test_permissions.py
```

---

## Variables de entorno (config.py las lee todas)

| Variable           | Descripción                                 | Ejemplo                        |
|--------------------|---------------------------------------------|--------------------------------|
| NIFI_URL           | URL base de NiFi                            | https://localhost:8443         |
| NIFI_USERNAME      | Usuario de NiFi                             | admin                          |
| NIFI_PASSWORD      | Contraseña de NiFi                          | ****                           |
| NIFI_VERIFY_SSL    | Verificar certificado SSL                   | false (local), true (prod)     |
| MCP_MODE           | Nivel de acceso permitido                   | readonly / full                |
| MCP_AUDIT_LOG      | Habilitar audit log                         | true                           |
| MCP_AUDIT_LOG_PATH | Ruta del archivo de audit log               | ./logs/audit.log               |
| MCP_RATE_LIMIT     | Máximo de llamadas por minuto               | 60                             |
| MCP_DRY_RUN        | Simular sin ejecutar (write/control)        | false                          |

---

## Reglas de desarrollo — SIEMPRE respetar

1. **Credenciales NUNCA hardcoded** — solo desde env vars via config.py
2. **Cada tool tiene docstring obligatorio** con: qué hace, endpoint que toca, permisos requeridos
3. **Audit log en cada tool call** — toda acción queda registrada en audit.py
4. **Modo readonly** — si MCP_MODE=readonly, las tools de write y control lanzan PermissionError
5. **Dry run** — si MCP_DRY_RUN=true, write y control describen qué harían sin ejecutar
6. **Tests antes de merge** — cada tool nueva debe tener su test en tests/
7. **Un archivo, una responsabilidad** — no mezclar lógica de tools con lógica de cliente REST
8. **Pydantic para inputs** — todos los parámetros de tools validados con modelos Pydantic
9. **Manejo explícito de errores** — nunca silenciar excepciones, siempre loguear y relanzar
10. **Sin dependencias innecesarias** — antes de agregar una librería, justificarla en ARCHITECTURE.md

---

## Orden de implementación (roadmap)

### Fase 1 — Base (empezar aquí)
- [ ] pyproject.toml con dependencias base
- [ ] config.py — lector de env vars con validación Pydantic
- [ ] nifi_client.py — wrapper básico (ping, autenticación JWT)
- [ ] auth.py — login y refresh de token
- [ ] audit.py — logger estructurado de tool calls
- [ ] permissions.py — guard por MCP_MODE
- [ ] server.py — entry point vacío que arranca fastmcp

### Fase 2 — Tools de lectura
- [ ] get_process_groups — listar grupos de procesos
- [ ] get_processors — listar procesadores de un grupo
- [ ] get_connections — listar conexiones
- [ ] get_flow_status — estado general del flujo
- [ ] get_system_diagnostics — salud del sistema NiFi

### Fase 3 — Tools de escritura
- [ ] create_process_group — crear grupo nuevo
- [ ] create_processor — agregar procesador
- [ ] update_processor — modificar propiedades
- [ ] create_connection — conectar dos procesadores
- [ ] delete_processor — eliminar procesador (con confirmación)

### Fase 4 — Tools de control
- [ ] start_processor / stop_processor
- [ ] start_process_group / stop_process_group
- [ ] get_queue_status — estado de colas
- [ ] purge_queue — vaciar cola (con confirmación)

### Fase 5 — Empaquetado
- [ ] Dockerfile + docker-compose.yml
- [ ] README.md completo
- [ ] .env.example documentado
- [ ] Configuración para Claude Code, VS Code y Cursor

---

## Cómo iniciar una sesión de trabajo con Claude

Siempre comenzar con:
> "Lee el CLAUDE.md y el árbol de carpetas actual. Dime en qué fase estamos
>  y qué sigue según el roadmap antes de que te pida algo."

---

## Progreso
<!-- Claude actualiza esta sección al final de cada sesión -->
- Sesión 1 (inicio): estructura definida, CLAUDE.md creado, pendiente scaffold inicial.
- Sesión 2: **Fase 1 completa.** Scaffold creado: pyproject.toml, config.py, auth.py, server.py, nifi_client.py, audit.py, permissions.py, placeholders de tools (read/write/control) y tests.
- Sesión 3: **Fase 2 completa.** 5 tools de lectura implementadas (get_process_groups, get_processors, get_connections, get_flow_status, get_system_diagnostics) con audit log y helper `_attr`. 9 tests con mocks.
- Sesión 4: **Fase 3 completa.** `_attr` movido a `tools/_utils.py`. 5 tools de escritura (create_process_group, create_processor, update_processor, create_connection, delete_processor) con dry_run, require_permission y audit. 9 tests con mocks.
- Sesión 5: **Fase 4 completa.** 6 tools de control (start/stop_processor, start/stop_process_group, get_queue_status, purge_queue). purge_queue hace polling hasta que NiFi confirma el drop (max 30 s). 8 tests con mocks.
- Sesión 6: **Fase 5 completa. Proyecto listo para usar.** Dockerfile, docker-compose.yml (NiFi 2.2.0 + MCP), README.md, .mcp.json (Claude Code), .vscode/mcp.json (VS Code). config.py y server.py actualizados para soportar MCP_TRANSPORT=sse. 16 tools registradas en total.
- Sesión 7: **Deuda técnica resuelta. 33/33 tests passing.** Logging estructurado en nifi_client.py (eliminados prints DEBUG). Lazy auth via decorador `@_with_auth` en NiFiClient y `ensure_authenticated()` como primera línea en las 16 tools (read/write/control). `auth.py` loguea errores no-401 antes de relanzar. ARCHITECTURE.md creado con decisiones de diseño (opción B vs A, lazy auth, roadmap NiFiClient como fachada). 5 tests nuevos para `auth.py`. Bugs pre-existentes corregidos: typo `FlowfileQueuesApi`→`FlowFileQueuesApi` (producción + tests), campos planos faltantes en `ConnectionEntity`, contaminación de estado por `importlib.reload` en tests. Fixture `_bypass_ensure_authenticated` en conftest.py evita conexiones reales en todos los tests de tools.
