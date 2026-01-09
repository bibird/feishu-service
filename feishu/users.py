# feishu/users.py
import json
import os
from typing import List, Dict
from feishu.http import feishu_get
from config import USER_MAP_FILE


def resolve_user_ids(app_id: str, app_secret: str,
                     emails: List[str] = None,
                     mobiles: List[str] = None,
                     save: bool = True) -> Dict[str, Dict]:
    emails = emails or []
    mobiles = mobiles or []

    params = []
    for e in emails:
        params.append(("emails", e))
    for m in mobiles:
        params.append(("mobiles", m))

    data = feishu_get(
        "/open-apis/user/v1/batch_get_id",
        app_id,
        app_secret,
        params=params,
    )

    if data.get("code") != 0:
        raise RuntimeError(data)

    result = data.get("data", {}).get("user_list", [])

    mapping = {}
    for u in result:
        key = u.get("email") or u.get("mobile")
        mapping[key] = {
            "user_id": u.get("user_id"),
            "open_id": u.get("open_id"),
        }

    if save:
        os.makedirs(os.path.dirname(USER_MAP_FILE), exist_ok=True)
        try:
            with open(USER_MAP_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except FileNotFoundError:
            cache = {}

        cache.update(mapping)
        with open(USER_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    return mapping
