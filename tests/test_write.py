import json
from unittest.mock import MagicMock, patch

from nifi_mcp.tools.write import (
    create_connection,
    create_process_group,
    create_processor,
    delete_process_group,
    delete_processor,
    update_processor,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_created_pg(id="pg-new", name="New Group", parent="root"):
    r = MagicMock()
    r.id = id
    r.component.name = name
    r.component.parent_group_id = parent
    return r


def _make_created_proc(id="proc-new", name="GetFile", type="org.apache.nifi.processors.standard.GetFile", state="STOPPED"):
    r = MagicMock()
    r.id = id
    r.component.name = name
    r.component.type = type
    r.component.state = state
    return r


def _make_process_group_entity(id="pg-1", name="MyGroup", running_count=0, revision_version=1):
    e = MagicMock()
    e.id = id
    e.component.name = name
    e.status.aggregate_snapshot.running_count = running_count
    e.revision.version = revision_version
    return e


def _make_processor_entity(id="proc-1", name="GetFile", run_status="STOPPED", revision_version=3):
    e = MagicMock()
    e.id = id
    e.component.name = name
    e.component.id = id
    e.status.run_status = run_status
    e.revision.version = revision_version
    return e


# ── create_process_group ──────────────────────────────────────────────────────

def test_create_process_group_returns_id():
    mock_result = _make_created_pg("pg-abc", "My Group")

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.create_process_group.return_value = mock_result
        result = create_process_group(name="My Group", parent_group_id="root")

    assert result["id"] == "pg-abc"
    assert result["name"] == "My Group"


def test_create_process_group_dry_run():
    import nifi_mcp.tools.write as w

    with patch.object(type(w.settings), "mcp_dry_run", new_callable=lambda: property(lambda self: True)), \
         patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        result = w.create_process_group(name="Test")

    MockApi.return_value.create_process_group.assert_not_called()
    assert result["dry_run"] is True


# ── create_processor ──────────────────────────────────────────────────────────

def test_create_processor_returns_id():
    mock_result = _make_created_proc("proc-xyz", "GetFile")

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.create_processor.return_value = mock_result
        result = create_processor(
            name="GetFile",
            processor_type="org.apache.nifi.processors.standard.GetFile",
        )

    assert result["id"] == "proc-xyz"
    assert result["state"] == "STOPPED"


# ── update_processor ──────────────────────────────────────────────────────────

def test_update_processor_sends_new_name():
    current = _make_processor_entity("proc-1", "OldName", revision_version=5)
    updated = _make_processor_entity("proc-1", "NewName")

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        MockApi.return_value.update_processor.return_value = updated
        result = update_processor(processor_id="proc-1", name="NewName")

    assert result["id"] == "proc-1"
    assert result["name"] == "NewName"
    assert result["properties_updated"] == []


def test_update_processor_reports_updated_keys():
    current = _make_processor_entity()
    updated = _make_processor_entity()

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        MockApi.return_value.update_processor.return_value = updated
        result = update_processor(
            processor_id="proc-1",
            properties={"Input Directory": "/tmp", "Recurse Subdirectories": "true"},
        )

    assert set(result["properties_updated"]) == {"Input Directory", "Recurse Subdirectories"}


# ── create_connection ─────────────────────────────────────────────────────────

def test_create_connection_defaults_to_success_relationship():
    mock_result = MagicMock()
    mock_result.id = "conn-1"
    mock_result.component.source.id = "src"
    mock_result.component.destination.id = "dst"
    mock_result.component.selected_relationships = ["success"]

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.create_connection.return_value = mock_result
        result = create_connection(source_id="src", destination_id="dst")

    assert result["id"] == "conn-1"
    assert result["relationships"] == ["success"]

    call_body = MockApi.return_value.create_connection.call_args.kwargs["body"]
    assert call_body.component.selected_relationships == ["success"]


# ── delete_processor ──────────────────────────────────────────────────────────

def test_delete_processor_stopped():
    current = _make_processor_entity("proc-del", "GetFile", run_status="STOPPED", revision_version=7)

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        result = delete_processor("proc-del")

    MockApi.return_value.delete_processor.assert_called_once_with(
        id="proc-del", version="7"
    )
    assert result["deleted_id"] == "proc-del"
    assert result["name"] == "GetFile"


def test_delete_processor_running_raises():
    current = _make_processor_entity("proc-run", "GetFile", run_status="RUNNING")

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        try:
            delete_processor("proc-run")
            assert False, "should have raised"
        except RuntimeError as exc:
            assert "RUNNING" in str(exc)

    MockApi.return_value.delete_processor.assert_not_called()


# ── delete_process_group ──────────────────────────────────────────────────────

def test_delete_process_group_stopped():
    current = _make_process_group_entity("pg-del", "Test-CodHector", running_count=0, revision_version=4)

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_process_group.return_value = current
        result = delete_process_group("pg-del")

    MockApi.return_value.remove_process_group.assert_called_once_with(
        id="pg-del", version="4"
    )
    assert result["deleted_id"] == "pg-del"
    assert result["name"] == "Test-CodHector"


def test_delete_process_group_running_raises():
    current = _make_process_group_entity("pg-run", "ActiveGroup", running_count=3)

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_process_group.return_value = current
        try:
            delete_process_group("pg-run")
            assert False, "should have raised"
        except RuntimeError as exc:
            assert "3" in str(exc)

    MockApi.return_value.remove_process_group.assert_not_called()


# ── audit redaction ───────────────────────────────────────────────────────────

def test_update_processor_redacts_sensitive_properties_in_audit_log():
    """update_processor with DB_PASSWORD in properties must log ***REDACTED***, not the real value."""
    import nifi_mcp.security.audit as audit_mod

    current = _make_processor_entity()
    updated = _make_processor_entity()

    logged_entries = []

    def capture(msg):
        logged_entries.append(json.loads(msg))

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi, \
         patch.object(audit_mod._logger, "info", side_effect=capture):
        MockApi.return_value.get_processor.return_value = current
        MockApi.return_value.update_processor.return_value = updated
        update_processor(processor_id="proc-1", properties={"DB_PASSWORD": "secret"})

    assert logged_entries, "audit logger was never called"
    props = logged_entries[0]["params"]["properties"]
    assert props["DB_PASSWORD"] == "***REDACTED***", f"expected REDACTED, got: {props['DB_PASSWORD']}"
    assert "secret" not in json.dumps(logged_entries[0])


def test_delete_process_group_dry_run():
    import nifi_mcp.tools.write as w

    current = _make_process_group_entity("pg-dry", "DryGroup")

    with patch.object(type(w.settings), "mcp_dry_run", new_callable=lambda: property(lambda self: True)), \
         patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_process_group.return_value = current
        result = w.delete_process_group("pg-dry")

    MockApi.return_value.remove_process_group.assert_not_called()
    assert result["dry_run"] is True
    assert result["would_delete"]["id"] == "pg-dry"
