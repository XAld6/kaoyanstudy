from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.config import project_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a YOLO model for campus wall defects.")
    parser.add_argument("--data", default="configs/wall_defects.yaml", help="YOLO data yaml path.")
    parser.add_argument("--model", default="yolov8s.pt", help="Base YOLO model or checkpoint.")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=1280, help="Cracks are thin targets; prefer >=1280 when VRAM allows.")
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="Device: 0 for first GPU, cpu otherwise. Default: auto.")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--patience", type=int, default=30, help="Early stopping patience.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", default="wall_defects_yolo")
    parser.add_argument(
        "--copy-best",
        action="store_true",
        help="Copy best.pt to data/models/best.pt after training so the web app picks it up.",
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Please install YOLO dependencies first: pip install -r requirements-yolo.txt") from exc

    # Crack-oriented augmentation: cracks are thin, low-saturation structures.
    # - close_mosaic: disable mosaic early so fine line features are not distorted late in training.
    # - hsv_s/hsv_v lowered: color jitter hurts gray-ish crack contrast.
    extra_kwargs = {}
    if args.device is not None:
        extra_kwargs["device"] = args.device

    model = YOLO(args.model)
    model.train(
        data=str(project_path(args.data)),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        patience=args.patience,
        seed=args.seed,
        project=str(project_path("runs")),
        name=args.name,
        close_mosaic=15,
        hsv_s=0.3,
        hsv_v=0.4,
        fliplr=0.5,
        flipud=0.0,
        degrees=2.0,
        translate=0.1,
        scale=0.3,
        **extra_kwargs,
    )

    best_weights = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"Training finished. Best checkpoint: {best_weights}")
    if args.copy_best and best_weights.exists():
        target = project_path("data/models/best.pt")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(best_weights, target)
        print(f"Copied best weights to {target}. Restart the service to switch to the YOLO engine.")
    else:
        print("Copy best.pt to data/models/best.pt (or retrain with --copy-best) for web inference.")


if __name__ == "__main__":
    main()
