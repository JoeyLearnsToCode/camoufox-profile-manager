"""Profile data validation logic."""
from typing import Dict, Any, Tuple


def validate_profile(profile: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate profile data before persistence.
    
    Args:
        profile: Profile dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Name validation
    name = profile.get('name', '').strip()
    if not name:
        return False, "Profile name cannot be empty"
    
    if len(name) > 100:
        return False, "Profile name must be 100 characters or less"
    
    # Viewport validation
    width = profile.get('viewport_width', 0)
    height = profile.get('viewport_height', 0)
    
    if not isinstance(width, int) or width < 320 or width > 10000:
        return False, "Viewport width must be between 320 and 10000"
    
    if not isinstance(height, int) or height < 320 or height > 10000:
        return False, "Viewport height must be between 320 and 10000"
    
    # Fullscreen validation
    if not isinstance(profile.get('fullscreen'), bool):
        return False, "Fullscreen must be a boolean value"
    
    # Storage directory validation
    storage = profile.get('persistent_dir', '').strip()
    if profile.get('storage_enabled', False) and not storage:
        return False, "Persistent storage directory cannot be empty"
    
    # GeoIP validation
    if not isinstance(profile.get('use_geoip'), bool):
        return False, "use_geoip must be a boolean value"
    
    # Proxy validation (if provided)
    proxy = profile.get('proxy', {})
    if isinstance(proxy, dict) and proxy.get('host'):
        is_valid, error = validate_proxy(proxy)
        if not is_valid:
            return False, f"Proxy error: {error}"
    
    return True, ""


def validate_proxy(proxy: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate proxy configuration.
    
    Args:
        proxy: Proxy configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    host = proxy.get('host', '').strip()
    port = proxy.get('port', 0)
    protocol = proxy.get('protocol', 'socks5')
    enabled = proxy.get('enabled', False)
    
    # Protocol validation
    if protocol not in ['socks5', 'http', 'https']:
        return False, "Protocol must be socks5, http, or https"
    
    # If proxy is enabled, host and port are required
    if enabled:
        if not host or not port:
            return False, "Host and port required when proxy is enabled"
    
    # If host is empty and not enabled, proxy is disabled (valid state)
    if not host and not enabled:
        return True, ""
    
    # Host validation (basic format check)
    if len(host) > 255:
        return False, "Proxy host must be 255 characters or less"
    
    # Port validation
    if not isinstance(port, int) or port < 1 or port > 65535:
        return False, "Proxy port must be between 1 and 65535"
    
    # Username/password validation (optional, but should be strings)
    username = proxy.get('username', '')
    password = proxy.get('password', '')
    
    if not isinstance(username, str):
        return False, "Proxy username must be a string"
    
    if not isinstance(password, str):
        return False, "Proxy password must be a string"
    
    return True, ""
