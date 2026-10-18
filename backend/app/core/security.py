import re
from urllib.parse import urlparse
from backend.app.core.config import settings

def is_url_allowed(url: str) -> bool:
    """
    Validates target URL against safety boundaries.
    Only allows HTTP/HTTPS schemes and whitelisted hosts.
    Prevents loopback access outside allowed dev hosts, AWS/cloud metadata (169.254.169.254), etc.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block cloud metadata addresses
        if hostname == "169.254.169.254" or hostname.startswith("169.254."):
            return False

        # If allow all hosts is active or wildcard is present
        if getattr(settings, "ALLOW_ALL_HOSTS", False) or "*" in settings.ALLOWED_HOSTS:
            return True

        # Check whitelist
        for allowed in settings.ALLOWED_HOSTS:
            if hostname == allowed or hostname.endswith("." + allowed):
                return True
                
        return False
    except Exception:
        return False

def sanitize_logs(text: str) -> str:
    """Redacts sensitive credentials, tokens, and passwords from logs and prompts."""
    if not text:
        return ""
    # Redact passwords
    text = re.sub(r'(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1[REDACTED]\3', text, flags=re.IGNORECASE)
    # Redact API keys / tokens
    text = re.sub(r'(token["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1[REDACTED]\3', text, flags=re.IGNORECASE)
    # Redact authorization headers
    text = re.sub(r'(authorization["\']?\s*[:=]\s*["\'])(Bearer\s+[^"\']+)(["\'])', r'\1Bearer [REDACTED]\3', text, flags=re.IGNORECASE)
    return text
