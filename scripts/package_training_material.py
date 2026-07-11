import argparse
import csv
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = {"accept", "accept_relabelled", "trim_then_accept"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-name", default="hen_bea_training_material")
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pack_root = ROOT / "output" / "training_pack" / args.output_name
    if pack_root.exists():
        shutil.rmtree(pack_root)

    videos_dir = pack_root / "videos"
    stills_dir = pack_root / "stills"
    labels_dir = pack_root / "labels"
    logs_dir = pack_root / "logs"
    for directory in (videos_dir, stills_dir, labels_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows = []
    rejected = []

    for item in manifest.get("results", []):
        status = item.get("review_status", "pending_review")
        caption = str(item.get("observed_caption", "")).strip()
        scene_id = item["scene_id"]

        if status not in ACCEPTED or not caption:
            rejected.append({"scene_id": scene_id, "review_status": status, "reason": "Not accepted or missing observed caption"})
            continue

        video_source = ROOT / str(item.get("video_path", ""))
        image_source = ROOT / str(item.get("image_path", ""))
        console_source = ROOT / str(item.get("console_log", ""))
        if not video_source.is_file():
            rejected.append({"scene_id": scene_id, "review_status": status, "reason": "Video file missing"})
            continue

        video_dest = videos_dir / f"{scene_id}.mp4"
        shutil.copy2(video_source, video_dest)
        if image_source.is_file():
            shutil.copy2(image_source, stills_dir / f"{scene_id}.png")
        if console_source.is_file():
            shutil.copy2(console_source, logs_dir / f"{scene_id}-console.txt")

        (labels_dir / f"{scene_id}.txt").write_text(caption + "\n", encoding="utf-8")
        rows.append(
            {
                "scene_id": scene_id,
                "video": f"videos/{scene_id}.mp4",
                "still": f"stills/{scene_id}.png" if image_source.is_file() else "",
                "label": f"labels/{scene_id}.txt",
                "observed_caption": caption,
                "review_status": status,
                "quality_score": item.get("quality_score", ""),
                "issues": "|".join(item.get("issues", [])),
            }
        )

    with (pack_root / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scene_id", "video", "still", "label", "observed_caption", "review_status", "quality_score", "issues"])
        writer.writeheader()
        writer.writerows(rows)

    (pack_root / "manifest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (pack_root / "rejected.json").write_text(json.dumps(rejected, indent=2), encoding="utf-8")
    (pack_root / "README.txt").write_text(
        "Hen & Bea truth-labelled video training material.\n"
        "Every caption describes the observed video rather than merely repeating the generation prompt.\n",
        encoding="utf-8",
    )

    zip_path = pack_root.parent / f"{args.output_name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in pack_root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(pack_root.parent))

    print(f"Packaged {len(rows)} accepted clips: {zip_path}")
    print(f"Excluded {len(rejected)} clips. See rejected.json.")


if __name__ == "__main__":
    main()
