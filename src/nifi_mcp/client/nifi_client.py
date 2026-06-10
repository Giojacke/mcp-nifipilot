import functools
import logging
import nipyapi
import nipyapi.nifi

from nifi_mcp.auth import ensure_authenticated
from nifi_mcp.config import settings

logger = logging.getLogger(__name__)


def _with_auth(method):
    """Decorator: call ensure_authenticated() before the wrapped method."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        ensure_authenticated()
        return method(self, *args, **kwargs)
    return wrapper


class NiFiClient:
    """Thin wrapper over nipyapi (and httpx for uncovered endpoints).

    Configures nipyapi globally on instantiation so that all nipyapi API
    objects created later inherit the correct host and SSL settings.
    """

    def __init__(self) -> None:
        base = str(settings.nifi_url).rstrip("/")
        nipyapi.config.nifi_config.host = f"{base}/nifi-api"
        nipyapi.config.nifi_config.verify_ssl = settings.nifi_verify_ssl
        logger.debug("NiFiClient configured — host: %s", nipyapi.config.nifi_config.host)

    @_with_auth
    def ping(self) -> dict:
        """GET /nifi-api/system-diagnostics — verify NiFi is reachable.

        Endpoint: GET /nifi-api/system-diagnostics
        Permissions: none (public endpoint)
        """
        result = nipyapi.nifi.SystemDiagnosticsApi().get_system_diagnostics()
        version = result.system_diagnostics.aggregate_snapshot.version_info.ni_fi_version
        return {"status": "ok", "nifi_version": version}


# Module-level singleton — import this everywhere instead of constructing anew.
client = NiFiClient()
