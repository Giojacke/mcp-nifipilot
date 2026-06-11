from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_file_override=False,
    )

    # NiFi connection
    nifi_url: AnyHttpUrl = "https://localhost:8443"  # type: ignore[assignment]
    nifi_username: str = "admin"
    nifi_password: str = ""
    nifi_verify_ssl: bool = False

    # MCP behaviour
    mcp_mode: str = "readonly"
    mcp_audit_log: bool = True
    mcp_audit_log_path: str = "./logs/audit.log"
    mcp_rate_limit: int = 60
    mcp_dry_run: bool = False

    # Transport (stdio for local clients, sse for Docker/remote)
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    @field_validator("mcp_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("readonly", "full"):
            raise ValueError("MCP_MODE must be 'readonly' or 'full'")
        return v

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        if v not in ("stdio", "sse"):
            raise ValueError("MCP_TRANSPORT must be 'stdio' or 'sse'")
        return v


settings = Settings()
