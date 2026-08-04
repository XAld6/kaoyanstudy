"""Batch-run the damage workflow on the samples pack and print a demo summary.

Usage (from repo root openclaw-damage-system):

    python scripts/demo_run.py
    python scripts/demo_run.py --samples samples --out demo_results
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from datetime import datetime  # noqa: E402

from app.reporting import build_pdf  # noqa: E402
from app.workflow import run_damage_workflow  # noqa: E402


def _iter_images(samples_dir: Path) -> list[Path]:
    files = sorted(
        p
        for p in samples_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"} and p.is_file()
    )
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="智爪识损样例批量演示")
    parser.add_argument("--samples", type=Path, default=ROOT / "samples", help="样例目录")
    parser.add_argument("--out", type=Path, default=ROOT / "demo_results", help="输出目录")
    parser.add_argument("--pdf", action="store_true", help="同时导出每张样例的 PDF 报告")
    args = parser.parse_args()

    samples_dir: Path = args.samples
    out_dir: Path = args.out
    ann_dir = out_dir / "annotated"
    pdf_dir = out_dir / "pdf"
    ann_dir.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        pdf_dir.mkdir(parents=True, exist_ok=True)

    if not samples_dir.exists():
        print(f"[error] samples dir not found: {samples_dir}")
        print("        run: python scripts/build_samples.py")
        return 1

    images = _iter_images(samples_dir)
    if not images:
        print(f"[error] no images in {samples_dir}")
        return 1

    summary_rows: list[dict] = []
    print("=" * 72)
    print("智爪识损 OpenClaw 演示批跑")
    print(f"samples: {samples_dir}")
    print(f"output : {out_dir}")
    print("=" * 72)

    for image_path in images:
        annotated_path = ann_dir / f"{image_path.stem}_annotated.png"
        try:
            result = run_damage_workflow(image_path, annotated_path)
        except Exception as exc:  # keep batch going
            print(f"[FAIL] {image_path.name}: {exc}")
            summary_rows.append({"file": image_path.name, "error": str(exc)})
            continue

        metrics = result["metrics"]
        quality = result.get("quality") if isinstance(result.get("quality"), dict) else {}
        row = {
            "file": image_path.name,
            "risk_level": result["risk_level"],
            "quality_grade": quality.get("quality_grade"),
            "quality_score": quality.get("quality_score"),
            "review_status": result["review_status"],
            "detection_count": metrics["detection_count"],
            "crack_count": metrics["crack_count"],
            "spalling_count": metrics["spalling_count"],
            "stain_count": metrics["stain_count"],
            "avg_confidence": metrics["avg_confidence"],
            "total_area_ratio": metrics["total_area_ratio"],
            "risk_reason": result["risk_reason"],
            "annotated": str(annotated_path.relative_to(ROOT)) if annotated_path.exists() else "",
            "workflow_agents": [step["agent"] for step in result["workflow"]],
        }
        summary_rows.append(row)

        if args.pdf:
            record = {
                "id": len(summary_rows),
                "filename": image_path.name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "risk_level": result["risk_level"],
                "review_status": result["review_status"],
                "detection_count": metrics["detection_count"],
                "confidence": result["confidence"],
                "risk_reason": result["risk_reason"],
                "review_note": "演示批跑自动生成",
                "metrics": metrics,
                "quality": result["quality"],
                "detections": result["detections"],
                "workflow": result["workflow"],
            }
            pdf_path = pdf_dir / f"{image_path.stem}.pdf"
            pdf_path.write_bytes(build_pdf(record))
            row["pdf"] = str(pdf_path.relative_to(ROOT))

        kinds = (
            f"裂缝{metrics['crack_count']} "
            f"剥落{metrics['spalling_count']} "
            f"渗水{metrics['stain_count']}"
        )
        qg = quality.get("quality_grade") or "-"
        qs = quality.get("quality_score")
        qs_text = f"{float(qs):.0f}" if isinstance(qs, (int, float)) else "-"
        print(
            f"{image_path.name:32s}  "
            f"风险={result['risk_level']}  "
            f"复核={result['review_status']:4s}  "
            f"候选={metrics['detection_count']:2d}  "
            f"[{kinds.strip()}]  "
            f"conf={metrics['avg_confidence']:.2f}  "
            f"质={qg}/{qs_text}"
        )

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown table for quick paste into答辩材料
    md_lines = [
        "# 演示批跑结果",
        "",
        f"> 智爪识损 v2 · 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 样例 | 风险 | 复核 | 候选 | 裂缝 | 剥落 | 渗水 | 置信度 | 质量 |",
        "|------|------|------|------|------|------|------|--------|------|",
    ]
    for row in summary_rows:
        if "error" in row:
            md_lines.append(f"| {row['file']} | ERROR | - | - | - | - | - | - | {row['error']} |")
            continue
        qg = row.get("quality_grade") or "-"
        qs = row.get("quality_score")
        qtext = f"{qg}/{float(qs):.0f}" if isinstance(qs, (int, float)) else str(qg)
        md_lines.append(
            f"| {row['file']} | {row['risk_level']} | {row['review_status']} | "
            f"{row['detection_count']} | {row['crack_count']} | {row['spalling_count']} | "
            f"{row['stain_count']} | {row['avg_confidence']:.2f} | {qtext} |"
        )
    md_path = out_dir / "summary.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("-" * 72)
    print(f"summary json: {summary_path}")
    print(f"summary md  : {md_path}")
    print(f"annotated   : {ann_dir}")
    if args.pdf:
        print(f"pdf reports : {pdf_dir}")
    print("=" * 72)

    failed = sum(1 for r in summary_rows if "error" in r)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
