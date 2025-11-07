"""Data models for Camoufox Profile Manager."""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional


@dataclass
class ProxyConfig:
    """Proxy server configuration."""
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""

    def to_proxy_dict(self) -> Optional[Dict[str, Any]]:
        """
        Convert ProxyConfig to Camoufox library format.
        Returns None if proxy is not configured.
        """
        if not self.host or not self.port:
            return None
        
        result = {"server": f"http://{self.host}:{self.port}"}
        
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
        
        # Default storage to C:\<ProfileName> if empty
        persistent_dir = d.get("persistent_dir", "")
        if not persistent_dir:
            persistent_dir = f"C:\\{name}"
        
        return Profile(
            name=name,
            viewport_width=int(d.get("viewport_width", 1280)),
            viewport_height=int(d.get("viewport_height", 800)),
            fullscreen=bool(d.get("fullscreen", False)),
            persistent_dir=persistent_dir,
            use_geoip=bool(d.get("use_geoip", False)),
            proxy=ProxyConfig(
                host=raw_proxy.get("host", ""),
                port=int(raw_proxy.get("port", 0) or 0),
                username=raw_proxy.get("username", ""),
                password=raw_proxy.get("password", ""),
            ),
        )
