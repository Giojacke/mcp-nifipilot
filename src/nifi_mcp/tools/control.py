from __future__ import annotations

import logging
import time

import nipyapi.nifi
import nipyapi.nifi.models as m

from nifi_mcp.auth import ensure_authenticated
from nifi_mcp.config import settings
from nifi_mcp.security import audit
from nifi_mcp.security.permissions import require_permission
from nifi_mcp.server import mcp
from nifi_mcp.tools._utils import _attr

logger = logging.getLogger(__name__)


def _update_run_status(processor_id: str, state: str) -> dict:
    current = nipyapi.nifi.ProcessorsApi().get_processor(id=processor_id)
    body = m.ProcessorRunStatusEntity(
        revision=current.revision,
        state=state,
        disconnected_node_acknowledged=False,
    )
    result = nipyapi.nifi.ProcessorsApi().update_run_status(id=processor_id, body=body)
    return {
        "id": processor_id,
        "name": _attr(result, "component", "name"),
        "requested_state": state,
    }


@mcp.tool()
def start_processor(processor_id: str) -> dict:
    """Start a processor. Must have no validation errors.

    Endpoint: PUT /nifi-api/processors/{id}/run-status
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("start_processor")
        params = {"processor_id": processor_id}
        if settings.mcp_dry_run:
            audit.log_call("start_processor", params, "dry_run")
            return {"dry_run": True, "would_start": processor_id}
        result = _update_run_status(processor_id, "RUNNING")
        audit.log_call("start_processor", params, "started")
        return result
    except Exception:
        logger.error("start_processor failed — processor_id: %s", processor_id, exc_info=True)
        raise


@mcp.tool()
def stop_processor(processor_id: str) -> dict:
    """Stop a running processor.

    Endpoint: PUT /nifi-api/processors/{id}/run-status
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("stop_processor")
        params = {"processor_id": processor_id}
        if settings.mcp_dry_run:
            audit.log_call("stop_processor", params, "dry_run")
            return {"dry_run": True, "would_stop": processor_id}
        result = _update_run_status(processor_id, "STOPPED")
        audit.log_call("stop_processor", params, "stopped")
        return result
    except Exception:
        logger.error("stop_processor failed — processor_id: %s", processor_id, exc_info=True)
        raise


@mcp.tool()
def start_process_group(group_id: str = "root") -> dict:
    """Start all processors in group_id.

    Endpoint: PUT /nifi-api/flow/process-groups/{id}
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("start_process_group")
        params = {"group_id": group_id}
        if settings.mcp_dry_run:
            audit.log_call("start_process_group", params, "dry_run")
            return {"dry_run": True, "would_start_group": group_id}
        nipyapi.nifi.FlowApi().schedule_components(
            id=group_id,
            body=m.ScheduleComponentsEntity(id=group_id, state="RUNNING"),
        )
        audit.log_call("start_process_group", params, "started")
        return {"group_id": group_id, "requested_state": "RUNNING"}
    except Exception:
        logger.error("start_process_group failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def stop_process_group(group_id: str = "root") -> dict:
    """Stop all processors in group_id.

    Endpoint: PUT /nifi-api/flow/process-groups/{id}
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("stop_process_group")
        params = {"group_id": group_id}
        if settings.mcp_dry_run:
            audit.log_call("stop_process_group", params, "dry_run")
            return {"dry_run": True, "would_stop_group": group_id}
        nipyapi.nifi.FlowApi().schedule_components(
            id=group_id,
            body=m.ScheduleComponentsEntity(id=group_id, state="STOPPED"),
        )
        audit.log_call("stop_process_group", params, "stopped")
        return {"group_id": group_id, "requested_state": "STOPPED"}
    except Exception:
        logger.error("stop_process_group failed — group_id: %s", group_id, exc_info=True)
        raise


@mcp.tool()
def get_queue_status(connection_id: str) -> dict:
    """Get current queue depth (count and size) for a connection.

    Endpoint: GET /nifi-api/connections/{id}/status
    Permissions: readonly or full
    """
    ensure_authenticated()
    try:
        result = nipyapi.nifi.ConnectionsApi().get_connection_status(id=connection_id)
        snap = _attr(result, "connection_status", "aggregate_snapshot")
        audit.log_call("get_queue_status", {"connection_id": connection_id}, "ok")
        return {
            "connection_id": connection_id,
            "queued_count": _attr(snap, "queued_count", default="0"),
            "queued_size": _attr(snap, "queued_size", default="0 bytes"),
            "input": _attr(snap, "input", default="0"),
            "output": _attr(snap, "output", default="0"),
        }
    except Exception:
        logger.error("get_queue_status failed — connection_id: %s", connection_id, exc_info=True)
        raise


@mcp.tool()
def purge_queue(connection_id: str) -> dict:
    """Drop all flowfiles from the queue of connection_id.

    Polls NiFi until the drop request finishes (max 30 s).
    Set MCP_DRY_RUN=true to preview without executing.

    Endpoint: POST /nifi-api/flowfile-queues/{id}/drop-requests
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("purge_queue")
        params = {"connection_id": connection_id}

        if settings.mcp_dry_run:
            status = nipyapi.nifi.ConnectionsApi().get_connection_status(id=connection_id)
            snap = _attr(status, "connection_status", "aggregate_snapshot")
            audit.log_call("purge_queue", params, "dry_run")
            return {
                "dry_run": True,
                "connection_id": connection_id,
                "would_drop": {
                    "queued_count": _attr(snap, "queued_count", default="0"),
                    "queued_size": _attr(snap, "queued_size", default="0 bytes"),
                },
            }

        drop = nipyapi.nifi.FlowFileQueuesApi().create_drop_request(id=connection_id)
        drop_id = drop.drop_request.id
        drop_req = drop

        for _ in range(60):  # max 30 s at 0.5 s intervals
            time.sleep(0.5)
            drop_req = nipyapi.nifi.FlowFileQueuesApi().get_drop_request(
                id=connection_id, drop_request_id=drop_id
            )
            if _attr(drop_req, "drop_request", "finished"):
                break

        nipyapi.nifi.FlowFileQueuesApi().remove_drop_request(
            id=connection_id, drop_request_id=drop_id
        )
        dropped = _attr(drop_req, "drop_request", "dropped_count", default=0)
        finished = _attr(drop_req, "drop_request", "finished", default=False)
        audit.log_call("purge_queue", params, f"dropped {dropped} flowfiles")
        return {
            "connection_id": connection_id,
            "dropped_count": dropped,
            "finished": finished,
        }
    except Exception:
        logger.error("purge_queue failed — connection_id: %s", connection_id, exc_info=True)
        raise
