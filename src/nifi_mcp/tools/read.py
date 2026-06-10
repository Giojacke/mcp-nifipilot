from __future__ import annotations

import logging
import nipyapi.nifi

from nifi_mcp.auth import ensure_authenticated
from nifi_mcp.security import audit
from nifi_mcp.server import mcp
from nifi_mcp.tools._utils import _attr

logger = logging.getLogger(__name__)


@mcp.tool()
def get_process_groups(group_id: str = "root") -> dict:
    """List direct child process groups of group_id.

    Endpoint: GET /nifi-api/process-groups/{id}/process-groups
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.ProcessGroupsApi().get_process_groups(id=group_id)
        groups = []
        for g in result.process_groups or []:
            snap = _attr(g, "status", "aggregate_snapshot")
            groups.append({
                "id": g.id,
                "name": _attr(g, "component", "name"),
                "running_count": _attr(snap, "running_count", default=0),
                "stopped_count": _attr(snap, "stopped_count", default=0),
                "invalid_count": _attr(snap, "invalid_count", default=0),
            })
        audit.log_call("get_process_groups", {"group_id": group_id}, f"{len(groups)} groups")
        return {"group_id": group_id, "process_groups": groups}
    except Exception:
        logger.error("get_process_groups failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def get_processors(group_id: str = "root") -> dict:
    """List all processors in group_id (direct children only).

    Endpoint: GET /nifi-api/process-groups/{id}/processors
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.ProcessGroupsApi().get_processors(id=group_id)
        processors = []
        for p in result.processors or []:
            processors.append({
                "id": p.id,
                "name": _attr(p, "component", "name"),
                "type": _attr(p, "component", "type"),
                "state": _attr(p, "component", "state"),
                "run_status": _attr(p, "status", "run_status"),
                "active_thread_count": _attr(
                    p, "status", "aggregate_snapshot", "active_thread_count", default=0
                ),
            })
        audit.log_call("get_processors", {"group_id": group_id}, f"{len(processors)} processors")
        return {"group_id": group_id, "processors": processors}
    except Exception:
        logger.error("get_processors failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def get_connections(group_id: str = "root") -> dict:
    """List all connections in group_id.

    Endpoint: GET /nifi-api/process-groups/{id}/connections
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.ProcessGroupsApi().get_connections(id=group_id)
        connections = []
        for c in result.connections or []:
            connections.append({
                "id": c.id,
                "name": _attr(c, "component", "name"),
                "source_id": _attr(c, "component", "source", "id"),
                "source_name": _attr(c, "component", "source", "name"),
                "destination_id": _attr(c, "component", "destination", "id"),
                "destination_name": _attr(c, "component", "destination", "name"),
                "queued_count": _attr(
                    c, "status", "aggregate_snapshot", "queued_count", default="0"
                ),
                "queued_size": _attr(
                    c, "status", "aggregate_snapshot", "queued_size", default="0 bytes"
                ),
            })
        audit.log_call("get_connections", {"group_id": group_id}, f"{len(connections)} connections")
        return {"group_id": group_id, "connections": connections}
    except Exception:
        logger.error("get_connections failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def get_flow_status(group_id: str = "root") -> dict:
    """Get running/stopped/invalid counts and throughput for a process group.

    Endpoint: GET /nifi-api/flow/process-groups/{id}/status
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.FlowApi().get_process_group_status(id=group_id)
        snap = _attr(result, "process_group_status", "aggregate_snapshot")
        audit.log_call("get_flow_status", {"group_id": group_id}, "ok")
        return {
            "group_id": group_id,
            "running_count": _attr(snap, "running_count", default=0),
            "stopped_count": _attr(snap, "stopped_count", default=0),
            "invalid_count": _attr(snap, "invalid_count", default=0),
            "disabled_count": _attr(snap, "disabled_count", default=0),
            "active_thread_count": _attr(snap, "active_thread_count", default=0),
            "queued_count": _attr(snap, "queued_count", default="0"),
            "bytes_read_5min": _attr(snap, "bytes_read", default="0 bytes"),
            "bytes_written_5min": _attr(snap, "bytes_written", default="0 bytes"),
        }
    except Exception:
        logger.error("get_flow_status failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def get_system_diagnostics() -> dict:
    """Get NiFi system health: heap, CPU, JVM version, uptime.

    Endpoint: GET /nifi-api/system-diagnostics
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.SystemDiagnosticsApi().get_system_diagnostics()
        snap = _attr(result, "system_diagnostics", "aggregate_snapshot")
        content_repos = _attr(snap, "content_repository_storage_usage") or []
        audit.log_call("get_system_diagnostics", {}, "ok")
        return {
            "nifi_version": _attr(snap, "version_info", "ni_fi_version"),
            "uptime": _attr(snap, "uptime"),
            "heap_utilization": _attr(snap, "heap_utilization"),
            "heap_used": _attr(snap, "used_heap"),
            "heap_max": _attr(snap, "max_heap"),
            "available_processors": _attr(snap, "available_processors"),
            "processor_load_average": _attr(snap, "processor_load_average"),
            "flow_file_repo_utilization": _attr(
                snap, "flow_file_repository_storage_usage", "utilization"
            ),
            "content_repo_utilizations": [
                _attr(r, "utilization") for r in content_repos
            ],
        }
    except Exception:
        logger.error("get_system_diagnostics failed", exc_info=True)
        raise
