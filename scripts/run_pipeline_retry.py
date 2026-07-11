import argparse
import json
import time

from scripts import run_pipeline as pipeline


def is_transient_piapi_failure(exc: Exception) -> bool:
    text = str(exc).lower()
    transient_markers = (
        "internal server error",
        "status code: 500",
        "status code: 502",
        "status code: 503",
        '"code": 10000',
        "temporarily unavailable",
        "timeout",
    )
    return any(marker in text for marker in transient_markers)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--video-attempts", type=int, default=4)
    args = parser.parse_args()

    pipeline.ensure_dirs()
    scenes = pipeline.load_scenes(pipeline.SCENES_FILE)
    if args.scene_id not in scenes:
        available = ", ".join(sorted(scenes))
        raise SystemExit(f"Unknown scene: {args.scene_id}. Available: {available}")

    scene = scenes[args.scene_id]

    image_path, hf_result = pipeline.generate_image(scene)
    print(f"Image saved: {image_path}")

    image_url, image_host = pipeline.upload_image(image_path, scene["scene_id"])
    print(f"Image available through {image_host}: {image_url}")

    creation_responses = []
    failed_task_responses = []
    task_id = None
    task_response = None

    for attempt in range(1, args.video_attempts + 1):
        print(f"Starting Hailuo attempt {attempt}/{args.video_attempts}...")
        task_id, creation_response = pipeline.create_hailuo_task(scene, image_url)
        creation_responses.append(creation_response)
        print(f"Hailuo task created: {task_id}")

        try:
            task_response = pipeline.poll_hailuo_task(task_id)
            break
        except RuntimeError as exc:
            failed_task_responses.append(str(exc))
            if not is_transient_piapi_failure(exc) or attempt >= args.video_attempts:
                raise

            wait_seconds = 30 * attempt
            print(
                "PiAPI returned a temporary internal error. "
                f"Retrying with a fresh task in {wait_seconds} seconds."
            )
            time.sleep(wait_seconds)

    if task_response is None:
        raise RuntimeError("No Hailuo task completed successfully")

    video_path, video_url = pipeline.download_video(task_response, scene["scene_id"])
    print(f"Video saved: {video_path}")

    log_path = pipeline.LOGS_DIR / f"{scene['scene_id']}.json"
    log_path.write_text(
        json.dumps(
            {
                "scene": scene,
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
    print(f"Log saved: {log_path}")


if __name__ == "__main__":
    main()
