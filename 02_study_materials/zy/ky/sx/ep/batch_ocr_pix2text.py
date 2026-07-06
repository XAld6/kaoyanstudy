from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import fitz
from pix2text import Pix2Text


ROOT = Path(__file__).resolve().parent

PDFS = [
    ("gaoshu", ROOT / "【A4留白】27ep-高数数一讲义例题做题本.pdf"),
    ("xiandai", ROOT / "【A4留白】27ep线代讲义例题做题本.pdf"),
]

OUT_ROOT = ROOT / "ocr"


def safe_text(value) -> str:
    return "" if value is None else str(value)


def element_to_dict(element) -> dict:
    data = getattr(element, "data", None)
    if isinstance(data, dict):
        box = data.get("box")
        text = data.get("text")
        element_type = safe_text(data.get("type"))
        score = data.get("score")
    else:
        box = getattr(element, "box", None)
        text = getattr(element, "text", "")
        element_type = safe_text(getattr(element, "type", ""))
        score = getattr(element, "score", None)
    return {
        "box": list(map(int, box)) if box is not None else None,
        "text": safe_text(text),
        "type": element_type,
        "score": float(score) if isinstance(score, (int, float)) else None,
    }


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def ocr_one_pdf(p2t: Pix2Text, slug: str, pdf_path: Path, start_page: int = 1, end_page: int | None = None) -> None:
    out_dir = OUT_ROOT / slug
    page_dir = out_dir / "pages"
    image_dir = out_dir / "images"
    page_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    last_page = end_page or doc.page_count
    manifest = {
        "slug": slug,
        "pdf": str(pdf_path),
        "page_count": doc.page_count,
        "start_page": start_page,
        "end_page": last_page,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    for page_no in range(start_page, last_page + 1):
        json_path = page_dir / f"page_{page_no:03d}.json"
        md_path = page_dir / f"page_{page_no:03d}.md"
        image_path = image_dir / f"page_{page_no:03d}.png"
        if json_path.exists() and md_path.exists():
            print(f"[skip] {slug} page {page_no}/{doc.page_count}", flush=True)
            continue

        page = doc[page_no - 1]
        if not image_path.exists():
            pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
            pix.save(image_path)

        print(f"[ocr] {slug} page {page_no}/{doc.page_count}", flush=True)
        result = p2t.recognize(
            str(image_path),
            file_type="page",
            resized_shape=1200,
            return_text=False,
            auto_line_break=True,
        )
        try:
            markdown = result.to_markdown()
        except Exception:
            markdown = "\n\n".join(element_to_dict(e)["text"] for e in getattr(result, "elements", []))
        elements = [element_to_dict(e) for e in getattr(result, "elements", [])]
        payload = {
            "slug": slug,
            "pdf_page": page_no,
            "image": str(image_path),
            "markdown": normalize_markdown(markdown),
            "elements": elements,
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(payload["markdown"], encoding="utf-8")
        print(f"[done] {slug} page {page_no}: {len(elements)} elements", flush=True)


def main(argv: list[str]) -> int:
    start_page = int(argv[1]) if len(argv) > 1 else 1
    end_page = int(argv[2]) if len(argv) > 2 else None
    which = argv[3] if len(argv) > 3 else "all"

    p2t = Pix2Text(device="cpu")
    for slug, pdf_path in PDFS:
        if which != "all" and slug != which:
            continue
        ocr_one_pdf(p2t, slug, pdf_path, start_page=start_page, end_page=end_page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
