import re
import shutil
import subprocess
from pathlib import Path
import fitz

ROOT = Path(r"D:/xm/zy/jglx")
ASSIGN_DIR = ROOT / "6.作业&答案"
OUT = ROOT / "jglx_14_lectures_retyped_latex"
OCR_DIR = OUT / "ocr"
TESS = Path(r"C:/Program Files/Tesseract-OCR/tesseract.exe")

CHAPTERS = {
    1: ("几何组成分析", [1]),
    2: ("理论力学回顾", [2]),
    3: ("材料力学回顾", [3]),
    4: ("静定梁和刚架", [4]),
    5: ("静定桁架", [5]),
    6: ("组合结构", [6]),
    7: ("三铰拱", [7]),
    8: ("静定结构影响线", [8]),
    9: ("静定结构位移计算", [9]),
    10: ("力法（一）", [10]),
    11: ("力法（二）", [11]),
    12: ("位移法", [12]),
    13: ("弯矩分配法", [13]),
    14: ("矩阵位移法", [14]),
}

EXPLAIN = {
    1: "先判定体系自由度，再结合二元体规则、两刚片规则、三刚片规则和瞬变判据作结论。",
    2: "先画隔离体受力图，再分别列水平力、竖向力和力矩平衡方程。",
    3: "按内力、应力、变形和强度/刚度条件组织解答，注意单位与符号。",
    4: "先求支座反力，再分段列剪力和弯矩，最后按突变规律绘制内力图。",
    5: "优先判别零杆，再用节点法或截面法求目标杆件轴力。",
    6: "先拆分组合结构的梁、桁架和刚架部分，再保证连接处作用力平衡。",
    7: "三铰拱题利用中铰弯矩为零求水平推力，再求截面内力。",
    8: "影响线题可用静力法或机动法，关键是单位移动荷载位置与正负号。",
    9: "位移计算以虚功原理为核心，常用单位荷载法、图乘法或积分法。",
    10: "力法先选赘余力，建立基本体系和柔度方程，再叠加内力。",
    11: "力法（二）重点检查柔度系数、自由项符号和变形协调条件。",
    12: "位移法以结点位移/转角为未知量，由杆端力和结点平衡建立方程。",
    13: "弯矩分配法按固端弯矩、分配系数、分配和传递逐轮计算。",
    14: "矩阵位移法按单元刚度、坐标转换、总体组装、边界条件和回代内力求解。",
}


def run(cmd):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def find_pdfs(n: int):
    candidates = sorted(ASSIGN_DIR.glob(f"*第{n}次*.pdf"), key=lambda p: p.name)
    combined = [p for p in candidates if "及答案" in p.name]
    if combined:
        return combined
    return candidates


