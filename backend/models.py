"""Data models for Camoufox Profile Manager."""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional


@dataclass
class ProxyConfig:
    """Proxy server configuration."""
    host: str = "127.0.0.1"
    port: int = 7888
    username: str = ""
    password: str = ""
    protocol: str = "socks5"
    enabled: bool = False

    def to_proxy_dict(self) -> Optional[Dict[str, Any]]:
        """
        Convert ProxyConfig to Camoufox library format.
        Returns None if proxy is not enabled or not configured.
        """
        if not self.enabled or not self.host or not self.port:
            return None
        
        result = {"server": f"{self.protocol}://{self.host}:{self.port}"}
        
        if self.username:
            result["username"] = self.username
        
        if self.password:
            result["password"] = self.password
        
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Profile:
    """Browser profile configuration."""
    name: str = "Profile"
    viewport_width: int = 1280
    viewport_height: int = 800
    fullscreen: bool = False
    persistent_dir: str = ""
    use_geoip: bool = False
    proxy: ProxyConfig = field(default_factory=ProxyConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["proxy"] = self.proxy.to_dict()
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Profile":
        """Create Profile from dictionary (JSON deserialization)."""
        raw_proxy = d.get("proxy", {})
        if not isinstance(raw_proxy, dict):
            raw_proxy = {}

        name = d.get("name", "Profile")

        persistent_dir = d.get("persistent_dir", "")
        if not persistent_dir:
            persistent_dir = f"D:\\Data\\Camoufox Profile {name}"

        # Backward compatibility: add default protocol if missing
        if "protocol" not in raw_proxy:
            raw_proxy["protocol"] = "socks5"

        # Backward compatibility: infer enabled from host/port if missing
        if "enabled" not in raw_proxy:
            raw_proxy["enabled"] = bool(raw_proxy.get("host") and raw_proxy.get("port"))

        # Default values for host/port if empty
        if not raw_proxy.get("host"):
            raw_proxy["host"] = "127.0.0.1"
        if not raw_proxy.get("port"):
            raw_proxy["port"] = 7888

        return Profile(
            name=name,
            viewport_width=int(d.get("viewport_width", 1280)),
            viewport_height=int(d.get("viewport_height", 800)),
            fullscreen=bool(d.get("fullscreen", False)),
            persistent_dir=persistent_dir,
            use_geoip=bool(d.get("use_geoip", False)),
            proxy=ProxyConfig(
                host=raw_proxy.get("host", "127.0.0.1"),
                port=int(raw_proxy.get("port", 7888) or 7888),
                username=raw_proxy.get("username", ""),
                password=raw_proxy.get("password", ""),
                protocol=raw_proxy.get("protocol", "socks5"),
                enabled=bool(raw_proxy.get("enabled", False)),
            ),
        )
