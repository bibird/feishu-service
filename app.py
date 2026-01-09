# app.py
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, jsonify, request
from feishu.departments import fetch_departments
from feishu.users import resolve_user_ids

app = Flask(__name__)

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

if not APP_ID or not APP_SECRET:
    raise RuntimeError("Please set FEISHU_APP_ID / FEISHU_APP_SECRET")


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
