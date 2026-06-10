from __future__ import annotations

import logging
import nipyapi.nifi
import nipyapi.nifi.models as m

from nifi_mcp.auth import ensure_authenticated
from nifi_mcp.config import settings
from nifi_mcp.security import audit
from nifi_mcp.security.permissions import require_permission
from nifi_mcp.server import mcp
from nifi_mcp.tools._utils import _attr

logger = logging.getLogger(__name__)


@mcp.tool()
def create_process_group(
    name: str,
    parent_group_id: str = "root",
    x: float = 0.0,
    y: float = 0.0,
) -> dict:
    """Create a new process group inside parent_group_id.

    Endpoint: POST /nifi-api/process-groups/{id}/process-groups
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("create_process_group")
        params = {"name": name, "parent_group_id": parent_group_id, "x": x, "y": y}

        if settings.mcp_dry_run:
            audit.log_call("create_process_group", params, "dry_run")
            return {"dry_run": True, "would_create": params}

        body = m.ProcessGroupEntity(
            revision=m.RevisionDTO(version=0),
            component=m.ProcessGroupDTO(
                name=name,
                position=m.PositionDTO(x=x, y=y),
            ),
        )
        result = nipyapi.nifi.ProcessGroupsApi().create_process_group(
            id=parent_group_id, body=body
        )
        audit.log_call("create_process_group", params, f"created {result.id}")
        return {
            "id": result.id,
            "name": _attr(result, "component", "name"),
            "parent_group_id": _attr(result, "component", "parent_group_id"),
        }
    except Exception:
        logger.error("create_process_group failed — name: %s", name, exc_info=True)
        raise


@mcp.tool()
def create_processor(
    name: str,
    processor_type: str,
    group_id: str = "root",
    x: float = 0.0,
    y: float = 0.0,
) -> dict:
    """Add a new processor to group_id.

    processor_type is the full Java class name, e.g.
    'org.apache.nifi.processors.standard.GetFile'.

    Endpoint: POST /nifi-api/process-groups/{id}/processors
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("create_processor")
        params = {"name": name, "type": processor_type, "group_id": group_id}

        if settings.mcp_dry_run:
            audit.log_call("create_processor", params, "dry_run")
            return {"dry_run": True, "would_create": params}

        body = m.ProcessorEntity(
            revision=m.RevisionDTO(version=0),
            component=m.ProcessorDTO(
                name=name,
                type=processor_type,
                position=m.PositionDTO(x=x, y=y),
            ),
        )
        result = nipyapi.nifi.ProcessGroupsApi().create_processor(id=group_id, body=body)
        audit.log_call("create_processor", params, f"created {result.id}")
        return {
            "id": result.id,
            "name": _attr(result, "component", "name"),
            "type": _attr(result, "component", "type"),
            "state": _attr(result, "component", "state"),
        }
    except Exception:
        logger.error(
            "create_processor failed — name: %s, group_id: %s", name, group_id, exc_info=True
        )
        raise


