import json
import os
import time

import requests

API_KEY = os.environ["PIAPI_API_KEY"]
IMAGE_URLS = [
    "https://raw.githubusercontent.com/sapiverpress-studio/Hen-Bea/main/generated-inputs/swings_001-1783752766.png",
    "https://cdn.jsdelivr.net/gh/sapiverpress-studio/Hen-Bea@main/generated-inputs/swings_001-1783752766.png",
]


def create_task(image_url: str):
    payload = {
        "model": "hailuo",
        "task_type": "video_generation",
        "input": {
            "prompt": "Two children gently swing back and forth. Keep the camera fixed and preserve the original illustration.",
            "image_url": image_url,
            "model": "v2.3-fast",
            "expand_prompt": False,
            "duration": 6,
            "resolution": 768,
        },
        "config": {"service_mode": "public"},
    }
    response = requests.post(
        "https://api.piapi.ai/api/v1/task",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    print("CREATE", image_url, response.status_code, response.text)
    response.raise_for_status()
    return response.json()["data"]["task_id"]


def poll(task_id: str):
    for _ in range(40):
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
    results = []
    for image_url in IMAGE_URLS:
        head = requests.get(image_url, timeout=60)
        print("IMAGE", image_url, head.status_code, head.headers.get("content-type"), len(head.content))
        try:
            task_id = create_task(image_url)
            result = poll(task_id)
            results.append({"image_url": image_url, "task_id": task_id, "result": result})
            if result.get("data", {}).get("status") == "completed":
                break
        except Exception as exc:
            results.append({"image_url": image_url, "error": repr(exc)})
    os.makedirs("output/diagnostic", exist_ok=True)
    with open("output/diagnostic/piapi_diagnostic.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
