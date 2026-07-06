import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(r"D:/xm/zy/jglx")
ASSIGN_DIR = ROOT / "6.作业&答案"
NOTE_DIR = ROOT / "7.作业讲解笔记"
OUT = ROOT / "jglx_14_lectures_overleaf"
IMG_DIR = OUT / "images"
TMP_DIR = OUT / "_tmp"

CHAPTERS = {
    1: {"title": "几何组成分析", "answer_no": 1, "note_no": 1},
    2: {"title": "理论力学回顾", "answer_no": 2, "note_no": 2},
    3: {"title": "材料力学回顾", "answer_no": 3, "note_no": 3},
    4: {"title": "静定梁和刚架", "answer_no": 4, "note_no": 4},
    5: {"title": "静定桁架", "answer_no": 5, "note_no": 5},
    6: {"title": "组合结构", "answer_no": 6, "note_no": 6},
    7: {"title": "三铰拱", "answer_no": 7, "note_no": 7},
    8: {"title": "静定结构影响线", "answer_no": 8, "note_no": 8},
    9: {"title": "静定结构位移计算", "answer_no": 9, "note_no": 9},
    10: {"title": "力法（一）", "answer_no": 10, "note_no": 10},
    11: {"title": "力法（二）", "answer_no": 11, "note_no": 10},
    12: {"title": "位移法", "answer_no": 12, "note_no": 11},
    13: {"title": "弯矩分配法", "answer_no": 13, "note_no": None},
    14: {"title": "矩阵位移法", "answer_no": 14, "note_no": 13},
}

EXPLANATIONS = {
    1: "几何组成分析先看支座约束和体系自由度，再用二元体规则、两刚片/三刚片规则与瞬变判据逐步化简。答案判断应写清“几何不变、几何可变或瞬变”的理由。",
    2: "理论力学回顾的关键是受力图。先隔离研究对象，完整标注约束反力、集中力、分布力等，再列 $\\sum F_x=0$、$\\sum F_y=0$、$\\sum M=0$ 求解。",
    3: "材料力学题通常按“内力—应力—变形—强度/刚度校核”组织。弯曲问题要注意截面惯性矩、正负号和最大应力位置。",
    4: "静定梁和刚架先由整体平衡求支座反力，再分段求剪力、弯矩和轴力。内力图要用集中力、集中力偶、铰结点等位置的突变规律校核。",
    5: "静定桁架优先识别零杆，再结合节点法和截面法。节点法适合逐点推进，截面法适合直接求少数目标杆力。",
    6: "组合结构要先辨认桁架杆、梁式杆和刚架部分的传力特点。解题时按连接点拆分子结构，保证连接处作用力与反作用力成对一致。",
    7: "三铰拱利用整体平衡和中间铰弯矩为零求水平推力。任意截面内力可由左段或右段隔离体求得，并与同跨度简支梁弯矩关系校核。",
    8: "影响线可用静力法或机动法。反力影响线来自单位移动荷载平衡，剪力和弯矩影响线要明确考察截面左右侧取隔离体。",
    9: "位移计算以虚功原理为主线。单位荷载法中，实际荷载弯矩图 $M$ 与单位荷载弯矩图 $\\overline M$ 的图乘或积分给出目标位移。",
    10: "力法先确定超静定次数，选择赘余力并建立基本体系。柔度方程表达的是赘余力方向上的变形协调，最后叠加荷载效应与赘余力效应。",
    11: "力法（二）通常题型更复杂，应重点检查基本未知力选择、单位力图、柔度系数对称性以及自由项符号。最终内力图必须满足原结构约束条件。",
    12: "位移法以结点位移和杆端转角为基本未知量。先写杆端弯矩/剪力表达式，再由结点力矩平衡或剪力平衡建立方程求位移。",
    13: "弯矩分配法适合无侧移或经处理后的连续梁、刚架。步骤是计算转动刚度、分配系数、固端弯矩，然后反复分配与传递直至收敛。",
    14: "矩阵位移法按单元刚度矩阵、坐标变换、总体刚度组装、施加边界条件、解结点位移、回代单元内力的流程完成。",
}

