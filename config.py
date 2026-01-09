# config.py
import os

FEISHU_HOST = "https://open.feishu.cn"
MAX_PAGE_SIZE = 50

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USER_MAP_FILE = os.path.join(DATA_DIR, "user_map.json")
