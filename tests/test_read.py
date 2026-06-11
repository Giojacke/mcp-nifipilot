from unittest.mock import MagicMock, patch

from nifi_mcp.tools.read import (
    get_connections,
    get_flow_status,
    get_process_groups,
    get_processors,
    get_system_diagnostics,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_group(id="pg-1", name="My Group", running=2, stopped=1, invalid=0):
    g = MagicMock()
    g.id = id
    g.component.name = name
    g.status.aggregate_snapshot.running_count = running
    g.status.aggregate_snapshot.stopped_count = stopped
    g.status.aggregate_snapshot.invalid_count = invalid
    return g


def _make_processor(id="proc-1", name="GetFile", type="GetFile", state="RUNNING"):
    p = MagicMock()
    p.id = id
    p.component.name = name
    p.component.type = type
    p.component.state = state
    p.status.run_status = state
    p.status.aggregate_snapshot.active_thread_count = 1
    return p


def _make_connection(id="conn-1"):
    c = MagicMock()
    c.id = id
    c.component.name = "success"
    c.component.source.id = "src-1"
    c.component.source.name = "GetFile"
    c.component.destination.id = "dst-1"
    c.component.destination.name = "PutFile"
    c.status.aggregate_snapshot.queued_count = "5"
    c.status.aggregate_snapshot.queued_size = "10 KB"
    return c


# ── get_process_groups ────────────────────────────────────────────────────────

def test_get_process_groups_returns_list():
    mock_result = MagicMock()
    mock_result.process_groups = [_make_group("pg-1", "Alpha"), _make_group("pg-2", "Beta")]

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_process_groups.return_value = mock_result
        result = get_process_groups()

    assert result["group_id"] == "root"
    assert len(result["process_groups"]) == 2
    assert result["process_groups"][0]["id"] == "pg-1"
    assert result["process_groups"][0]["name"] == "Alpha"
    assert result["process_groups"][0]["running_count"] == 2


def test_get_process_groups_empty():
    mock_result = MagicMock()
    mock_result.process_groups = []

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_process_groups.return_value = mock_result
        result = get_process_groups(group_id="some-id")

    assert result["group_id"] == "some-id"
    assert result["process_groups"] == []


# ── get_processors ────────────────────────────────────────────────────────────

def test_get_processors_returns_list():
    mock_result = MagicMock()
    mock_result.processors = [_make_processor("p1", "GetFile"), _make_processor("p2", "PutFile")]

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_processors.return_value = mock_result
        result = get_processors()

    assert len(result["processors"]) == 2
    assert result["processors"][0]["id"] == "p1"
    assert result["processors"][0]["run_status"] == "RUNNING"


# ── get_connections ───────────────────────────────────────────────────────────

def test_get_connections_returns_list():
    mock_result = MagicMock()
    mock_result.connections = [_make_connection("c1")]

    with patch("nipyapi.nifi.ProcessGroupsApi") as MockApi:
        MockApi.return_value.get_connections.return_value = mock_result
        result = get_connections()

    conn = result["connections"][0]
    assert conn["id"] == "c1"
    assert conn["source_name"] == "GetFile"
    assert conn["destination_name"] == "PutFile"
    assert conn["queued_count"] == "5"


# ── get_flow_status ───────────────────────────────────────────────────────────

def test_get_flow_status_returns_expected_keys():
    mock_result = MagicMock()
    snap = mock_result.process_group_status.aggregate_snapshot
    snap.running_count = 3
    snap.stopped_count = 1
    snap.invalid_count = 0
    snap.disabled_count = 0
    snap.active_thread_count = 3
    snap.queued_count = "0"
    snap.bytes_read = "1 MB"
    snap.bytes_written = "2 MB"

    with patch("nipyapi.nifi.FlowApi") as MockApi:
        MockApi.return_value.get_process_group_status.return_value = mock_result
        result = get_flow_status()

    assert result["running_count"] == 3
    assert result["bytes_read_5min"] == "1 MB"
    assert "disabled_count" in result


# ── get_system_diagnostics ────────────────────────────────────────────────────

def test_get_system_diagnostics_returns_version():
    mock_result = MagicMock()
    snap = mock_result.system_diagnostics.aggregate_snapshot
    snap.version_info.ni_fi_version = "2.2.0"
    snap.uptime = "5 days"
    snap.heap_utilization = "40%"
    snap.used_heap = "512 MB"
    snap.max_heap = "2 GB"
    snap.available_processors = 8
    snap.processor_load_average = 1.5
    snap.flow_file_repository_storage_usage.utilization = "10%"
    snap.content_repository_storage_usage = []

    with patch("nipyapi.nifi.SystemDiagnosticsApi") as MockApi:
        MockApi.return_value.get_system_diagnostics.return_value = mock_result
        result = get_system_diagnostics()

    assert result["nifi_version"] == "2.2.0"
    assert result["heap_utilization"] == "40%"
    assert result["available_processors"] == 8
