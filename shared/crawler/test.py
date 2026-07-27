import json
from pathlib import Path
import requests
# ====== CẤU HÌNH ======
TASK_ID = "08a3bcc5-611f-429c-b2d7-ca3e5fec7baf"
WORKER_ID = "manual-test"
URL = "http://localhost:8000/workers/complete-task"

# Dán truyện vào file này
INPUT_FILE = r"C:\Users\HLC\PycharmProjects\distributed-video-system-worker\shared\crawler\transalted.txt"

# File json sinh ra
OUTPUT_FILE = "payload.json"

# ======================

text = Path(INPUT_FILE).read_text(encoding="utf-8")

payload = {
    "worker_id": WORKER_ID,
    "task_id": TASK_ID,
    "result": {
        "translated_text": text
    },
    "output_path": None,
    "manifest_path": None,
    "resource_metrics": {}
}

Path(OUTPUT_FILE).write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

response = requests.post(
    URL,
    json=payload,
    timeout=300,
)

print("Status:", response.status_code)

try:
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except Exception:
    print(response.text)

response.raise_for_status()