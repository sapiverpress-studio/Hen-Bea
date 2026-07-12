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


def ensure_dirs():
    pipeline.ensure_dirs()
    for directory in (MANIFESTS_DIR, TRAINING_VIDEOS_DIR, TRAINING_TEXTS_DIR, TRAINING_STILLS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def save_manifest(rows, json_path, csv_path):
    json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    fields = [
        "scene_id", "title", "scene_index", "status", "quality_tier",
        "training_caption_draft", "image_path", "image_url", "image_host",
        "video_path", "video_url", "text_path", "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_log(scene_id, payload):
    path = LOGS_DIR / f"{scene_id}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--attempt-count", type=int, default=10)
    parser.add_argument("--pause-seconds", type=int, default=20)
    parser.add_argument("--stop-after-total-failures", type=int, default=5)
    parser.add_argument("--stop-after-consecutive-failures", type=int, default=3)
    parser.add_argument("--output-tag", default="batch_01")
    args = parser.parse_args()

    ensure_dirs()
    scenes = build_scenes()
    start = max(1, args.start_index)
    end = min(len(scenes), start + max(1, args.attempt_count) - 1)
    selected = list(enumerate(scenes[start - 1:end], start=start))

    rows = []
    manifest_json = MANIFESTS_DIR / f"{args.output_tag}_manifest.json"
    manifest_csv = MANIFESTS_DIR / f"{args.output_tag}_manifest.csv"
    summary_json = MANIFESTS_DIR / f"{args.output_tag}_summary.json"

    successes = 0
    failures = 0
    consecutive_failures = 0
    stop_reason = "batch_completed"

    for position, (scene_index, scene) in enumerate(selected, start=1):
        scene_id = scene["scene_id"]
        print(f"=== Batch attempt {position}/{len(selected)}: scene {scene_index} {scene_id} ===")
        row = {
            "scene_id": scene_id,
            "title": scene.get("title", scene_id),
            "scene_index": scene_index,
            "status": "started",
            "quality_tier": "draft_success",
            "training_caption_draft": scene.get("training_caption_draft", scene.get("title", scene_id)),
        }
        log = {"scene": scene, "scene_index": scene_index, "status": "started"}

        try:
            image_path, hf_result = pipeline.generate_image(scene)
            row["image_path"] = str(image_path)
            log["image_path"] = str(image_path)
            log["hf_result"] = hf_result

            image_url, image_host = pipeline.upload_image(image_path, scene_id)
            row["image_url"] = image_url
            row["image_host"] = image_host
            log["image_url"] = image_url
            log["image_host"] = image_host

            task_id, creation_response = create_paid_hailuo_task(scene, image_url)
            log["task_id"] = task_id
            log["creation_response"] = creation_response

            task_response = pipeline.poll_hailuo_task(task_id)
            log["task_response"] = task_response
            video_path, video_url = pipeline.download_video(task_response, scene_id)
            row["video_path"] = str(video_path)
            row["video_url"] = video_url
            log["video_path"] = str(video_path)
            log["video_url"] = video_url

            text_path = TRAINING_TEXTS_DIR / f"{scene_id}.txt"
            text_path.write_text(row["training_caption_draft"].strip() + "\n", encoding="utf-8")
            row["text_path"] = str(text_path)
            shutil.copy2(video_path, TRAINING_VIDEOS_DIR / video_path.name)
            shutil.copy2(image_path, TRAINING_STILLS_DIR / image_path.name)

            row["status"] = "success"
            log["status"] = "success"
            successes += 1
            consecutive_failures = 0
        except Exception as exc:
            failures += 1
            consecutive_failures += 1
            row["status"] = "failed"
            row["quality_tier"] = "failed_generation"
            row["error"] = str(exc)
            log["status"] = "failed"
            log["error"] = str(exc)
            print(f"{scene_id} failed: {exc}")
        finally:
            row["log_path"] = str(write_log(scene_id, log))
            rows.append(row)
            save_manifest(rows, manifest_json, manifest_csv)

        if failures >= args.stop_after_total_failures:
            stop_reason = "total_failure_limit_reached"
            break
        if consecutive_failures >= args.stop_after_consecutive_failures:
            stop_reason = "consecutive_failure_limit_reached"
            break
        if position < len(selected):
            time.sleep(args.pause_seconds)

    summary = {
        "output_tag": args.output_tag,
        "start_index": start,
        "requested_attempts": args.attempt_count,
        "attempts_completed": len(rows),
        "successes": successes,
        "failures": failures,
        "consecutive_failures_at_end": consecutive_failures,
        "next_start_index": start + len(rows),
        "stop_reason": stop_reason,
        "manifest_json": str(manifest_json),
        "manifest_csv": str(manifest_csv),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
