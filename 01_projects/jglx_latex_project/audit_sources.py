import os
import re
import json
from pathlib import Path

try:
    import fitz
except Exception as e:
    raise SystemExit(f"pymupdf import failed: {e}")

root = Path(r"D:/xm/zy/jglx")
source_dirs = [root / "6.作业&答案", root / "7.作业讲解笔记"]
editable_exts = {".doc", ".docx", ".ppt", ".pptx", ".md", ".tex", ".html", ".htm"}
pdf_paths = []
editable = []
for base in source_dirs:
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if path.is_file():
            if path.suffix.lower() == ".pdf":
                pdf_paths.append(path)
            if path.suffix.lower() in editable_exts:
                editable.append(path)

rows = []
for path in sorted(pdf_paths, key=lambda p: str(p)):
    try:
        doc = fitz.open(path)
    except Exception as e:
        rows.append({"file": str(path), "error": str(e)})
        continue
    pages = len(doc)
    text_chars = 0
    text_pages = 0
    image_pages = 0
    numbered_hits = 0
    sample = ""
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        chars = len(text.strip())
        text_chars += chars
        if chars > 80:
            text_pages += 1
        if page.get_images(full=True):
            image_pages += 1
        numbered_hits += len(re.findall(r"(?:^|\n)\s*(?:\d+|[一二三四五六七八九十]+)[\.、)]", text))
        if not sample and text.strip():
            sample = " ".join(text.split())[:160]
    rows.append({
        "file": str(path.relative_to(root)),
        "pages": pages,
        "text_chars": text_chars,
        "text_pages_gt80": text_pages,
        "image_pages": image_pages,
        "numbered_hits": numbered_hits,
        "sample": sample,
    })

total_pages = sum(r.get("pages", 0) for r in rows)
total_text = sum(r.get("text_chars", 0) for r in rows)
print("EDITABLE_COUNT", len(editable))
for p in editable:
    print("EDITABLE", p.relative_to(root))
print("PDF_COUNT", len(rows))
print("TOTAL_PAGES", total_pages)
print("TOTAL_TEXT_CHARS", total_text)
print("JSON_START")
print(json.dumps(rows, ensure_ascii=False, indent=2))
