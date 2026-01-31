from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, jsonify, request, redirect
from feishu.departments import fetch_departments
from feishu.users import resolve_user_ids
from feishu.oauth import new_state, build_auth_url, exchange_code_for_user_token, save_user_token, get_user_token
from feishu.tasks import create_task_with_link
import logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
REDIRECT_URI = os.getenv("FEISHU_REDIRECT_URI", "http://127.0.0.1:5000/oauth/callback")

if not APP_ID or not APP_SECRET:
    raise RuntimeError("Please set FEISHU_APP_ID / FEISHU_APP_SECRET")


@app.get("/oauth/start")
def oauth_start():
    # 可以替换成成具体员工，比如 "me" / "zhangsan" / employee_id
    user_key = request.args.get("user_key", "me")
    state = new_state(user_key=user_key)

    #print("[oauth_start] user_key =", user_key, flush=True) 检查授权对象
    #print("[oauth_start] state =", state, flush=True) CSRF 身份校验
    #print("[oauth_start] REDIRECT_URI =", REDIRECT_URI, flush=True) 重定向URL地址

    url = build_auth_url(APP_ID, REDIRECT_URI, state)

    # print("[oauth_start] redirect to =", url, flush=True) 确认拼接结果

    return redirect(url)


@app.get("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return jsonify({"ok": False, "error": "missing code/state", "args": dict(request.args)}), 400

    token_data = exchange_code_for_user_token(APP_ID, APP_SECRET, code)
    saved = save_user_token(state, token_data)
    # 成功后返回一个提示页
    return jsonify({"ok": True, "saved": {k: saved.get(k) for k in ["open_id", "user_id", "expires_in", "token_type"]}})


@app.post("/todo/push_link")
def todo_push_link():
    """
    用已授权的 user_access_token 发一个“代办/任务”，描述里带网页链接
    body: { "title": "...", "url": "https://..." , "user_key": "me" }
    """
    body = request.get_json(force=True)
    title = body.get("title", "外部报表推送")
    url = body.get("url")
    user_key = body.get("user_key", "me")

    if not url:
        return jsonify({"ok": False, "error": "missing url"}), 400

    token = get_user_token(user_key=user_key)
    if not token:
        return jsonify({"ok": False, "error": "no user token, open /oauth/start first"}), 400

    result = create_task_with_link(token, title=title, url=url)
    return jsonify({"ok": True, **result})

@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/departments")
def departments():
    items = fetch_departments(APP_ID, APP_SECRET)
    return jsonify({"count": len(items), "items": items})


@app.post("/resolve_user_ids")
def resolve_users():
    body = request.get_json(force=True)
    mapping = resolve_user_ids(
        APP_ID,
        APP_SECRET,
        emails=body.get("emails"),
        mobiles=body.get("mobiles"),
        save=body.get("save_to_file", True),
    )
    return jsonify(mapping)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
