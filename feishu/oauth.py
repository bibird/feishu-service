import json
import os
import time
import secrets
import requests
from typing import Dict, Optional
from config import FEISHU_HOST, DATA_DIR
from urllib.parse import urlencode

TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
USER_TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _load_tokens() -> Dict:
    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"states": {}, "users": {}}


def _save_tokens(data: Dict) -> None:
    os.makedirs(os.path.dirname(TOKENS_FILE), exist_ok=True)
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def new_state(user_key: str = "me") -> str:
    """
    生成 state 并写入 tokens.json，回调用来防 CSRF
    user_key: 可以用 open_id / employee_id / 自己定义的 key 来区分不同授权人
    """
    store = _load_tokens()
    state = secrets.token_urlsafe(24)
    store["states"][state] = {"user_key": user_key, "created_at": int(time.time())}
    _save_tokens(store)
    return state


def build_auth_url(app_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "app_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
    }
    qs = urlencode(params, safe=":/")
    auth_url = f"{FEISHU_HOST}/open-apis/authen/v1/index?{qs}"
    # print("[oauth] redirect_uri =", redirect_uri, flush=True)
    # print("[oauth] auth_url =", auth_url, flush=True) 飞书跳转url是否正确

    return auth_url



def exchange_code_for_user_token(app_id: str, app_secret: str, code: str) -> Dict:
    """
    用 code 换 user_access_token
    返回体里通常会带：access_token / refresh_token / expires_in / open_id 等
    """
    url = f"{FEISHU_HOST}/open-apis/authen/v1/access_token"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret, "code": code, "grant_type": "authorization_code"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    print("[oauth] exchange_token resp code/msg =", data.get("code"), data.get("msg"), flush=True)

    if data.get("code") != 0:
        raise RuntimeError(data)
    return data.get("data", {})


def refresh_user_token(app_id: str, app_secret: str, refresh_token: str) -> Dict:
    """
    刷新用户凭证-一个星期.
    """
    url = f"{FEISHU_HOST}/open-apis/authen/v1/refresh_access_token"
    resp = requests.post(
        url,
        json={
            "app_id": app_id,
            "app_secret": app_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    print("[oauth] refresh_token resp code/msg =", data.get("code"), data.get("msg"), flush=True)

    if data.get("code") != 0:
        raise RuntimeError(data)
    return data.get("data", {})


def save_user_token(state: str, token_data: Dict) -> Dict:
    """
    把 user_access_token 落盘到 data/tokens.json
    """
    store = _load_tokens()
    st = store.get("states", {}).pop(state, None)
    if not st:
        raise RuntimeError({"error": "invalid_state", "state": state})

    user_key = st.get("user_key", "me")
    now = int(time.time())
    store["users"][user_key] = _with_expire_at(token_data, now)
    _save_tokens(store)
    return store["users"][user_key]


def _with_expire_at(token_data: Dict, now: Optional[int] = None) -> Dict:
    now = now or int(time.time())
    expires_in = int(token_data.get("expires_in") or 0)
    refresh_expires_in = int(token_data.get("refresh_expires_in") or 0)

    data = {
        **token_data,
        "saved_at": now,
    }
    data["authorized_at"] = int(data.get("authorized_at") or now)
    data["auth_expire_at"] = data["authorized_at"] + USER_TOKEN_MAX_AGE_SECONDS
    if expires_in:
        data["expire_at"] = now + expires_in
    if refresh_expires_in:
        data["refresh_expire_at"] = now + refresh_expires_in
    return data


def get_user_token(app_id: str, app_secret: str, user_key: str = "me") -> Optional[str]:
    store = _load_tokens()
    u = store.get("users", {}).get(user_key)
    if not u:
        return None

    now = int(time.time())
    authorized_at = int(u.get("authorized_at") or u.get("saved_at") or 0)
    if authorized_at and now >= authorized_at + USER_TOKEN_MAX_AGE_SECONDS:
        return None

    expire_at = int(u.get("expire_at") or 0)
    if not expire_at and u.get("saved_at") and u.get("expires_in"):
        expire_at = int(u["saved_at"]) + int(u["expires_in"])

    if expire_at and now < expire_at - 300:
        return u.get("access_token")

    refresh_token = u.get("refresh_token")
    refresh_expire_at = int(u.get("refresh_expire_at") or 0)
    if not refresh_expire_at and u.get("saved_at") and u.get("refresh_expires_in"):
        refresh_expire_at = int(u["saved_at"]) + int(u["refresh_expires_in"])

    if not refresh_token:
        return None
    if refresh_expire_at and now >= refresh_expire_at - 300:
        return None

    token_data = refresh_user_token(app_id, app_secret, refresh_token)
    store["users"][user_key] = _with_expire_at({**u, **token_data}, now)
    _save_tokens(store)
    return store["users"][user_key].get("access_token")
