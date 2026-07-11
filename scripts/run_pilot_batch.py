import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
LOGS = OUTPUT / "logs"
MANIFESTS = OUTPUT / "manifests"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-file", default="prompts/pilot_batch_01.json")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=10)
    parser.add_argument("--pause-seconds", type=int, default=30)
    args = parser.parse_args()

    batch_path = ROOT / args.batch_file
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    scene_ids = batch["scene_ids"]

    start = max(1, args.start)
    end = min(len(scene_ids), args.end)
    if start > end:
        raise SystemExit(f"Invalid range: {start}-{end}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)

    selected = scene_ids[start - 1 : end]
    summary = {
        "batch_id": batch["batch_id"],
        "batch_file": str(batch_path.relative_to(ROOT)),
        "started_at": utc_now(),
        "requested_range": {"start": start, "end": end},
        "results": [],
    }

    for index, scene_id in enumerate(selected, start=start):
        print(f"\n=== Scene {index}/{end}: {scene_id} ===", flush=True)
        command = [
            sys.executable,
            str(ROOT / "scripts" / "run_pipeline_private.py"),
            "--scene-id",
            scene_id,
            "--video-attempts",
            "1",
        ]
        started = utc_now()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)

        console_path = LOGS / f"{scene_id}-console.txt"
        console_path.write_text(
            result.stdout + "\n--- STDERR ---\n" + result.stderr,
            encoding="utf-8",
        )

        video_path = OUTPUT / "videos" / f"{scene_id}.mp4"
        image_path = OUTPUT / "images" / f"{scene_id}.png"
        status = "completed" if result.returncode == 0 and video_path.exists() else "failed"

        summary["results"].append(
            {
                "index": index,
                "scene_id": scene_id,
                "status": status,
                "return_code": result.returncode,
                "started_at": started,
                "finished_at": utc_now(),
                "image_path": str(image_path.relative_to(ROOT)) if image_path.exists() else None,
                "video_path": str(video_path.relative_to(ROOT)) if video_path.exists() else None,
                "console_log": str(console_path.relative_to(ROOT)),
                "observed_caption": "",
                "review_status": "pending_review",
                "quality_score": "",
                "issues": [],
            }
        )

        manifest_path = MANIFESTS / f"{batch['batch_id']}.json"
        manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        if index < end and args.pause_seconds > 0:
            print(f"Pausing {args.pause_seconds} seconds before the next paid task.", flush=True)
            time.sleep(args.pause_seconds)

    summary["finished_at"] = utc_now()
    summary["completed_count"] = sum(r["status"] == "completed" for r in summary["results"])
    summary["failed_count"] = sum(r["status"] == "failed" for r in summary["results"])
    manifest_path = MANIFESTS / f"{batch['batch_id']}.json"
    manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"Batch finished: {summary['completed_count']} completed, "
        f"{summary['failed_count']} failed. Manifest: {manifest_path}"
    )

    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
