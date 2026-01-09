# feishu/auth.py
import time
import requests
from config import FEISHU_HOST

_token_cache = {
    "token": None,
    "expire_at": 0.0,
}


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    now = time.time()

    if _token_cache["token"] and now < _token_cache["expire_at"] - 60:
        return _token_cache["token"]

    url = f"{FEISHU_HOST}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"tenant_access_token error: {data}")

    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expire_at"] = now + int(data.get("expire", 0))
    return _token_cache["token"]