ANSWER_SUMMARY = {
    1: "答案页给出了几何组成判定过程；整理时以约束数、刚片连接方式和瞬变情形作为最终判据。",
    2: "答案页给出了各题平衡方程和反力结果；可用任一点力矩平衡复核。",
    3: "答案页包含材料力学回顾题的计算过程；重点核对截面内力、应力公式和变形公式。",
    4: "答案页包含静定梁与刚架内力图；关键截面的剪力、弯矩值可作为校核点。",
    5: "答案页给出桁架杆力计算；正负号分别对应受拉、受压，零杆应单独标明。",
    6: "答案页给出组合结构拆分和受力计算；连接处内力平衡是主要校核点。",
    7: "答案页给出三铰拱水平推力和截面内力；中铰弯矩为零可作为核心校核。",
    8: "答案页给出影响线图和关键纵坐标；应检查单位荷载在控制位置时的正负号。",
    9: "答案页给出位移计算结果；注意实际弯矩图和单位弯矩图的乘积符号。",
    10: "答案页给出力法（一）的柔度方程和赘余力；最终内力由基本体系叠加得到。",
    11: "答案页给出力法（二）的方程与结果；柔度系数对称性和变形协调条件是主要检查点。",
    12: "答案页给出位移法作业完整解答；讲解笔记第 11 次可作为同主题补充。",
    13: "答案页给出弯矩分配过程；可用结点不平衡力矩逐轮趋近零进行检查。",
    14: "答案页给出矩阵位移法作业结果；讲解笔记第 13 次补充了矩阵组装和回代思路。",
}


def run(cmd):
    subprocess.run(cmd, check=True)


def pages(pdf: Path) -> int:
    data = subprocess.check_output(["pdfinfo", str(pdf)], stderr=subprocess.DEVNULL)
    text = data.decode("utf-8", errors="ignore")
    m = re.search(r"^Pages:\s+(\d+)", text, re.M)
    if not m:
        raise RuntimeError(f"读取页数失败：{pdf}")
    return int(m.group(1))


def find_answer_pdf(n: int) -> Path | None:
    candidates = sorted(ASSIGN_DIR.glob(f"*第{n}次*.pdf"), key=lambda p: ("及答案" not in p.name, "答案" not in p.name, len(p.name)))
    if not candidates:
        return None
    combined = [p for p in candidates if "及答案" in p.name]
    if combined:
        return combined[0]
    answer = [p for p in candidates if "答案" in p.name]
    assignment = [p for p in candidates if "答案" not in p.name]
    if answer and assignment:
        return None
    return candidates[0]


def find_split_answer_pdfs(n: int) -> list[Path]:
    candidates = sorted(ASSIGN_DIR.glob(f"*第{n}次*.pdf"), key=lambda p: p.name)
    combined = [p for p in candidates if "及答案" in p.name]
    if combined:
        return [combined[0]]
    return candidates


def find_note_pdf(n: int | None) -> Path | None:
    if n is None:
        return None
    candidates = sorted(NOTE_DIR.glob(f"*第{n}次作业笔记*.pdf"), key=lambda p: ("(1)" in p.name, p.name))
    return candidates[0] if candidates else None


def clean_image(path: Path):
    image = Image.open(path).convert("RGB")
    gray = ImageOps.grayscale(image)
    # 去除浅色水印/背景：浅于阈值的像素置白，深色笔迹和结构线保留。
    bw = gray.point(lambda pixel: 255 if pixel > 198 else max(0, int((pixel - 20) * 0.9)))
    cleaned = Image.merge("RGB", (bw, bw, bw))
    cleaned = ImageOps.autocontrast(cleaned, cutoff=1)
    inverted = ImageOps.invert(ImageOps.grayscale(cleaned))
    bbox = inverted.point(lambda pixel: 255 if pixel > 16 else 0).getbbox()
    if bbox:
        l, t, r, b = bbox
        pad = 18
        cleaned = cleaned.crop((max(0, l - pad), max(0, t - pad), min(cleaned.width, r + pad), min(cleaned.height, b + pad)))
    cleaned.save(path, optimize=True, compress_level=9)


def render_pdf(pdf: Path, prefix: str) -> list[str]:
    raw_prefix = TMP_DIR / prefix
    run(["pdftoppm", "-r", "135", "-png", str(pdf), str(raw_prefix)])
    generated = sorted(TMP_DIR.glob(f"{prefix}-*.png"), key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)))
    out = []
    for i, src in enumerate(generated, start=1):
        dst = IMG_DIR / f"{prefix}_p{i:02d}.png"
        shutil.move(src, dst)
        clean_image(dst)
        out.append(dst.relative_to(OUT).as_posix())
    return out


def esc(s: str) -> str:
    repl = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in s)


