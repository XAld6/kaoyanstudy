import hashlib
import json
import re
from pathlib import Path
import fitz

root = Path(r"D:/xm/zy/jglx")
source_dirs = [root / "6.作业&答案", root / "7.作业讲解笔记"]

def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def chapter_of(name):
    m = re.search(r"第(\d+)次", name)
    return int(m.group(1)) if m else None

def kind_of(path):
    s = str(path)
    if "作业讲解笔记" in s:
        return "讲解笔记"
    if "作业答案" in s:
        return "答案"
    if "作业及答案" in s:
        return "作业及答案"
    if "作业" in s:
        return "作业题目"
    return "其他"

seen = {}
records = []
for base in source_dirs:
    for p in sorted(base.glob("*.pdf")):
        ch = chapter_of(p.name)
        if ch is None or ch > 14:
            continue
        sha = file_hash(p)
        if sha in seen:
            duplicate_of = seen[sha]
            duplicate = True
        else:
            seen[sha] = str(p.relative_to(root))
            duplicate_of = ""
            duplicate = False
        doc = fitz.open(p)
        text_chars = sum(len((page.get_text('text') or '').strip()) for page in doc)
        image_pages = sum(1 for page in doc if page.get_images(full=True))
        records.append({
            "chapter": ch,
            "kind": kind_of(p),
            "file": str(p.relative_to(root)),
            "pages": len(doc),
            "text_chars": text_chars,
            "image_pages": image_pages,
            "sha256": sha,
            "duplicate": duplicate,
            "duplicate_of": duplicate_of,
        })

unique = [r for r in records if not r['duplicate']]
lines = ["# 结构力学 14 次资料去重审计\n"]
lines.append("| 次数 | 唯一页数 | 图片页 | 文本字符 | 唯一文件 |")
lines.append("|---:|---:|---:|---:|---|")
for ch in range(1,15):
    items = [r for r in unique if r['chapter'] == ch]
    lines.append(f"| {ch} | {sum(r['pages'] for r in items)} | {sum(r['image_pages'] for r in items)} | {sum(r['text_chars'] for r in items)} | " + "<br>".join(f"{r['kind']}: {r['pages']}页/{r['text_chars']}字" for r in items) + " |")
lines.append("\n## 重复文件\n")
for r in records:
    if r['duplicate']:
        lines.append(f"- `{r['file']}` = `{r['duplicate_of']}`")
lines.append("\n## 唯一文件明细\n")
for r in unique:
    lines.append(f"- 第{r['chapter']}次 {r['kind']}: `{r['file']}`（{r['pages']}页，图片页{r['image_pages']}，文本层{r['text_chars']}字）")

(root / "manual_correction_audit_dedup.md").write_text("\n".join(lines), encoding="utf-8")
print("unique files", len(unique))
print("unique pages", sum(r['pages'] for r in unique))
print("unique image pages", sum(r['image_pages'] for r in unique))
print("unique text chars", sum(r['text_chars'] for r in unique))
print("duplicates", sum(1 for r in records if r['duplicate']))