def clean_text(text: str) -> str:
    text = (text.replace("", "=").replace("", r"\\times ").replace("", "-")
                .replace("", "+").replace("", r"\\cdot ").replace("", r"\\div "))
    text = "".join(ch if (ch in "\n\t" or ord(ch) >= 32) else " " for ch in text)
    text = "".join("[符号]" if 0xE000 <= ord(ch) <= 0xF8FF else ch for ch in text)
    text = text.replace("（", "(").replace("）", ")")
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.search(r"第\s*\d+\s*页.*共\s*\d+\s*页", line):
            continue
        if "版权所有" in line or "水印" in line or "草稿纸" in line:
            continue
        if len(line) <= 2 and re.fullmatch(r"[|/\\_\-—,.，。 ]+", line):
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_page_text(pdf: Path, page_index: int, prefix: str) -> tuple[str, str]:
    doc = fitz.open(pdf)
    page = doc[page_index]
    text = clean_text(page.get_text("text"))
    if len(text) >= 80 and sum('\u4e00' <= ch <= '\u9fff' for ch in text) >= 5:
        return text, "pdf-text"
    image_prefix = OCR_DIR / prefix
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-f", str(page_index + 1), "-l", str(page_index + 1), str(pdf), str(image_prefix)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    imgs = sorted(OCR_DIR.glob(f"{prefix}-*.png"))
    if not imgs:
        return text, "empty"
    out_prefix = OCR_DIR / f"{prefix}_ocr"
    subprocess.run([str(TESS), str(imgs[0]), str(out_prefix), "-l", "chi_sim+eng", "--psm", "6"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ocr_text = clean_text((out_prefix.with_suffix(".txt")).read_text(encoding="utf-8", errors="ignore"))
    return ocr_text, "ocr"


def latex_escape(s: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def split_items(text: str):
    pattern = re.compile(r"(?m)(?=^\s*\(?\d+[-－]\d+[,，、.]?)")
    parts = [p.strip() for p in pattern.split(text) if p.strip()]
    return parts or [text.strip()]


def classify_pdf(pdf: Path):
    name = pdf.name
    if "答案" in name and "及答案" not in name:
        return "答案"
    if "及答案" in name:
        return "作业及答案"
    return "作业题目"


def make_tex():
    if OUT.exists():
        shutil.rmtree(OUT)
    OCR_DIR.mkdir(parents=True)
    raw_dir = OUT / "extracted_text"
    raw_dir.mkdir()

    tex = [
        r"\documentclass[UTF8,12pt,a4paper,openany]{ctexbook}",
        r"\usepackage[margin=2.2cm]{geometry}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{enumitem}",
        r"\usepackage[most]{tcolorbox}",
        r"\usepackage{xcolor}",
        r"\usepackage{hyperref}",
        r"\hypersetup{colorlinks=true,linkcolor=blue}",
        r"\newcommand{\TODO}[1]{\textcolor{red}{[需校对：#1]}}",
        r"\tcbset{colback=gray!3,colframe=black!45,arc=2mm,boxrule=0.5pt}",
        r"\title{结构力学十四讲作业、解析与答案\\\large OCR 转写 LaTeX 重排版}",
        r"\author{根据本地 PDF 资料转写整理}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\frontmatter",
        r"\chapter*{使用说明}",
        "本版不再采用整页扫描图嵌入，而是将题干、答案和解析转为可编辑 LaTeX 文本。原始资料中部分题面为扫描图片，部分讲解为手写内容，OCR 对结构图、复杂公式和手写字识别不稳定；文中以 \\TODO{...} 标出需要人工对照原 PDF 校对的位置。",
        r"\tableofcontents",
        r"\mainmatter",
    ]

    report = []
    for chapter, (title, nums) in CHAPTERS.items():
        tex.append(f"\\chapter{{第{chapter}讲：{latex_escape(title)}}}")
        tex.append(r"\begin{tcolorbox}[title=解析总览]")
        tex.append(latex_escape(EXPLAIN[chapter]))
        tex.append(r"\end{tcolorbox}")
        for n in nums:
            pdfs = find_pdfs(n)
            if not pdfs:
                tex.append(r"\TODO{未找到对应 PDF 源文件。}")
                continue
            for pdf in pdfs:
                kind = classify_pdf(pdf)
                tex.append(f"\\section{{{latex_escape(kind)}：{latex_escape(pdf.stem)}}}")
                doc = fitz.open(pdf)
                all_text = []
                methods = {"ocr": 0, "pdf-text": 0, "empty": 0}
                for page_index in range(doc.page_count):
                    text, method = extract_page_text(pdf, page_index, f"c{chapter:02d}_{kind}_{page_index+1:03d}")
                    methods[method] = methods.get(method, 0) + 1
                    all_text.append(f"【第 {page_index+1} 页，来源：{method}】\n{text}")
                raw = "\n\n".join(all_text)
                (raw_dir / f"c{chapter:02d}_{pdf.stem}.txt").write_text(raw, encoding="utf-8")
                report.append(f"第{chapter}讲 {pdf.name}: {doc.page_count}页, {methods}")
                items = split_items(raw)
                tex.append(r"\begin{enumerate}[label=\textbf{\arabic*.},leftmargin=2em]")
                for item in items:
                    if not item.strip():
                        continue
                    uncertain = "\\TODO{OCR 自动转写，结构图/公式需对照原 PDF 校对。}\\par "
                    tex.append(r"\item " + uncertain + latex_escape(item).replace("\n", r"\par "))
                tex.append(r"\end{enumerate}")
    tex.extend([r"\backmatter", r"\chapter*{OCR 处理报告}", r"\begin{itemize}"])
    for line in report:
        tex.append(r"\item " + latex_escape(line))
    tex.extend([r"\end{itemize}", r"\end{document}"])
    (OUT / "main.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 结构力学十四讲 OCR 转写 LaTeX 版\n\n"
        "- 主文件：`main.tex`\n"
        "- 编译器：XeLaTeX\n"
        "- 本版不嵌入整页扫描图，正文为 OCR/文本抽取得到的可编辑 LaTeX。\n"
        "- `extracted_text/` 保存每个源 PDF 的原始抽取文本，便于人工校对。\n"
        "- 标有 `需校对` 的地方需要对照原 PDF 修正公式、结构图和手写内容。\n",
        encoding="utf-8",
    )
    print("生成完成", OUT)
    print("\n".join(report))

if __name__ == "__main__":
    make_tex()
