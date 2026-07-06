from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from models.detector import WallDefectDetector
from utils.config import load_settings, project_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run wall defect detection on one image.")
    parser.add_argument("image", help="Input image path.")
    parser.add_argument("--output", help="Output annotated image path.")
    args = parser.parse_args()

    settings = load_settings()
    image_path = project_path(args.image)
    output_path = project_path(args.output) if args.output else project_path(settings["paths"]["results_dir"]) / f"{image_path.stem}_result.jpg"
    detector = WallDefectDetector(settings)
    result = detector.predict(image_path, output_path)

    print(
        json.dumps(
            {
                "engine": result.engine,
                "overall_risk": result.overall_risk,
                "result_image_path": str(result.result_image_path),
                "detections": result.detections,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
