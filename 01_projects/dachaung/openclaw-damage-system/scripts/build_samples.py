"""Generate a fixed demo sample pack for 智爪识损 presentations and regression demos."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


def _save(image: Image.Image, name: str, note: str) -> None:
    path = SAMPLES / name
    image.save(path, format="PNG")
    print(f"wrote {path.name:28s}  {note}")


def _base_rgb(
    size: tuple[int, int] = (480, 320),
    base: tuple[int, int, int] = (212, 205, 193),
    sigma: float = 9.0,
    seed: int = 42,
) -> Image.Image:
    """Fine grain concrete texture: contrast for quality checks, no large dark blobs."""
    w, h = size
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, (h, w)).astype(np.float32)
    # tiny low-frequency tilt only (keeps surface looking natural, not blotchy)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    tilt = 2.5 * np.sin(xx / 120.0) + 2.0 * np.cos(yy / 100.0)
    field = noise + tilt
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    rgb[..., 0] = np.clip(base[0] + field, 0, 255)
    rgb[..., 1] = np.clip(base[1] + field * 0.96 - 1.0, 0, 255)
    rgb[..., 2] = np.clip(base[2] + field * 0.92 - 2.5, 0, 255)
    return Image.fromarray(rgb.astype(np.uint8), mode="RGB")


def make_plain() -> Image.Image:
    return _base_rgb(sigma=9.5, seed=7)


def make_crack() -> Image.Image:
    image = _base_rgb(sigma=8.0, seed=11)
    draw = ImageDraw.Draw(image)
    draw.line([(36, 48), (120, 110), (190, 105), (280, 175), (400, 250)], fill="#121212", width=4)
    draw.line([(220, 40), (245, 95), (238, 170), (255, 240)], fill="#2a2a2a", width=2)
    return image


def make_spalling() -> Image.Image:
    # mid-tone base + clearly brighter spall island
    image = _base_rgb(base=(198, 192, 180), sigma=7.0, seed=13)
    draw = ImageDraw.Draw(image)
    draw.ellipse((140, 90, 280, 210), fill="#f6f2ea")
    draw.ellipse((165, 110, 255, 190), fill="#fcfaf6")
    draw.polygon([(150, 120), (175, 75), (230, 80), (255, 115)], fill="#f0ebe1")
    draw.arc((140, 90, 280, 210), 20, 200, fill="#8f877b", width=3)
    return image


def make_stain() -> Image.Image:
    image = _base_rgb(base=(214, 207, 195), sigma=7.0, seed=17)
    draw = ImageDraw.Draw(image)
    draw.ellipse((100, 70, 300, 240), fill="#5a4a38")
    draw.ellipse((130, 100, 270, 210), fill="#4a3c2c")
    draw.ellipse((160, 120, 240, 180), fill="#403426")
    return image


def make_mixed() -> Image.Image:
    image = _base_rgb(base=(200, 194, 182), sigma=7.0, seed=19)
    draw = ImageDraw.Draw(image)
    # dark wet stain
    draw.ellipse((280, 40, 430, 180), fill="#514132")
    # crack
    draw.line([(40, 50), (130, 120), (200, 115), (310, 210), (420, 280)], fill="#101010", width=4)
    # bright spalling island (large enough for geometry gates)
    draw.ellipse((50, 160, 180, 280), fill="#f6f2ea")
    draw.ellipse((70, 180, 160, 260), fill="#fcfaf6")
    return image


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)

    _save(make_plain(), "01_plain_surface.png", "正常墙面（期望低风险/无候选）")
    _save(make_crack(), "02_crack_synthetic.png", "合成裂缝（期望 crack）")
    _save(make_spalling(), "03_spalling_synthetic.png", "合成剥落（期望 spalling）")
    _save(make_stain(), "04_stain_synthetic.png", "合成渗水/色差（期望 stain）")
    _save(make_mixed(), "05_mixed_damage.png", "混合病害（多类型）")

    for src_name, dst_name, note in (
        ("sample-crack.png", "06_sample_crack.png", "项目内置裂缝样例"),
        ("demo-concrete-crack.png", "07_demo_concrete_crack.png", "混凝土裂缝展示图"),
    ):
        src = ROOT / src_name
        if src.exists():
            shutil.copy2(src, SAMPLES / dst_name)
            print(f"copied {dst_name:28s}  {note}")
        else:
            print(f"skip   {dst_name:28s}  missing {src_name}")

    (SAMPLES / "README.md").write_text(
        """# 演示样例包 samples/

用于答辩演示、回归验证和 `scripts/demo_run.py` 批量跑通。

| 文件 | 场景 | 建议讲解点 |
|------|------|------------|
| `01_plain_surface.png` | 正常表面 | 无显著病害 → 低风险/自动通过 |
| `02_crack_synthetic.png` | 合成裂缝 | 线状候选、红色标注 |
| `03_spalling_synthetic.png` | 合成剥落 | 块状亮斑、橙色标注 |
| `04_stain_synthetic.png` | 合成渗水/色差 | 暗湿斑、蓝色标注 |
| `05_mixed_damage.png` | 混合病害 | 多类型 metrics + 较高风险 |
| `06_sample_crack.png` | 内置裂缝样例 | 快速上传验证 |
| `07_demo_concrete_crack.png` | 混凝土展示图 | 标注图 + PDF 报告演示 |

重新生成合成图：

```powershell
python scripts/build_samples.py
```
""",
        encoding="utf-8",
    )
    print(f"wrote {SAMPLES / 'README.md'}")


if __name__ == "__main__":
    main()
