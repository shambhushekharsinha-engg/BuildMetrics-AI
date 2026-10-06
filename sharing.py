"""
BuildMetrics AI — Project Sharing Module
Generates and validates signed read-only share tokens for blueprint sharing.
"""
import hashlib
import hmac
import json
import os
import time
from typing import Optional


_SECRET = os.environ.get("SHARE_SECRET", "dev-share-secret-change-in-prod")


def generate_share_token(building_id: str, user_id: str, ttl_hours: int = 72) -> str:
    """
    Generate a signed, time-limited share token for a building model.
    
    Args:
        building_id: The building's UUID from MODEL_STORE.
        user_id: The owning user's ID.
        ttl_hours: How long the token is valid (default 72h = 3 days).
    
    Returns:
        A URL-safe token string: base64-encoded JSON payload + HMAC signature.
    """
    import base64
    payload = {
        "building_id": building_id,
        "user_id": str(user_id),
        "exp": int(time.time()) + ttl_hours * 3600,
        "iat": int(time.time()),
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    
    sig = hmac.new(
        _SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # 16-char signature prefix
    
    return f"{payload_b64}.{sig}"


def validate_share_token(token: str) -> Optional[dict]:
    """
    Validate a share token. Returns the payload dict on success, None on failure.
    
    Checks: signature validity, expiry.
    """
    import base64
    try:
        payload_b64, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    
    # Verify signature
    expected_sig = hmac.new(
        _SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    if not hmac.compare_digest(sig, expected_sig):
        return None
    
    # Decode payload
    try:
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)
    except Exception:
        return None
    
    # Check expiry
    if time.time() > payload.get("exp", 0):
        return None
    
    return payload
