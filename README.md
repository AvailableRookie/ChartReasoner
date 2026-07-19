
# ChartReasoner

ChartReasoner is a code-driven long-chain reasoning dataset for chart question answering. The release contains annotations, questions, answers, and generated reasoning traces. It does not redistribute chart images from the original open-source datasets.

## Data Sources

The annotations reference images from the following source datasets:

- EvoChart: 64,626 samples
- ChartBench: 39,473 samples
- PlotQA: 26,648 samples
- ChartQA: 16,134 samples

Total: 146,881 samples.

Each record keeps `data_source` and `source_image_path` so users can obtain the corresponding image from the original dataset. The public `image_path` field is rewritten as a relative placeholder under `./data/` and includes the source name as a filename suffix.

Example:

```json
{
  "data_source": "evochart",
  "source_image_path": "PNG/43427.png",
  "image_path": "./data/evochart/PNG/43427_evochart.png"
}
```

For ChartBench, paths preserve the nested source structure:

```json
{
  "data_source": "chartbench",
  "source_image_path": "train/area/area/chart_901/image.png",
  "image_path": "./data/chartbench/train/area/area/chart_901/image_chartbench.png"
}
```

## Files

- `annotations/ChartReasoner_part_*.jsonl`: public annotation shards.
- `annotations/manifest.json`: record counts, data-source counts, and image-path examples.
- `scripts/convert_image_paths.py`: conversion script used to rewrite private absolute image paths.
- `data/`: placeholder directory for images downloaded by users from the original datasets. Images are intentionally ignored by git.

## Annotation Fields

Each annotation record contains:

- `id`: unique sample identifier.
- `data_source`: source dataset name.
- `old_id`: original sample identifier when available.
- `image_path`: relative image placeholder under `./data/`.
- `source_image_path`: path of the corresponding image inside the original source dataset.
- `question`: chart question.
- `answer`: final answer.
- `question_type`: question/reasoning category.
- `chart_type`: chart type.
- `cot_answer`: generated final answer with reasoning-style formatting.
- `cot_reasoning`: generated long-chain reasoning trace.

## Rebuild the Release Annotations

From the repository root:

```bash
python scripts/convert_image_paths.py /path/to/ChartReasoner.json --output-dir annotations
```

This writes sharded JSONL files by default. To create a single JSON file instead:

```bash
python scripts/convert_image_paths.py /path/to/ChartReasoner.json --output-dir annotations --format json
```

The single JSON file is large and may exceed normal GitHub file-size limits. The JSONL shards are recommended for GitHub upload.

## Image Policy

We do not provide or redistribute the original chart images. Please download the images from the corresponding open-source datasets and place them under the paths indicated by `image_path`. The source suffix in each filename, such as `_evochart`, `_chartqa`, `_plotqa`, or `_chartbench`, is used to make the source explicit and avoid name collisions. Users must follow the licenses and terms of the original datasets.

## Upload

Suggested GitHub commands:

```bash
git init
git add README.md scripts annotations .gitignore data/.gitkeep
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/AvailableRookie/ChartReasoner.git
git push -u origin main
```

## Citation

If you use this dataset, please cite ChartReasoner and the original source datasets used by the referenced images.
