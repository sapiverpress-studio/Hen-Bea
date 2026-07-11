import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pipeline as pipeline
from generate_production_batch import build_scenes
from run_pipeline_private import create_paid_hailuo_task

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
LOGS_DIR = OUTPUT_DIR / "logs"
MANIFESTS_DIR = OUTPUT_DIR / "manifests"
TRAINING_DIR = OUTPUT_DIR / "training_upload"
TRAINING_VIDEOS_DIR = TRAINING_DIR / "videos"
TRAINING_TEXTS_DIR = TRAINING_DIR / "texts"
TRAINING_STILLS_DIR = TRAINING_DIR / "stills"


def ensure_all_dirs():
    pipeline.ensure_dirs()
    for directory in (
        MANIFESTS_DIR,
        TRAINING_DIR,
        TRAINING_VIDEOS_DIR,
        TRAINING_TEXTS_DIR,
        TRAINING_STILLS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def save_manifest(rows, json_path, csv_path):
    json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    fieldnames = [
        "scene_id",
        "title",
        "status",
        "attempt_number",
        "quality_tier",
        "training_caption_draft",
        "image_path",
        "image_url",
        "image_host",
        "video_path",
        "video_url",
        "text_path",
        "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_scene_log(scene_id, payload):
    path = LOGS_DIR / f"{scene_id}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-successes", type=int, default=60)
    parser.add_argument("--max-attempts", type=int, default=90)
    parser.add_argument("--pause-seconds", type=int, default=20)
    args = parser.parse_args()

    ensure_all_dirs()
    scenes = build_scenes()

    manifest_rows = []
    manifest_json = MANIFESTS_DIR / "production_sweep_01_manifest.json"
    manifest_csv = MANIFESTS_DIR / "production_sweep_01_manifest.csv"

    attempts = 0
    successes = 0
    failures = 0

    for scene in scenes:
        if attempts >= args.max_attempts or successes >= args.target_successes:
            break

        attempts += 1
        scene_id = scene["scene_id"]
        print(f"=== Production attempt {attempts}/{args.max_attempts}: {scene_id} ===")

        row = {
            "scene_id": scene_id,
            "title": scene.get("title", scene_id),
            "attempt_number": attempts,
            "status": "started",
            "quality_tier": "draft_success",
            "training_caption_draft": scene.get(
                "training_caption_draft", scene.get("title", scene_id)
            ),
        }
        log_payload = {"scene": scene, "status": "started"}

        try:
            image_path, hf_result = pipeline.generate_image(scene)
            row["image_path"] = str(image_path)
            log_payload["image_path"] = str(image_path)
            log_payload["hf_result"] = hf_result
            print(f"Image saved: {image_path}")

            image_url, image_host = pipeline.upload_image(image_path, scene_id)
            row["image_url"] = image_url
            row["image_host"] = image_host
            log_payload["image_url"] = image_url
            log_payload["image_host"] = image_host
            print(f"Image available through {image_host}: {image_url}")

            task_id, creation_response = create_paid_hailuo_task(scene, image_url)
            log_payload["task_id"] = task_id
            log_payload["creation_response"] = creation_response
            print(f"Hailuo task created: {task_id}")

            task_response = pipeline.poll_hailuo_task(task_id)
            log_payload["task_response"] = task_response

            video_path, video_url = pipeline.download_video(task_response, scene_id)
            row["video_path"] = str(video_path)
            row["video_url"] = video_url
            log_payload["video_path"] = str(video_path)
            log_payload["video_url"] = video_url
            print(f"Video saved: {video_path}")

            text_path = TRAINING_TEXTS_DIR / f"{scene_id}.txt"
            text_path.write_text(
                row["training_caption_draft"].strip() + "\n", encoding="utf-8"
            )
            row["text_path"] = str(text_path)

            shutil.copy2(video_path, TRAINING_VIDEOS_DIR / video_path.name)
            shutil.copy2(image_path, TRAINING_STILLS_DIR / image_path.name)

            row["status"] = "success"
            log_payload["status"] = "success"
            successes += 1
        except Exception as exc:
            failures += 1
            row["status"] = "failed"
            row["quality_tier"] = "failed_generation"
            row["error"] = str(exc)
            log_payload["status"] = "failed"
            log_payload["error"] = str(exc)
            print(f"{scene_id} failed: {exc}")
        finally:
            log_path = write_scene_log(scene_id, log_payload)
            row["log_path"] = str(log_path)
            manifest_rows.append(row)
            save_manifest(manifest_rows, manifest_json, manifest_csv)

        if (
            attempts < args.max_attempts
            and successes < args.target_successes
            and attempts < len(scenes)
        ):
            print(f"Pausing {args.pause_seconds} seconds before the next attempt...")
            time.sleep(args.pause_seconds)

    summary = {
        "target_successes": args.target_successes,
        "max_attempts": args.max_attempts,
        "attempts_completed": attempts,
        "successes": successes,
        "failures": failures,
        "stopped_reason": (
            "target_reached"
            if successes >= args.target_successes
            else "max_attempts_or_scene_list_exhausted"
        ),
        "training_upload_dir": str(TRAINING_DIR),
        "manifest_json": str(manifest_json),
        "manifest_csv": str(manifest_csv),
    }
    (MANIFESTS_DIR / "production_sweep_01_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
