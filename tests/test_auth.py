from unittest.mock import MagicMock, patch

import nipyapi.nifi.rest
import pytest

from nifi_mcp.auth import ensure_authenticated, login


def _api_exception(status: int) -> nipyapi.nifi.rest.ApiException:
    exc = nipyapi.nifi.rest.ApiException(status=status)
    exc.status = status
    exc.reason = f"HTTP {status}"
    return exc


@patch("nifi_mcp.auth.nipyapi.security.service_login")
def test_login_calls_service_login_with_credentials(mock_service_login):
    """login() forwards username and password from settings to nipyapi."""
    login()

    mock_service_login.assert_called_once_with(
        service="nifi",
        username="test",
        password="test",
    )


@patch("nifi_mcp.auth.login")
@patch("nifi_mcp.auth.nipyapi.nifi.FlowApi")
def test_ensure_authenticated_does_not_login_when_session_is_active(
    mock_flow_api_cls, mock_login
):
    """ensure_authenticated() skips login() when the probe call succeeds."""
    mock_flow_api_cls.return_value.get_process_group_status.return_value = MagicMock()

    ensure_authenticated()

    mock_login.assert_not_called()


@patch("nifi_mcp.auth.login")
@patch("nifi_mcp.auth.nipyapi.nifi.FlowApi")
def test_ensure_authenticated_calls_login_on_401(mock_flow_api_cls, mock_login):
    """ensure_authenticated() calls login() when the probe returns 401."""
    mock_flow_api_cls.return_value.get_process_group_status.side_effect = (
        _api_exception(401)
    )

    ensure_authenticated()

    mock_login.assert_called_once()


@patch("nifi_mcp.auth.login")
@patch("nifi_mcp.auth.nipyapi.nifi.FlowApi")
def test_ensure_authenticated_reraises_non_401_api_error(
    mock_flow_api_cls, mock_login
):
    """ensure_authenticated() re-raises ApiException with status != 401 without calling login()."""
    mock_flow_api_cls.return_value.get_process_group_status.side_effect = (
        _api_exception(500)
    )

    with pytest.raises(nipyapi.nifi.rest.ApiException) as exc_info:
        ensure_authenticated()

    assert exc_info.value.status == 500
    mock_login.assert_not_called()


@patch("nifi_mcp.auth.login")
@patch("nifi_mcp.auth.nipyapi.nifi.FlowApi")
def test_ensure_authenticated_logs_error_on_non_401_api_error(
    mock_flow_api_cls, mock_login, caplog
):
    """ensure_authenticated() logs the error before re-raising on status != 401."""
    import logging

    mock_flow_api_cls.return_value.get_process_group_status.side_effect = (
        _api_exception(503)
    )

    with caplog.at_level(logging.ERROR, logger="nifi_mcp.auth"):
        with pytest.raises(nipyapi.nifi.rest.ApiException):
            ensure_authenticated()

    assert any("503" in record.message for record in caplog.records)
