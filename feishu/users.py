# feishu/users.py

import json
import os
from typing import List, Dict, Optional
from feishu.http import feishu_get
from config import USER_MAP_FILE


def resolve_user_ids(
    app_id: str,
    app_secret: str,
    emails: Optional[List[str]] = None,
    mobiles: Optional[List[str]] = None,
    save: bool = True
) -> Dict[str, Dict]:
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

    data_block = data.get("data", {})
    mapping: Dict[str, Dict] = {}

    # 解析手机号返回
    mobile_users = data_block.get("mobile_users", {})
    for mobile, users in mobile_users.items():
        for u in users:
            mapping[mobile] = {
                "user_id": u.get("user_id"),
                "open_id": u.get("open_id"),
            }

    # 解析邮箱返回
    email_users = data_block.get("email_users", {})
    for email, users in email_users.items():
        for u in users:
            mapping[email] = {
                "user_id": u.get("user_id"),
                "open_id": u.get("open_id"),
            }

    if save:
        # Debug 输出
        # print("[user_map] file =", os.path.abspath(USER_MAP_FILE), flush=True)
        # print("[user_map] mapping size =", len(mapping), flush=True)
        # print("[user_map] mapping =", mapping, flush=True)

        os.makedirs(os.path.dirname(USER_MAP_FILE), exist_ok=True)

        try:
            with open(USER_MAP_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cache = {}

        cache.update(mapping)

        with open(USER_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    return mapping
