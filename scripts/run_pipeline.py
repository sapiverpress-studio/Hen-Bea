import argparse
import base64
import json
import os
import shutil
import sys
import time
from pathlib import Path

import requests
from gradio_client import Client

ROOT = Path(__file__).resolve().parents[1]
SCENES_FILE = ROOT / "prompts" / "scenes.json"
OUTPUT_DIR = ROOT / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
VIDEOS_DIR = OUTPUT_DIR / "videos"
LOGS_DIR = OUTPUT_DIR / "logs"


def load_scenes(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {item["scene_id"]: item for item in data}
    if isinstance(data, dict) and "scenes" in data:
        return {item["scene_id"]: item for item in data["scenes"]}
    raise ValueError("scenes.json must be a list or an object with a 'scenes' key")


def ensure_dirs():
    for directory in (IMAGES_DIR, VIDEOS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def extract_image_path(result):
    if isinstance(result, (list, tuple)) and result:
        return extract_image_path(result[0])
    if isinstance(result, dict):
        for key in ("path", "name"):
            if result.get(key):
                return str(result[key])
    if isinstance(result, str):
        return result
    raise RuntimeError(f"Could not find image path in result: {result!r}")


def generate_image(scene):
    client = Client(
        os.getenv("HF_SPACE_ID", "sapiverpress/hen-bea-generator"),
        hf_token=os.getenv("HF_TOKEN") or None,
    )

    args = (
        scene["image_prompt"],
        float(scene.get("lora_strength", 0.9)),
        int(scene.get("steps", 9)),
        int(scene.get("width", 768)),
        int(scene.get("height", 768)),
        int(scene.get("seed", -1)),
    )

    candidates = [name for name in [os.getenv("HF_API_NAME"), "/generate_image", "/predict"] if name]
    result = None
    last_error = None
    for api_name in candidates:
        try:
            result = client.predict(*args, api_name=api_name)
            break
        except Exception as exc:
            last_error = exc

    if result is None:
        raise RuntimeError(f"Hugging Face generation failed: {last_error}")

    source = Path(extract_image_path(result))
    if not source.exists():
        raise RuntimeError(f"Generated image path does not exist: {source}")

    destination = IMAGES_DIR / f"{scene['scene_id']}.png"
    shutil.copy2(source, destination)
    return destination, result


def upload_image_to_piapi(image_path: Path):
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    response = requests.post(
        "https://upload.theapi.app/api/ephemeral_resource",
        headers={
            "x-api-key": os.environ["PIAPI_API_KEY"],
            "Content-Type": "application/json",
        },
        json={
            "file_name": image_path.name,
            "file_data": f"data:image/png;base64,{encoded}",
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        return payload["data"]["url"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected upload response: {payload}") from exc


def create_hailuo_task(scene, image_url: str):
    payload = {
        "model": "hailuo",
        "task_type": "video_generation",
        "input": {
            "prompt": scene["video_prompt"],
            "image_url": image_url,
            "model": scene.get("video_model", "v2.3-fast"),
            "expand_prompt": bool(scene.get("expand_prompt", True)),
            "duration": int(scene.get("duration", 6)),
            "resolution": int(scene.get("resolution", 768)),
        },
        "config": {"service_mode": "public"},
    }

    response = requests.post(
        "https://api.piapi.ai/api/v1/task",
        headers={
            "x-api-key": os.environ["PIAPI_API_KEY"],
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    task_id = body.get("data", {}).get("task_id") or body.get("task_id")
    if not task_id:
        raise RuntimeError(f"Unexpected task creation response: {body}")
    return task_id, body


def poll_hailuo_task(task_id: str):
    deadline = time.time() + int(os.getenv("POLL_TIMEOUT_SECONDS", "1200"))
    interval = int(os.getenv("POLL_SECONDS", "15"))
    last = None

    while time.time() < deadline:
        response = requests.get(
            f"https://api.piapi.ai/api/v1/task/{task_id}",
            headers={"x-api-key": os.environ["PIAPI_API_KEY"]},
            timeout=60,
        )
        response.raise_for_status()
        last = response.json()
        status = last.get("data", {}).get("status", "unknown")
        print(f"PiAPI status: {status}")

        if status == "completed":
            return last
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError(json.dumps(last, indent=2))
        time.sleep(interval)

    raise TimeoutError(f"Timed out waiting for {task_id}: {json.dumps(last, indent=2) if last else 'no response'}")


def download_video(task_response, scene_id: str):
    video_url = task_response.get("data", {}).get("output", {}).get("video")
    if not video_url:
        raise RuntimeError(f"No video URL found: {task_response}")

    destination = VIDEOS_DIR / f"{scene_id}.mp4"
    with requests.get(video_url, stream=True, timeout=180) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)
    return destination, video_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-id", required=True)
    args = parser.parse_args()

    ensure_dirs()
    scenes = load_scenes(SCENES_FILE)
    if args.scene_id not in scenes:
        print(f"Unknown scene: {args.scene_id}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(scenes))}", file=sys.stderr)
        raise SystemExit(2)

    scene = scenes[args.scene_id]
    image_path, hf_result = generate_image(scene)
    print(f"Image saved: {image_path}")

    image_url = upload_image_to_piapi(image_path)
    print(f"Image uploaded: {image_url}")

    task_id, creation_response = create_hailuo_task(scene, image_url)
    print(f"Hailuo task created: {task_id}")

    task_response = poll_hailuo_task(task_id)
    video_path, video_url = download_video(task_response, scene["scene_id"])
    print(f"Video saved: {video_path}")

    log_path = LOGS_DIR / f"{scene['scene_id']}.json"
    log_path.write_text(
        json.dumps(
            {
                "scene": scene,
                "image_path": str(image_path),
                "image_url": image_url,
                "task_id": task_id,
                "video_path": str(video_path),
                "video_url": video_url,
                "hf_result": hf_result,
                "creation_response": creation_response,
                "task_response": task_response,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Log saved: {log_path}")


if __name__ == "__main__":
    main()
