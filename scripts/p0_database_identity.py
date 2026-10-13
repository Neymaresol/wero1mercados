"""P0: safe, offline production configuration diagnostic (never expose URL or credentials)."""
import hashlib
import hmac
import os
from urllib.parse import urlsplit

def diagnose(env=None):
    env = os.environ if env is None else env
    raw = env.get("DATABASE_URL", "")
    if not raw:
        return {"configured": False, "valid_format": False, "reason": "missing", "fingerprint": None}
    try:
        u = urlsplit(raw)
        valid = u.scheme in ("postgres", "postgresql") and bool(u.hostname and u.path.strip("/"))
    except ValueError:
        valid = False
    # Non-reversible identity only. No hostname, username, database or password printed.
    key = env.get("DB_DIAGNOSTIC_KEY", "")
    fingerprint = hmac.new(key.encode(), raw.encode(), hashlib.sha256).hexdigest()[:16] if valid and len(key) >= 32 else None
    return {"configured": True, "valid_format": valid, "reason": "ok" if valid else "invalid", "fingerprint": fingerprint}

if __name__ == "__main__":
    import json
    print(json.dumps(diagnose()))
