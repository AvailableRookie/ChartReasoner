#!/usr/bin/env python3
"""Prepare ChartReasoner annotations for public release.

The original annotation file contains private absolute image paths. This script
rewrites them to public relative placeholders under ./data/<source>/... and adds
source_image_path so users can recover the corresponding image from the original
open-source datasets. It does not copy or redistribute images.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


SOURCE_ROOT_MARKERS = {
    "evochart": ("evochart_release/", "EvoChart/"),
    "chartqa": ("ChartQA_Dataset/", "CharQA/"),
    "plotqa": ("PlotQA/",),
    "chartbench": ("ChartBench/data/",),
}


def sanitize_source(source: Any) -> str:
    text = str(source or "unknown").strip().lower()
    keep = []
    for ch in text:
        keep.append(ch if ch.isalnum() or ch in ("-", "_") else "_")
    return "".join(keep).strip("_") or "unknown"


def normalize_posix_path(path: Any) -> str:
    return str(path or "").replace("\\", "/")


def source_relative_path(original_path: Any, source: str) -> str:
    """Return the path inside the source dataset, without private prefixes."""
    path = normalize_posix_path(original_path)
    markers = SOURCE_ROOT_MARKERS.get(source, ())
    for marker in markers:
        if marker in path:
            return path.split(marker, 1)[1].lstrip("/")
    return PurePosixPath(path).name


def suffixed_relative_image_path(source: str, source_rel: str) -> str:
    """Build ./data/<source>/<path>/<stem>_<source><suffix>."""
    rel = PurePosixPath(normalize_posix_path(source_rel))
    suffix = rel.suffix or ".png"
    stem = rel.stem or "image"
    source_suffix = f"_{source}"
    filename = rel.name
    if not stem.endswith(source_suffix):
        filename = f"{stem}{source_suffix}{suffix}"
    return "./" + str(PurePosixPath("data") / source / rel.parent / filename)


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    new_record = dict(record)
    source = sanitize_source(new_record.get("data_source"))
    source_rel = source_relative_path(new_record.get("image_path"), source)
    new_record["data_source"] = source
    new_record["source_image_path"] = source_rel
    new_record["image_path"] = suffixed_relative_image_path(source, source_rel)
    return new_record


def write_jsonl_shards(
    records: list[dict[str, Any]],
    output_dir: Path,
    shard_size: int,
    prefix: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shard_paths: list[Path] = []
    for shard_index, start in enumerate(range(0, len(records), shard_size)):
        shard = records[start : start + shard_size]
        out_path = output_dir / f"{prefix}_part_{shard_index:03d}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for item in shard:
                json.dump(convert_record(item), f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")
        shard_paths.append(out_path)
    return shard_paths


def write_single_json(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    converted = [convert_record(item) for item in records]
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return output_path


def write_manifest(records: list[dict[str, Any]], output_dir: Path, files: list[Path]) -> Path:
    counts = Counter(sanitize_source(item.get("data_source")) for item in records)
    example_paths: dict[str, dict[str, str]] = {}
    for item in records:
        source = sanitize_source(item.get("data_source"))
        if source not in example_paths:
            source_rel = source_relative_path(item.get("image_path"), source)
            example_paths[source] = {
                "source_image_path": source_rel,
                "release_image_path": suffixed_relative_image_path(source, source_rel),
            }
    manifest = {
        "name": "ChartReasoner",
        "num_records": len(records),
        "data_sources": dict(sorted(counts.items())),
        "annotation_files": [str(path.relative_to(output_dir.parent)) for path in files],
        "image_policy": "Images are not redistributed. image_path is a relative placeholder under ./data/; source_image_path identifies the corresponding file inside the original open-source dataset.",
        "example_image_paths": example_paths,
    }
    out_path = output_dir / "manifest.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="Original ChartReasoner.json file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("annotations"),
        help="Directory for release annotations. Default: annotations",
    )
    parser.add_argument(
        "--format",
        choices=("jsonl", "json"),
        default="jsonl",
        help="Output format. jsonl writes sharded JSON Lines; json writes one JSON array.",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=25000,
        help="Number of records per JSONL shard. Default: 25000",
    )
    parser.add_argument(
        "--prefix",
        default="ChartReasoner",
        help="Output filename prefix. Default: ChartReasoner",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.input_json.open("r", encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        raise TypeError("Expected the input JSON to be a list of records.")

    if args.format == "jsonl":
        output_files = write_jsonl_shards(records, args.output_dir, args.shard_size, args.prefix)
    else:
        output_files = [write_single_json(records, args.output_dir / f"{args.prefix}.json")]
    manifest = write_manifest(records, args.output_dir, output_files)

    print(f"Converted {len(records)} records.")
    for path in output_files:
        print(path)
    print(manifest)


if __name__ == "__main__":
    main()
