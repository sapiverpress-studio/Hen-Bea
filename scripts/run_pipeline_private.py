import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pipeline as pipeline


def create_private_hailuo_task(scene, image_url: str):
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
        "config": {"service_mode": "private"},
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
    if not response.ok:
        raise RuntimeError(
            f"PiAPI private task creation failed ({response.status_code}): {response.text}"
        )
    body = response.json()
    task_id = body.get("data", {}).get("task_id") or body.get("task_id")
    if not task_id:
        raise RuntimeError(f"Unexpected private task creation response: {body}")
    return task_id, body


def is_transient_failure(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "internal server error",
            "status code: 500",
            "status code: 502",
            "status code: 503",
            '"code": 10000',
            "temporarily unavailable",
            "timeout",
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--video-attempts", type=int, default=2)
    args = parser.parse_args()

    pipeline.ensure_dirs()
    scenes = pipeline.load_scenes(pipeline.SCENES_FILE)
    if args.scene_id not in scenes:
        raise SystemExit(f"Unknown scene: {args.scene_id}")

    scene = scenes[args.scene_id]
    image_path, hf_result = pipeline.generate_image(scene)
    print(f"Image saved: {image_path}")

    image_url, image_host = pipeline.upload_image(image_path, scene["scene_id"])
    print(f"Image available through {image_host}: {image_url}")

    task_response = None
    task_id = None
    creation_responses = []
    failed_task_responses = []

    for attempt in range(1, args.video_attempts + 1):
        print(f"Starting paid private Hailuo attempt {attempt}/{args.video_attempts}...")
        task_id, creation_response = create_private_hailuo_task(scene, image_url)
        creation_responses.append(creation_response)
        print(f"Private Hailuo task created: {task_id}")
        try:
            task_response = pipeline.poll_hailuo_task(task_id)
            break
        except RuntimeError as exc:
            failed_task_responses.append(str(exc))
            if not is_transient_failure(exc) or attempt >= args.video_attempts:
                raise
            time.sleep(45 * attempt)

    if task_response is None:
        raise RuntimeError("No private Hailuo task completed")

    video_path, video_url = pipeline.download_video(task_response, scene["scene_id"])
    print(f"Video saved: {video_path}")

    log_path = pipeline.LOGS_DIR / f"{scene['scene_id']}.json"
    log_path.write_text(
        json.dumps(
            {
                "scene": scene,
                "service_mode": "private",
                "image_path": str(image_path),
                "image_url": image_url,
                "image_host": image_host,
                "task_id": task_id,
                "video_path": str(video_path),
                "video_url": video_url,
                "hf_result": hf_result,
                "creation_responses": creation_responses,
                "failed_task_responses": failed_task_responses,
                "task_response": task_response,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
