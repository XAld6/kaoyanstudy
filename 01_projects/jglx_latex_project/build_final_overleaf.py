from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:
    RapidOCR = None


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "jglx_final_overleaf"
CACHE = ROOT / "_final_ocr_cache"
FIG_DIR = OUT / "figures"
SEC_DIR = OUT / "sections"

WATERMARK_PATTERNS = [
    "小鹿土木",
    "研大",
    "公众号",
    "萌兔",
    "快印",
    "草稿纸",
    "后续关注",
    "备注",
    "永久微信",
    "微信",
    "1931637888",
    "193",
    "第*页,共*页",
    "第*页，共*页",
]

METHOD_NOTES = {
    "几何组成分析": "先算自由度，再按二元体、两刚片、三刚片和瞬变判据复核。判断顺序建议为：先找可并入大地的刚片，再检查约束方向是否共线、平行或交于一点，最后判定有无多余约束。",
    "理论力学回顾": "支座反力题统一从整体隔离体入手，列水平力、竖向力和力矩平衡。若求得反力为负，说明真实方向与假设方向相反，数值仍可直接代入后续内力计算。",
    "材料力学回顾": "弯矩图、剪力图和轴力图要先确定支座反力，再按截面法分段。符号约定要前后一致，最大应力或变形应结合截面几何量与材料参数检查量纲。",
    "静定梁和刚架": "静定结构按平衡方程逐段推进即可。集中力使剪力突变，集中力矩使弯矩突变，均布荷载区段的剪力为一次函数、弯矩为二次函数。",
    "静定桁架": "优先判断零杆，再选择节点法或截面法。节点法适合逐点推进，截面法适合只求少数目标杆件；受拉为正、受压为负的约定要在答案中写清。",
    "组合结构": "先拆分梁、桁架、刚架等子结构，连接点处作用力成对出现。对组合结构求解时应从约束较少或可独立平衡的部分开始。",
    "三铰拱": "三铰拱利用中铰弯矩为零求水平推力，再用截面平衡求轴力、剪力和弯矩。注意拱轴线高度会直接影响弯矩表达式。",
    "静定结构影响线": "影响线可用静力法或机动法。剪力影响线关注截面两侧相对竖向位移，弯矩影响线关注相对转角；移动荷载取影响线同号面积最大的位置。",
    "静定结构位移计算": "位移计算以虚功原理为核心。常用单位荷载法、图乘法和积分法，关键是实结构内力图与虚结构内力图的符号和区段对应。",
    "力法1": "力法先选多余约束，建立基本体系，再由变形协调方程求多余未知力。柔度系数和自由项应由内力图乘或积分得到。",
    "力法2": "高阶超静定力法要注意未知量编号、柔度矩阵对称性和自由项符号。解出多余力后，将基本体系内力与各单位多余力内力线性叠加。",
    "位移法": "位移法以节点转角和线位移为未知量，由杆端力表达式和节点平衡建立方程。对称结构可先取半结构以减少未知量。",
    "弯矩分配法": "弯矩分配法按固端弯矩、分配系数、传递系数和逐轮平衡进行。最后应检查每个节点的杆端弯矩代数和是否接近外加节点力矩。",
    "矩阵位移法": "矩阵位移法按单元刚度矩阵、坐标转换、整体刚度组装、边界条件处理和回代杆端力求解。编号清楚可显著减少代数错误。",
    "动力学": "动力学题先明确自由度和广义坐标，建立质量、阻尼、刚度关系。单自由度系统重点掌握固有频率、阻尼比和动力系数。",
    "稳定": "稳定问题通常转化为特征值问题。临界荷载由结构刚度退化条件确定，端部约束和有效长度系数是最容易出错的地方。",
    "极限荷载": "极限荷载题要找塑性铰形成过程和机构条件。可用静力法列平衡上限，也可用机构法由外功等于塑性耗能求解。"
}


@dataclass
class SourcePDF:
    path: Path
    group: str
    number: int | None
    title: str
    kind: str


def natural_key(path: Path) -> tuple[int, str]:
    number = extract_number(path.name) or 999
    return number, path.name


def extract_number(name: str) -> int | None:
    m = re.search(r"第\s*(\d+)\s*次", name)
    return int(m.group(1)) if m else None


def title_from_name(name: str) -> str:
    m = re.search(r"[（(]([^）)]+)[）)]", name)
    if m:
        return m.group(1).strip()
    m = re.search(r"—(.+?)\.pdf$", name)
    if m:
        return m.group(1).strip()
    return Path(name).stem


def classify(path: Path, group: str) -> str:
    name = path.name
    if group == "notes":
        return "讲解笔记"
    if "答案" in name and "及答案" not in name:
        return "答案与解析"
    if "及答案" in name:
        return "作业及答案"
    return "作业题目"


