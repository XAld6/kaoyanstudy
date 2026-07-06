from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.sample_generator import generate_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo campus wall defect images.")
    parser.add_argument("--count", type=int, default=8, help="Number of sample images to generate.")
    args = parser.parse_args()

    paths = generate_samples(count=args.count)
    print(f"Generated {len(paths)} sample images:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
