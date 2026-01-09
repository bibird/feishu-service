# feishu/http.py
import requests
from typing import Dict, Any, Optional
from feishu.auth import get_tenant_access_token


def feishu_get(path: str, app_id: str, app_secret: str,
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    token = get_tenant_access_token(app_id, app_secret)
    url = "https://open.feishu.cn" + path
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params=params or {}, timeout=20)
    resp.raise_for_status()
    return resp.json()
