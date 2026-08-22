from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.config import project_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained wall defect YOLO model.")
    parser.add_argument("--weights", default="data/models/best.pt", help="Checkpoint to evaluate.")
    parser.add_argument("--data", default="configs/wall_defects.yaml", help="YOLO data yaml path.")
    parser.add_argument("--split", default="test", choices=["val", "test"], help="Split to evaluate.")
    parser.add_argument("--imgsz", type=int, default=1280, help="Match the training image size.")
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="Device: 0 for first GPU, cpu otherwise. Default: auto.")
    parser.add_argument("--name", default="wall_defects_eval")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Please install YOLO dependencies first: pip install -r requirements-yolo.txt") from exc

    weights_path = project_path(args.weights)
    if not weights_path.exists():
        raise SystemExit(f"Weights not found: {weights_path}")

    extra_kwargs = {}
    if args.device is not None:
        extra_kwargs["device"] = args.device

    model = YOLO(str(weights_path))
    metrics = model.val(
        data=str(project_path(args.data)),
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(project_path("runs")),
        name=args.name,
        **extra_kwargs,
    )

    results = metrics.results_dict
    print("\n===== Evaluation summary =====")
    print(f"split          : {args.split}")
    print(f"mAP50-95       : {results.get('metrics/mAP50-95(B)', float('nan')):.4f}")
    print(f"mAP50          : {results.get('metrics/mAP50(B)', float('nan')):.4f}")
    print(f"precision      : {results.get('metrics/precision(B)', float('nan')):.4f}")
    print(f"recall         : {results.get('metrics/recall(B)', float('nan')):.4f}")

    save_dir = getattr(metrics, "save_dir", None)
    if save_dir is not None:
        print(f"\nPer-class breakdown, PR curves and confusion matrix saved under: {save_dir}")


if __name__ == "__main__":
    main()
