from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "jglx_final_overleaf_upload_clean"
FIGURES = PROJECT / "figures"
SECTIONS = PROJECT / "sections"
OUT_CSV = ROOT / "strict_retype_figure_audit.csv"
OUT_JSON = ROOT / "strict_retype_figure_audit.json"


def collect_references() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{figures/([^}]+)\}")
    for tex in sorted(SECTIONS.glob("*.tex")):
        for idx, line in enumerate(tex.read_text(encoding="utf-8").splitlines(), start=1):
            for match in pattern.finditer(line):
                refs.setdefault(match.group(1), []).append(f"{tex.name}:{idx}")
    return refs


def image_stats(path: Path) -> dict[str, float | int]:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"width": 0, "height": 0, "ink_ratio": 0.0, "blue_red_ratio": 0.0}
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = gray < 245
    ink_ratio = float(ink.mean())
    b, g, r = cv2.split(img)
    colored = ((r.astype(np.int16) - g.astype(np.int16) > 35) | (b.astype(np.int16) - g.astype(np.int16) > 35)) & ink
    blue_red_ratio = float(colored.mean())
    return {"width": w, "height": h, "ink_ratio": ink_ratio, "blue_red_ratio": blue_red_ratio}


def classify(text: str, stats: dict[str, float | int]) -> str:
    text_len = len(text)
    colored = float(stats["blue_red_ratio"])
    if colored > 0.015:
        return "handwritten_or_colored_note"
    if text_len > 260:
        return "text_heavy_convert_to_latex"
    if text_len > 80:
        return "mixed_text_and_diagram"
    return "diagram_heavy_redraw_or_crop"


def write_outputs(rows: list[dict[str, str | int | float]]) -> None:
    if not rows:
        return
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    refs = collect_references()
    ocr = RapidOCR()
    existing: dict[str, dict[str, str | int | float]] = {}
    if args.resume and OUT_JSON.exists():
        for row in json.loads(OUT_JSON.read_text(encoding="utf-8")):
            existing[str(row["figure"])] = row

    rows = [existing[k] for k in sorted(existing)]
    all_images = [p for p in sorted(FIGURES.glob("*")) if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    selected = all_images[args.offset :]
    if args.limit:
        selected = selected[: args.limit]

    for idx, image in enumerate(selected, start=1):
        if image.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        if image.name in existing:
            continue
        result, _ = ocr(str(image))
        pieces = []
        confidences = []
        if result:
            for _, text, conf in result:
                pieces.append(text)
                confidences.append(float(conf))
        text = "\n".join(pieces)
        stats = image_stats(image)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        row = {
            "figure": image.name,
            "references": ";".join(refs.get(image.name, [])),
            "text_len": len(text),
            "ocr_items": len(pieces),
            "avg_conf": round(avg_conf, 4),
            "ink_ratio": round(float(stats["ink_ratio"]), 5),
            "blue_red_ratio": round(float(stats["blue_red_ratio"]), 5),
            "class": classify(text, stats),
            "ocr_preview": text.replace("\n", " ")[:220],
        }
        rows.append(row)
        rows.sort(key=lambda r: str(r["figure"]))
        write_outputs(rows)
        print(f"[{idx}/{len(selected)}] {image.name}: {row['class']} len={row['text_len']}")

    summary: dict[str, int] = {}
    for row in rows:
        summary[row["class"]] = summary.get(row["class"], 0) + 1
    print(json.dumps({"figures": len(rows), "summary": summary, "csv": str(OUT_CSV)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
