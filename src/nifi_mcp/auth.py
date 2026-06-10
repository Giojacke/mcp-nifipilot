import logging
import nipyapi
import nipyapi.security

from nifi_mcp.config import settings

logger = logging.getLogger(__name__)


def login() -> None:
    """Authenticate against NiFi and store the JWT in nipyapi's session.

    Endpoint: POST /nifi-api/access/token
    Required env vars: NIFI_USERNAME, NIFI_PASSWORD
    """
    nipyapi.security.service_login(
        service="nifi",
        username=settings.nifi_username,
        password=settings.nifi_password,
    )


def ensure_authenticated() -> None:
    """Re-login if the current nipyapi session returns 401."""
    try:
        nipyapi.nifi.FlowApi().get_process_group_status(id="root")
    except nipyapi.nifi.rest.ApiException as exc:
        if exc.status == 401:
            login()
        else:
            logger.error(
                "NiFi API error during auth check — status %s: %s",
                exc.status,
                exc.reason,
            )
            raise
