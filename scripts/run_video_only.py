import argparse
import json
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pipeline as pipeline
from run_pipeline_private import create_paid_hailuo_task


def validate_image_url(image_url: str) -> None:
    response = requests.get(image_url, timeout=60)
    if not response.ok:
        raise RuntimeError(
            f"Existing image URL is unavailable ({response.status_code}): {image_url}"
        )
    content_type = response.headers.get("content-type", "").lower()
    if "image" not in content_type and not response.content.startswith(b"\x89PNG"):
        raise RuntimeError(
            f"Existing URL did not return an image ({content_type or 'unknown type'}): {image_url}"
        )
    print(f"Existing still validated: {image_url}")


def write_log(scene, image_url, task_id, creation_response, task_response, video_path, video_url, error):
    log_path = pipeline.LOGS_DIR / f"{scene['scene_id']}-video-only.json"
    log_path.write_text(
        json.dumps(
            {
                "scene": scene,
                "mode": "video_only_retry",
                "service_mode": "public",
                "image_url": image_url,
                "task_id": task_id,
                "video_path": str(video_path) if video_path else None,
                "video_url": video_url,
                "creation_response": creation_response,
                "task_response": task_response,
                "error": error,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Log saved: {log_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--image-url", required=True)
    args = parser.parse_args()

    pipeline.ensure_dirs()
    scenes = pipeline.load_scenes(pipeline.SCENES_FILE)
    if args.scene_id not in scenes:
        available = ", ".join(sorted(scenes))
        raise SystemExit(f"Unknown scene: {args.scene_id}. Available: {available}")

    scene = scenes[args.scene_id]
    task_id = None
    creation_response = None
    task_response = None
    video_path = None
    video_url = None
    error = None

    try:
        validate_image_url(args.image_url)
        print("Starting one paid public Hailuo video-only attempt...")
        task_id, creation_response = create_paid_hailuo_task(scene, args.image_url)
        print(f"Hailuo task created: {task_id}")
        task_response = pipeline.poll_hailuo_task(task_id)
        video_path, video_url = pipeline.download_video(task_response, scene["scene_id"])
        print(f"Video saved: {video_path}")
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        write_log(
            scene,
            args.image_url,
            task_id,
            creation_response,
            task_response,
            video_path,
            video_url,
            error,
        )


if __name__ == "__main__":
    main()