@mcp.tool()
def update_processor(
    processor_id: str,
    name: str | None = None,
    properties: dict[str, str] | None = None,
    scheduling_period: str | None = None,
) -> dict:
    """Update a processor's name, config properties, or scheduling period.

    Fetches the current revision automatically — no need to pass a version.
    At least one of name, properties, or scheduling_period must be provided.

    Endpoint: PUT /nifi-api/processors/{id}
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("update_processor")
        params = {
            "processor_id": processor_id,
            "name": name,
            "properties": properties,
            "scheduling_period": scheduling_period,
        }

        if settings.mcp_dry_run:
            audit.log_call("update_processor", params, "dry_run")
            return {"dry_run": True, "would_update": params}

        current = nipyapi.nifi.ProcessorsApi().get_processor(id=processor_id)
        has_config = properties or scheduling_period
        body = m.ProcessorEntity(
            revision=current.revision,
            component=m.ProcessorDTO(
                id=processor_id,
                name=name,
                config=m.ProcessorConfigDTO(
                    properties=properties,
                    scheduling_period=scheduling_period,
                ) if has_config else None,
            ),
        )
        result = nipyapi.nifi.ProcessorsApi().update_processor(id=processor_id, body=body)
        audit.log_call("update_processor", params, f"updated {processor_id}")
        return {
            "id": result.id,
            "name": _attr(result, "component", "name"),
            "properties_updated": list(properties.keys()) if properties else [],
        }
    except Exception:
        logger.error("update_processor failed — processor_id: %s", processor_id, exc_info=True)
        raise


@mcp.tool()
def create_connection(
    source_id: str,
    destination_id: str,
    group_id: str = "root",
    relationships: list[str] | None = None,
    source_type: str = "PROCESSOR",
    destination_type: str = "PROCESSOR",
) -> dict:
    """Connect source_id to destination_id within group_id.

    relationships defaults to ['success'].
    source_type / destination_type: PROCESSOR | INPUT_PORT | OUTPUT_PORT | FUNNEL.

    Endpoint: POST /nifi-api/process-groups/{id}/connections
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("create_connection")
        rels = relationships or ["success"]
        params = {
            "source_id": source_id,
            "destination_id": destination_id,
            "group_id": group_id,
            "relationships": rels,
        }

        if settings.mcp_dry_run:
            audit.log_call("create_connection", params, "dry_run")
            return {"dry_run": True, "would_create": params}

        body = m.ConnectionEntity(
            revision=m.RevisionDTO(version=0),
            source_id=source_id,
            source_type=source_type,
            source_group_id=group_id,
            destination_id=destination_id,
            destination_type=destination_type,
            destination_group_id=group_id,
            component=m.ConnectionDTO(
                source=m.ConnectableDTO(
                    id=source_id, type=source_type, group_id=group_id
                ),
                destination=m.ConnectableDTO(
                    id=destination_id, type=destination_type, group_id=group_id
                ),
                selected_relationships=rels,
            ),
        )
        result = nipyapi.nifi.ProcessGroupsApi().create_connection(id=group_id, body=body)
        audit.log_call("create_connection", params, f"created {result.id}")
        return {
            "id": result.id,
            "source_id": _attr(result, "component", "source", "id"),
            "destination_id": _attr(result, "component", "destination", "id"),
            "relationships": _attr(result, "component", "selected_relationships"),
        }
    except Exception:
        logger.error(
            "create_connection failed — source: %s -> dest: %s", source_id, destination_id, exc_info=True
        )
        raise


@mcp.tool()
def delete_processor(processor_id: str) -> dict:
    """Delete a processor by ID. The processor must be STOPPED or DISABLED first.

    Fetches the current revision automatically.

    Endpoint: DELETE /nifi-api/processors/{id}
    Permissions: full
    """
    ensure_authenticated()
    try:
        require_permission("delete_processor")
        params = {"processor_id": processor_id}

        current = nipyapi.nifi.ProcessorsApi().get_processor(id=processor_id)
        proc_name = _attr(current, "component", "name", default=processor_id)
        run_status = _attr(current, "status", "run_status", default="")

        if settings.mcp_dry_run:
            audit.log_call("delete_processor", params, "dry_run")
            return {"dry_run": True, "would_delete": {"id": processor_id, "name": proc_name}}

        if run_status not in ("STOPPED", "DISABLED", ""):
            raise RuntimeError(
                f"Processor '{proc_name}' is {run_status} — stop it before deleting."
            )

        nipyapi.nifi.ProcessorsApi().delete_processor(
            id=processor_id,
            version=str(current.revision.version),
        )
        audit.log_call("delete_processor", params, f"deleted {processor_id}")
        return {"deleted_id": processor_id, "name": proc_name}
    except Exception:
        logger.error("delete_processor failed — processor_id: %s", processor_id, exc_info=True)
        raise