def section_images(tex: list[str], title: str, images: list[str]):
    tex.append(f"\\section{{{esc(title)}}}")
    if not images:
        tex.append(r"\begin{tcolorbox}[title=缺失说明]")
        tex.append("当前目录未找到对应 PDF。")
        tex.append(r"\end{tcolorbox}")
        return
    for i, img in enumerate(images, start=1):
        tex.append(r"\begin{center}")
        tex.append(f"\\includegraphics[width=0.96\\textwidth,height=0.82\\textheight,keepaspectratio]{{{img}}}")
        tex.append(f"\\par\\small {esc(title)}，第 {i}/{len(images)} 页")
        tex.append(r"\end{center}")
        if i != len(images):
            tex.append(r"\clearpage")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    IMG_DIR.mkdir(parents=True)
    TMP_DIR.mkdir()

    assembled = {}
    for n, meta in CHAPTERS.items():
        answer_pdfs = find_split_answer_pdfs(meta["answer_no"])
        note_pdf = find_note_pdf(meta["note_no"])
        answer_images = []
        for idx, pdf in enumerate(answer_pdfs, start=1):
            answer_images.extend(render_pdf(pdf, f"c{n:02d}_answer_{idx}"))
        note_images = render_pdf(note_pdf, f"c{n:02d}_note") if note_pdf else []
        assembled[n] = {"answer_pdfs": answer_pdfs, "note_pdf": note_pdf, "answer_images": answer_images, "note_images": note_images}
        print(f"第{n}讲：答案/作业 {len(answer_images)} 页，讲解笔记 {len(note_images)} 页")

    tex = [
        r"\documentclass[UTF8,12pt,a4paper,openany]{ctexbook}",
        r"\usepackage[margin=1.7cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{xcolor}",
        r"\usepackage[most]{tcolorbox}",
        r"\usepackage{hyperref}",
        r"\usepackage{fancyhdr}",
        r"\usepackage{enumitem}",
        r"\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\setlength{\headheight}{15pt}",
        r"\lhead{结构力学十四讲作业与答案整理}",
        r"\rhead{\thepage}",
        r"\setlength{\parindent}{2em}",
        r"\setlist[itemize]{leftmargin=2em}",
        r"\tcbset{colback=gray!4,colframe=black!45,arc=2mm,boxrule=0.5pt}",
        r"\title{结构力学十四讲作业与答案整理\\\large 去水印版、解析与讲解笔记汇编}",
        r"\author{根据本地资料整理}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\frontmatter",
        r"\chapter*{整理说明}",
        "本工程将本地 \\texttt{6.作业\\&答案} 与 \\texttt{7.作业讲解笔记} 中的资料整理为 XeLaTeX 可编译文档。原始资料多为手写或扫描式 PDF，机器文本识别不稳定，因此保留去水印、裁边后的页面图像，并为每讲补充解析要点、答案校核提示和对应讲解笔记。",
        "\\par 本文按前十四讲组织：第 1--12 讲对应第 1--12 次作业，第 13 讲为弯矩分配法，第 14 讲为矩阵位移法；动力学资料位于原第 15 次作业和第 14 次讲解笔记，未纳入本十四讲主线。",
        r"\tableofcontents",
        r"\mainmatter",
    ]

    for n, meta in CHAPTERS.items():
        tex.append(f"\\chapter{{第{n}讲：{esc(meta['title'])}}}")
        tex.append(r"\begin{tcolorbox}[title=解析要点]")
        tex.append(EXPLANATIONS[n])
        tex.append(r"\end{tcolorbox}")
        tex.append(r"\begin{tcolorbox}[title=答案与校核]")
        tex.append(ANSWER_SUMMARY[n])
        tex.append(r"\end{tcolorbox}")
        section_images(tex, "作业与答案（去水印版）", assembled[n]["answer_images"])
        tex.append(r"\clearpage")
        section_images(tex, "讲解笔记（去水印版）", assembled[n]["note_images"])
        tex.append(r"\clearpage")

    tex.extend([
        r"\backmatter",
        r"\chapter*{源文件索引}",
        r"\begin{itemize}",
    ])
    for n, data in assembled.items():
        answer_names = "；".join(p.name for p in data["answer_pdfs"]) or "未找到"
        note_name = data["note_pdf"].name if data["note_pdf"] else "未找到"
        tex.append(f"\\item 第{n}讲：作业/答案：{esc(answer_names)}；讲解笔记：{esc(note_name)}。")
    tex.extend([r"\end{itemize}", r"\end{document}"])

    (OUT / "main.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 结构力学十四讲作业与答案整理\n\n"
        "- 编译器：XeLaTeX。\n"
        "- Overleaf：上传压缩包后，Menu/Settings 中选择 XeLaTeX 编译。\n"
        "- 主文件：`main.tex`。\n"
        "- 内容：每讲包含解析要点、答案校核、作业答案去水印页面和讲解笔记去水印页面。\n",
        encoding="utf-8",
    )
    shutil.rmtree(TMP_DIR)
    print(f"生成完成：{OUT}")

if __name__ == "__main__":
    main()
