import zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent

from xml.etree import ElementTree as ET

path = HERE / "submission_review.docx"
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

with zipfile.ZipFile(path) as z:
    xml = z.read("word/document.xml")

root = ET.fromstring(xml)
items = []
for idx, node in enumerate(root.findall(".//w:t", ns)):
    text = node.text or ""
    if any(key in text for key in ["慧眼", "识裂", "基础设施", "项目背景"]):
        items.append((idx, text))

print("matches", len(items))
for idx, text in items[:80]:
    print(idx, repr(text[:300]))
