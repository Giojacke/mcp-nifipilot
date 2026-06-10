from unittest.mock import MagicMock, call, patch

from nifi_mcp.tools.control import (
    get_queue_status,
    purge_queue,
    start_process_group,
    start_processor,
    stop_process_group,
    stop_processor,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _proc(id="p1", name="GetFile", revision=3):
    e = MagicMock()
    e.id = id
    e.component.name = name
    e.revision.version = revision
    return e


def _run_status_result(id="p1", name="GetFile"):
    r = MagicMock()
    r.id = id
    r.component.name = name
    return r


# ── start_processor ───────────────────────────────────────────────────────────

def test_start_processor_calls_update_run_status():
    current = _proc("p1", "GetFile", revision=4)
    updated = _run_status_result("p1", "GetFile")

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        MockApi.return_value.update_run_status.return_value = updated
        result = start_processor("p1")

    call_body = MockApi.return_value.update_run_status.call_args.kwargs["body"]
    assert call_body.state == "RUNNING"
    assert result["requested_state"] == "RUNNING"
    assert result["id"] == "p1"


# ── stop_processor ────────────────────────────────────────────────────────────

def test_stop_processor_requests_stopped():
    current = _proc("p2", "PutFile", revision=2)
    updated = _run_status_result("p2", "PutFile")

    with patch("nipyapi.nifi.ProcessorsApi") as MockApi:
        MockApi.return_value.get_processor.return_value = current
        MockApi.return_value.update_run_status.return_value = updated
        result = stop_processor("p2")

    call_body = MockApi.return_value.update_run_status.call_args.kwargs["body"]
    assert call_body.state == "STOPPED"
    assert result["requested_state"] == "STOPPED"


# ── start_process_group ───────────────────────────────────────────────────────

def test_start_process_group_schedules_running():
    with patch("nipyapi.nifi.FlowApi") as MockApi:
        result = start_process_group("pg-1")

    body = MockApi.return_value.schedule_components.call_args.kwargs["body"]
    assert body.state == "RUNNING"
    assert result["requested_state"] == "RUNNING"
    assert result["group_id"] == "pg-1"


def test_start_process_group_defaults_to_root():
    with patch("nipyapi.nifi.FlowApi") as MockApi:
        result = start_process_group()

    assert result["group_id"] == "root"
    MockApi.return_value.schedule_components.assert_called_once()


# ── stop_process_group ────────────────────────────────────────────────────────

def test_stop_process_group_schedules_stopped():
    with patch("nipyapi.nifi.FlowApi") as MockApi:
        result = stop_process_group("pg-1")

    body = MockApi.return_value.schedule_components.call_args.kwargs["body"]
    assert body.state == "STOPPED"
    assert result["requested_state"] == "STOPPED"


# ── get_queue_status ──────────────────────────────────────────────────────────

def test_get_queue_status_returns_counts():
    mock_result = MagicMock()
    snap = mock_result.connection_status.aggregate_snapshot
    snap.queued_count = "123"
    snap.queued_size = "45 KB"
    snap.input = "10"
    snap.output = "5"

    with patch("nipyapi.nifi.ConnectionsApi") as MockApi:
        MockApi.return_value.get_connection_status.return_value = mock_result
        result = get_queue_status("conn-1")

    assert result["queued_count"] == "123"
    assert result["queued_size"] == "45 KB"
    assert result["connection_id"] == "conn-1"


# ── purge_queue ───────────────────────────────────────────────────────────────

def test_purge_queue_dry_run_shows_queue_size():
    mock_status = MagicMock()
    snap = mock_status.connection_status.aggregate_snapshot
    snap.queued_count = "500"
    snap.queued_size = "2 MB"

    with patch("nipyapi.nifi.ConnectionsApi") as MockConnApi, \
         patch("nipyapi.nifi.FlowFileQueuesApi") as MockQueueApi:
        MockConnApi.return_value.get_connection_status.return_value = mock_status

        import importlib, nifi_mcp.config as cfg
        importlib.reload(cfg)

        # Temporarily patch settings.mcp_dry_run
        import nifi_mcp.tools.control as ctrl
        original = ctrl.settings.mcp_dry_run
        ctrl.settings.__class__.mcp_dry_run = property(lambda self: True)
        try:
            result = ctrl.purge_queue("conn-1")
        finally:
            ctrl.settings.__class__.mcp_dry_run = property(lambda self: original)

    MockQueueApi.return_value.create_drop_request.assert_not_called()
    assert result["dry_run"] is True
    assert result["would_drop"]["queued_count"] == "500"


def test_purge_queue_polls_until_finished():
    drop_created = MagicMock()
    drop_created.drop_request.id = "drop-42"

    drop_done = MagicMock()
    drop_done.drop_request.finished = True
    drop_done.drop_request.dropped_count = 99

    with patch("nipyapi.nifi.FlowFileQueuesApi") as MockApi, \
         patch("time.sleep"):
        MockApi.return_value.create_drop_request.return_value = drop_created
        MockApi.return_value.get_drop_request.return_value = drop_done

        result = purge_queue("conn-2")

    MockApi.return_value.create_drop_request.assert_called_once_with(id="conn-2")
    MockApi.return_value.remove_drop_request.assert_called_once_with(
        id="conn-2", drop_request_id="drop-42"
    )
    assert result["dropped_count"] == 99
    assert result["finished"] is True
