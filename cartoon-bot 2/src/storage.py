"""Free video/JSON storage on Supabase Storage (public bucket). No card needed."""
import json, requests
import config as C
from util import retry, log

def _headers(extra=None):
    key = C.SUPABASE_KEY()
    h = {"apikey": key}
    if key.startswith("eyJ"):                 # legacy JWT keys also go in Authorization; new sb_secret keys don't
        h["Authorization"] = f"Bearer {key}"
    h.update(extra or {})
    return h

def _base():
    return f"{C.SUPABASE_URL()}/storage/v1/object"

def public_url(key):
    return f"{_base()}/public/{C.SUPABASE_BUCKET()}/{key}"

@retry(tries=3, delay=4)
def _upload(data, key, content_type):
    r = requests.post(f"{_base()}/{C.SUPABASE_BUCKET()}/{key}", data=data, timeout=300,
                      headers=_headers({"Content-Type": content_type, "x-upsert": "true"}))
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Supabase upload {key} failed {r.status_code}: {r.text[:200]}")

def upload_file(path, key, content_type="video/mp4"):
    with open(path, "rb") as f:
        _upload(f.read(), key, content_type)
    return public_url(key)

def get_json(key, default):
    r = requests.get(f"{_base()}/authenticated/{C.SUPABASE_BUCKET()}/{key}", headers=_headers(), timeout=60)
    if r.status_code in (400, 404):           # file doesn't exist yet
        return default
    if r.status_code != 200:                  # real error: stop, never overwrite good data with a default
        raise RuntimeError(f"Supabase read {key} failed {r.status_code}: {r.text[:200]}")
    try:
        return r.json()
    except ValueError:
        return default

def put_json(key, data):
    _upload(json.dumps(data, ensure_ascii=False).encode(), key, "application/json")

def delete(key):
    try:
        requests.delete(f"{_base()}/{C.SUPABASE_BUCKET()}", headers=_headers({"Content-Type": "application/json"}),
                        data=json.dumps({"prefixes": [key]}), timeout=60)
    except Exception as e:
        log("Delete failed:", e)

def cleanup(prefix, keep=30):
    """Keep only the newest `keep` files under prefix."""
    r = requests.post(f"{C.SUPABASE_URL()}/storage/v1/object/list/{C.SUPABASE_BUCKET()}",
                      headers=_headers({"Content-Type": "application/json"}), timeout=60,
                      data=json.dumps({"prefix": prefix, "limit": 1000, "offset": 0,
                                       "sortBy": {"column": "created_at", "order": "asc"}}))
    if r.status_code != 200:
        return
    names = [f["name"] for f in r.json() if f.get("name") and not f["name"].endswith("/")]
    old = names[:-keep] if len(names) > keep else []
    if old:
        requests.delete(f"{_base()}/{C.SUPABASE_BUCKET()}", headers=_headers({"Content-Type": "application/json"}),
                        data=json.dumps({"prefixes": [f"{prefix}/{n}" for n in old]}), timeout=60)
        log(f"Cleaned {len(old)} old files")
