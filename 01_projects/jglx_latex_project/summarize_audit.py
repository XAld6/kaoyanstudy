import json
import re
from pathlib import Path

root = Path(r"D:/xm/zy/jglx")
report = root / "audit_sources_report.txt"
text = report.read_text(encoding="utf-8", errors="replace")
rows = json.loads(text.split("JSON_START", 1)[1])

def chapter_of(file):
    m = re.search(r"第(\d+)次", file)
    return int(m.group(1)) if m else None

def kind_of(file):
    if "讲解笔记" in file:
        return "讲解笔记"
    if "答案" in file and "作业及答案" not in file:
        return "答案"
    if "作业及答案" in file:
        return "作业及答案"
    if "作业" in file:
        return "作业题目"
    return "其他"

agg = {}
for row in rows:
    ch = chapter_of(row["file"])
    if ch is None or not 1 <= ch <= 14:
        continue
    agg.setdefault(ch, {"pages":0,"text_chars":0,"image_pages":0,"files":[]})
    agg[ch]["pages"] += row.get("pages",0)
    agg[ch]["text_chars"] += row.get("text_chars",0)
    agg[ch]["image_pages"] += row.get("image_pages",0)
    agg[ch]["files"].append((kind_of(row["file"]), row["pages"], row["text_chars"], row["file"]))

lines = []
lines.append("# 结构力学 14 次资料审计\n")
lines.append("| 次数 | 合计页数 | 图片页 | 文本字符 | 文件构成 |")
lines.append("|---:|---:|---:|---:|---|")
for ch in range(1,15):
    a = agg.get(ch, {"pages":0,"text_chars":0,"image_pages":0,"files":[]})
    file_desc = "<br>".join([f"{k}: {p}页/{tc}字" for k,p,tc,f in a["files"]])
    lines.append(f"| {ch} | {a['pages']} | {a['image_pages']} | {a['text_chars']} | {file_desc} |")
lines.append("\n## 详细文件\n")
for ch in range(1,15):
    lines.append(f"### 第 {ch} 次\n")
    for k,p,tc,f in agg.get(ch, {"files":[]})["files"]:
        lines.append(f"- {k}: `{f}`（{p} 页，文本层 {tc} 字）")
    lines.append("")
(root / "manual_correction_audit.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote manual_correction_audit.md")
print("chapters", len(agg), "pages", sum(a['pages'] for a in agg.values()))
