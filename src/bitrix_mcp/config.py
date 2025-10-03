"""Configuration management for Bitrix24 MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class BitrixConfig:
    """Bitrix24 configuration settings."""
    
    # Authentication settings
    webhook_url: Optional[str] = None
    access_token: Optional[str] = None
    portal_url: Optional[str] = None
    
    # Performance settings
    requests_per_second: float = 2.0
    request_pool_size: int = 50
    respect_velocity_policy: bool = True
    
    # SSL settings
    ssl_verify: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.webhook_url and not (self.access_token and self.portal_url):
            raise ValueError(
                "Either webhook_url or both access_token and portal_url must be provided"
            )
    
    @classmethod
    def from_env(cls) -> "BitrixConfig":
        """Create configuration from environment variables."""
        return cls(
            webhook_url=os.getenv("BITRIX24_WEBHOOK_URL"),
            access_token=os.getenv("BITRIX24_ACCESS_TOKEN"),
            portal_url=os.getenv("BITRIX24_PORTAL_URL"),
            requests_per_second=float(os.getenv("BITRIX24_REQUESTS_PER_SECOND", "2")),
            request_pool_size=int(os.getenv("BITRIX24_REQUEST_POOL_SIZE", "50")),
            respect_velocity_policy=os.getenv("BITRIX24_RESPECT_VELOCITY_POLICY", "true").lower() == "true",
            ssl_verify=os.getenv("BITRIX24_SSL_VERIFY", "true").lower() == "true",
        )


@dataclass
class MCPConfig:
    """MCP server configuration settings."""
    
    server_name: str = "bitrix24-mcp"
    server_version: str = "1.0.0"
    description: str = "Model Context Protocol server for Bitrix24 integration"
    
    # Transport settings
    transport: str = "stdio"  # stdio, streamable-http, sse
    port: int = 8000
    host: str = "localhost"
    
    # Logging settings
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        return cls(
            server_name=os.getenv("MCP_SERVER_NAME", "bitrix24-mcp"),
            server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
            description=os.getenv("MCP_SERVER_DESCRIPTION", "Model Context Protocol server for Bitrix24 integration"),
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
            port=int(os.getenv("MCP_PORT", "8000")),
            host=os.getenv("MCP_HOST", "localhost"),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
        )


def get_config() -> tuple[BitrixConfig, MCPConfig]:
    """Get complete configuration from environment."""
    return BitrixConfig.from_env(), MCPConfig.from_env()