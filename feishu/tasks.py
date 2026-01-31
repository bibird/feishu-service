import requests
from typing import Dict, Any
from config import FEISHU_HOST


def create_task_with_link(user_access_token: str, title: str, url: str) -> Dict[str, Any]:
    """
    创建一个任务/代办，并把网页链接放进描述里（或自定义字段里）
    """
    api = f"{FEISHU_HOST}/open-apis/task/v2/tasks"  # 常见写法之一
    headers = {"Authorization": f"Bearer {user_access_token}"}

    payload = {
        "summary": title,
        "description": f"报表链接：{url}",
    }

    resp = requests.post(api, headers=headers, json=payload, timeout=20)
    # 不直接 raise，检查错误体
    try:
        data = resp.json()
    except Exception:
        data = {"http_status": resp.status_code, "text": resp.text}

    return {"http_status": resp.status_code, "data": data}