def collect_sources() -> list[SourcePDF]:
    assignment_dir = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("6."))
    note_dir = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("7."))
    sources: list[SourcePDF] = []
    for path in sorted(assignment_dir.glob("*.pdf"), key=natural_key):
        sources.append(SourcePDF(path, "assignments", extract_number(path.name), title_from_name(path.name), classify(path, "assignments")))
    seen_note_keys: set[tuple[int | None, str]] = set()
    for path in sorted(note_dir.glob("*.pdf"), key=natural_key):
        key = (extract_number(path.name), re.sub(r"\(1\)", "", path.stem))
        if key in seen_note_keys:
            continue
        seen_note_keys.add(key)
        sources.append(SourcePDF(path, "notes", extract_number(path.name), title_from_name(path.name), classify(path, "notes")))
    return sources


def is_watermark(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return True
    if re.search(r"微.?信|193\d{3,}|19[:：]?\d{3,}|小鹿|萌兔|快印", compact):
        return True
    for pattern in WATERMARK_PATTERNS:
        regex = re.escape(pattern).replace(r"\*", ".*")
        if re.search(regex, compact):
            return True
    if re.fullmatch(r"第?\d+页[，,]?共?\d+页?", compact):
        return True
    return False


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\uf020", " ")
    text = text.replace("", "=").replace("", r"\times ").replace("", "-")
    text = text.replace("", "+").replace("", r"\Delta ").replace("", r"\theta ")
    text = text.replace("⼀", "一").replace("⼆", "二").replace("⽀", "支").replace("⼒", "力")
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line or is_watermark(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def readable_pdf_text(text: str) -> bool:
    if len(text.strip()) < 180:
        return False
    cjk = sum("\u4e00" <= ch <= "\u9fff" for ch in text)
    weird = sum(ord(ch) > 0x2FFF and not ("\u4e00" <= ch <= "\u9fff") for ch in text)
    return cjk >= 25 and weird / max(len(text), 1) < 0.18


def render_page(page: fitz.Page, dpi: int = 140) -> Image.Image:
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def clean_image(img: Image.Image) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    draw.rectangle((0, 0, w, int(h * 0.055)), fill="white")
    draw.rectangle((0, int(h * 0.94), w, h), fill="white")
    draw.rectangle((int(w * 0.72), 0, w, int(h * 0.12)), fill="white")
    draw.rectangle((int(w * 0.38), int(h * 0.04), int(w * 0.72), int(h * 0.19)), fill="white")
    draw.rectangle((int(w * 0.66), int(h * 0.68), w, int(h * 0.94)), fill="white")
    px = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            avg = (r + g + b) // 3
            if 105 <= avg <= 245 and max(r, g, b) - min(r, g, b) <= 22:
                px[x, y] = (255, 255, 255)
    return out


def ocr_image(engine: RapidOCR, image_path: Path) -> list[str]:
    result, _ = engine(str(image_path))
    if not result:
        return []
    lines = []
    for item in result:
        text = str(item[1]).strip()
        if text and not is_watermark(text):
            lines.append(text)
    return lines


def page_record(source: SourcePDF, source_index: int, page_index: int, page: fitz.Page, engine: RapidOCR | None) -> dict:
    key = f"{source.path.stem}_p{page_index + 1:03d}"
    old_safe_key = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", key)
    safe_key = f"src{source_index:02d}_p{page_index + 1:03d}"
    json_path = CACHE / f"{safe_key}.json"
    old_json_path = CACHE / f"{old_safe_key}.json"
    fig_rel = f"figures/{safe_key}.jpg"
    fig_path = OUT / fig_rel
    if json_path.exists() and fig_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))

    image = render_page(page)
    clean = clean_image(image)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    clean.save(fig_path, "JPEG", quality=72, optimize=True)

    if old_json_path.exists():
        old = json.loads(old_json_path.read_text(encoding="utf-8"))
        text = clean_text(old.get("text", ""))
        method = old.get("method", "cache")
    else:
        raw_pdf = clean_text(page.get_text("text") or "")
        method = "pdf-text"
        text = raw_pdf
        if not readable_pdf_text(raw_pdf) and engine is not None:
            ocr_tmp = CACHE / f"{safe_key}_ocr.jpg"
            image.save(ocr_tmp, "JPEG", quality=82)
            ocr_lines = ocr_image(engine, ocr_tmp)
            if len("\n".join(ocr_lines)) > len(raw_pdf):
                text = clean_text("\n".join(ocr_lines))
                method = "rapidocr"
    record = {
        "source": str(source.path),
        "page": page_index + 1,
        "method": method,
        "text": text,
        "figure": fig_rel,
    }
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def latex_escape(text: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in text)


def para_tex(text: str) -> str:
    if not text.strip():
        return r"\emph{本页原始资料主要为结构图、手写推导或扫描图形；已在下方清理图形页保留。}"
    pieces = [latex_escape(line) for line in text.splitlines() if line.strip()]
    return "\n\n".join(pieces)


