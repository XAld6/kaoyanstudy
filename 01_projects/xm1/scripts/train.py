from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.config import project_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a YOLO model for campus wall defects.")
    parser.add_argument("--data", default="configs/wall_defects.yaml", help="YOLO data yaml path.")
    parser.add_argument("--model", default="yolov8n.pt", help="Base YOLO model or checkpoint.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="wall_defects_yolo")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Please install YOLO dependencies first: pip install -r requirements-yolo.txt") from exc

    model = YOLO(args.model)
    model.train(
        data=str(project_path(args.data)),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(project_path("runs")),
        name=args.name,
    )
    print("Training finished. Copy the best.pt checkpoint to data/models/best.pt for web inference.")


if __name__ == "__main__":
    main()
