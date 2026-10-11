"""Read-only configuration check. Never prints secrets or connects to a database."""
import json
import os
from urllib.parse import urlparse

def inspect(env=None):
    env = os.environ if env is None else env
    raw = env.get("DATABASE_URL", "")
    if not raw:
        return {"configured": False, "valid_format": False, "reason": "DATABASE_URL_missing"}
    parsed = urlparse(raw)
    valid = parsed.scheme in ("postgres", "postgresql") and bool(parsed.hostname and parsed.path.strip("/"))
    return {"configured": True, "valid_format": bool(valid), "reason": "ok" if valid else "invalid_url"}

if __name__ == "__main__":
    print(json.dumps(inspect()))
