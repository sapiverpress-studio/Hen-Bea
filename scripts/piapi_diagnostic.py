import json
import os
import time

import requests

API_KEY = os.environ["PIAPI_API_KEY"]
IMAGE_URL = "https://cdn.jsdelivr.net/gh/sapiverpress-studio/Hen-Bea@main/generated-inputs/swings_001-1783752766.png"


def create_task():
    payload = {
        "model": "hailuo",
        "task_type": "video_generation",
        "input": {
            "prompt": "Two children gently swing back and forth. Keep the camera fixed and preserve the original illustration.",
            "image_url": IMAGE_URL,
            "model": "v2.3-fast",
            "expand_prompt": False,
            "duration": 6,
            "resolution": 768,
        },
        "config": {"service_mode": "private"},
    }
    response = requests.post(
        "https://api.piapi.ai/api/v1/task",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    print("CREATE", response.status_code, response.text)
    response.raise_for_status()
    return response.json()["data"]["task_id"]


def poll(task_id: str):
    for _ in range(80):
        response = requests.get(
            f"https://api.piapi.ai/api/v1/task/{task_id}",
            headers={"x-api-key": API_KEY},
            timeout=60,
        )
        print("POLL", task_id, response.status_code, response.text)
        response.raise_for_status()
        body = response.json()
        status = body.get("data", {}).get("status")
        if status in {"completed", "failed", "error", "cancelled"}:
            return body
        time.sleep(15)
    raise TimeoutError(task_id)


def main():
    image = requests.get(IMAGE_URL, timeout=60)
    print("IMAGE", image.status_code, image.headers.get("content-type"), len(image.content))
    result = {"image_url": IMAGE_URL, "service_mode": "private"}
    try:
        task_id = create_task()
        result["task_id"] = task_id
        result["result"] = poll(task_id)
    except Exception as exc:
        result["error"] = repr(exc)

    os.makedirs("output/diagnostic", exist_ok=True)
    with open("output/diagnostic/piapi_private_diagnostic.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, default=str)
    print(json.dumps(result, indent=2, default=str))

    status = result.get("result", {}).get("data", {}).get("status")
    if status != "completed":
        raise SystemExit("Private-mode PiAPI diagnostic did not complete")


if __name__ == "__main__":
    main()