def section_tex(source: SourcePDF, records: list[dict]) -> str:
    title = f"{source.kind}：{source.path.stem}"
    body = [f"\\section{{{latex_escape(title)}}}"]
    body.append(r"\begin{analysisbox}")
    note = METHOD_NOTES.get(source.title, METHOD_NOTES.get(source.path.stem, "本节按题目、答案和讲解笔记顺序整理。对扫描图中的结构几何关系，正文保留 OCR 可识别文字，并在图形页中保留清理后的题图，便于核对杆件、支座、荷载和尺寸。"))
    body.append(latex_escape(note))
    body.append(r"\end{analysisbox}")
    for rec in records:
        body.append(f"\\subsection*{{第 {rec['page']} 页转写}}")
        body.append(para_tex(rec["text"]))
        body.append(r"\begin{figure}[H]\centering")
        body.append(f"\\includegraphics[width=0.92\\textwidth]{{{rec['figure']}}}")
        body.append(f"\\caption{{{latex_escape(source.path.stem)} 第 {rec['page']} 页清理图形页}}")
        body.append(r"\end{figure}")
    return "\n".join(body) + "\n"


def write_main(sources: list[SourcePDF], section_files: list[str]) -> None:
    main = [
        r"\documentclass[UTF8,zihao=-4,openany]{ctexbook}",
        r"\usepackage[a4paper,margin=2.1cm]{geometry}",
        r"\usepackage{amsmath,amssymb,mathtools}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\usepackage{enumitem}",
        r"\usepackage{xcolor}",
        r"\usepackage{hyperref}",
        r"\usepackage[most]{tcolorbox}",
        r"\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}",
        r"\setlist{itemsep=0.35em,topsep=0.35em}",
        r"\newtcolorbox{analysisbox}{breakable,enhanced,colback=blue!2,colframe=blue!45!black,title=解析补充}",
        r"\title{结构力学基础与技巧班作业、答案与讲解笔记\\\large LaTeX 重构去水印版}",
        r"\author{根据本地 PDF 资料整理}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\frontmatter",
        r"\chapter*{整理说明}",
        r"本工程将原始扫描 PDF 中的题目、答案、解析和讲解笔记整理为可编译的 LaTeX 文档。正文采用文本抽取与本地 OCR 转写，广告、水印、页脚和无关印刷信息已过滤；涉及结构图、荷载图、内力图等难以可靠纯文本表达的内容，使用清理后的图形页辅助保留，避免题图信息丢失。",
        r"\tableofcontents",
        r"\mainmatter",
    ]
    for section_file in section_files:
        main.append(f"\\include{{sections/{Path(section_file).stem}}}")
    main.extend([r"\backmatter", r"\chapter*{源文件覆盖清单}", r"\begin{itemize}"])
    for source in sources:
        main.append(r"\item " + latex_escape(f"{source.kind} - 第{source.number if source.number is not None else '?'}次 - {source.path.name}"))
    main.extend([r"\end{itemize}", r"\end{document}"])
    (OUT / "main.tex").write_text("\n".join(main) + "\n", encoding="utf-8")


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    CACHE.mkdir(exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    SEC_DIR.mkdir(parents=True, exist_ok=True)

    sources = collect_sources()
    engine = RapidOCR() if RapidOCR is not None else None
    section_files: list[str] = []
    report: list[dict] = []
    for idx, source in enumerate(sources, start=1):
        print(f"[{idx}/{len(sources)}] {source.path.name}", flush=True)
        doc = fitz.open(source.path)
        records = [page_record(source, idx, i, page, engine) for i, page in enumerate(doc)]
        sec_name = f"{idx:02d}_{source.group}_{source.number or 0:02d}.tex"
        (SEC_DIR / sec_name).write_text(section_tex(source, records), encoding="utf-8")
        section_files.append(sec_name)
        report.append({
            "file": source.path.name,
            "pages": len(records),
            "methods": {m: sum(1 for r in records if r["method"] == m) for m in sorted({r["method"] for r in records})},
            "chars": sum(len(r["text"]) for r in records),
        })
    write_main(sources, section_files)
    (OUT / "README.md").write_text(
        "Overleaf 上传说明\n"
        "================\n\n"
        "1. 上传整个压缩包或上传本目录全部文件。\n"
        "2. 编译器选择 XeLaTeX。\n"
        "3. 主文件为 main.tex。\n\n"
        "说明：正文为 LaTeX 文本重排，图形页为清理水印后的辅助图形资料，用于保留结构图、荷载图、内力图等题目必要信息。\n",
        encoding="utf-8",
    )
    (OUT / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def compile_and_zip() -> None:
    for _ in range(2):
        subprocess.run(["xelatex", "-interaction=nonstopmode", "main.tex"], cwd=OUT, check=True)
    zip_path = ROOT / "jglx_final_overleaf.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in OUT.rglob("*"):
            if path.is_file() and path.suffix.lower() not in {".aux", ".log", ".out", ".toc"}:
                zf.write(path, path.relative_to(OUT))
    print(f"ZIP={zip_path}")
    print(f"PDF={OUT / 'main.pdf'}")


if __name__ == "__main__":
    build()
    compile_and_zip()
