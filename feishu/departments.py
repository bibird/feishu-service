# feishu/departments.py
from typing import List, Dict
from feishu.http import feishu_get
from config import MAX_PAGE_SIZE


def fetch_departments(app_id: str, app_secret: str) -> List[Dict]:
    path = "/open-apis/contact/v3/departments"
    params = {"page_size": MAX_PAGE_SIZE}
    items = []

    while True:
        data = feishu_get(path, app_id, app_secret, params)
        if data.get("code") != 0:
            raise RuntimeError(data)

        block = data.get("data") or {}
        items.extend(block.get("items") or [])

        if not block.get("has_more"):
            break
        params["page_token"] = block.get("page_token")

    return items
