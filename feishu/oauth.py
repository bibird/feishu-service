import json
import os
import time
import secrets
import requests
from typing import Dict, Optional
from config import FEISHU_HOST, DATA_DIR
from urllib.parse import urlencode

TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")


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


def save_user_token(state: str, token_data: Dict) -> Dict:
    """
    把 user_access_token 落盘到 data/tokens.json
    """
    store = _load_tokens()
    st = store.get("states", {}).pop(state, None)
    if not st:
        raise RuntimeError({"error": "invalid_state", "state": state})

    user_key = st.get("user_key", "me")
    store["users"][user_key] = {
        "saved_at": int(time.time()),
        **token_data,
    }
    _save_tokens(store)
    return store["users"][user_key]


def get_user_token(user_key: str = "me") -> Optional[str]:
    store = _load_tokens()
    u = store.get("users", {}).get(user_key)
    if not u:
        return None
    return u.get("access_token")
