import requests

tasks = [
    {
        "user_key": "me",
        "title": "周报待填写",
        "url": "https://xxx/report"
    },
    {
        "user_key": "me",
        "title": "月报待审核",
        "url": "https://xxx/month"
    }
]

for task in tasks:
    resp = requests.post(   
        "http://127.0.0.1:5000/todo/push_link",
        json=task
    )

    print(task["title"], resp.status_code, resp.json())