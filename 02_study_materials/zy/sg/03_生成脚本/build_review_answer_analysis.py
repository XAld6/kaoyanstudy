"""施工章节测试_复习指南对应题_带答案解析版
生成 LaTeX 工程: 题目 + 答案速查表 + 每题解析
"""
from __future__ import annotations
import json
import shutil
import zipfile
from pathlib import Path

import build_practice_no_solution as base

ROOT = base.BASE
PROJECTS_DIR = ROOT / "02_LaTeX工程"
PDF_DIR = ROOT / "01_最终成品" / "PDF"
ZIP_DIR = ROOT / "01_最终成品" / "Overleaf压缩包"
PROJECT_DIR = PROJECTS_DIR / "practice_review_answer_with_analysis"
ZIP_PATH = ZIP_DIR / "施工章节测试_复习指南对应题_答案解析版_Overleaf.zip"
SCRIPT_DIR = Path(__file__).resolve().parent

# ── 章节信息: (简称, 全称) ─ 题数由 ANSWER_TABLE 自动推导 ────
CHAPTER_NAMES = [
    ("第一章",   "土方工程"),
    ("第二章",   "桩基础工程"),
    ("第三章",   "基坑工程"),
    ("第四章",   "混凝土结构工程"),
    ("第五章",   "预应力混凝土工程"),
    ("第六章",   "砌筑工程"),
    ("第七章",   "脚手架工程"),
    ("第八章",   "装饰工程(抹灰工程)"),
    ("第九章",   "防水工程"),
    ("第十章",   "流水施工原理"),
    ("第十一章", "网络计划技术"),
]

# ── 答案速查表数据 ──────────────────────────────────────────────
ANSWER_TABLE = [
    # Ch1 土方工程 (Q1-30)
    ["A","B","C","D","C","A","ACDE","D","ABCD","A",
     "D","B","C","BCE","C","B","ABC","D","ACD","ACE",
     "B","A","B","BD","BCDE","A","BCE","B","A","C"],
    # Ch2 桩基础工程 (Q31-37)
    ["D","D","BE","CE","D","A","B"],
    # Ch3 基坑工程 (Q38-47)
    ["C","D","ABD","AB","A","C","BE","AE","A","A"],
    # Ch4 混凝土结构工程 (Q48-62)
    ["A","C","B","BD","B","ABC","C","D","B","D",
     "BCD","ADE","C","A","CDE"],
    # Ch5 预应力混凝土工程 (Q63-71)
    ["A","C","D","A","C","D","ACE"],
    # Ch6 砌筑工程 (Q72-96)
    ["D","C","A","D","C","D","A","C","ABC","D",
     "C","BCD","B","C","A","B","C","D","C","C",
     "D","BE","C","B","AD"],
    # Ch7 脚手架工程 (Q97-101)
    ["BC","CE","B","AB","AE"],
    # Ch8 装饰工程 (Q102-103)
    ["BDE","C"],
    # Ch9 防水工程 (Q104-110)
    ["A","BDE","BE","ABCE","A","ACE","B"],
    # Ch10 流水施工原理 (Q111-124)
    ["C","C","A","B","B","B","C","D","B","C",
     "D","C","B","C"],
    # Ch11 网络计划技术 (Q125-147)
    ["D","C","B","A","A","D","A","A","B","B",
     "D","BC","B","C","D","C","D","B","BD","AB",
     "BCD","A","BD"],
]


def load_explanations() -> dict[int, str]:
    """从 analysis_data.json 加载解析数据."""
    json_path = SCRIPT_DIR / "analysis_data.json"
    if not json_path.exists():
        return {}
    raw = json.load(open(json_path, encoding="utf-8"))
    return {int(k): v for k, v in raw.items()}


def tex_escape(text: str) -> str:
    return base.tex_escape(text)


def preamble() -> str:
    return r"""\documentclass[UTF8,fontset=windows,11pt]{ctexart}
\usepackage[a4paper,margin=1.85cm,headheight=24pt,footskip=24pt]{geometry}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{tcolorbox}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage{tabularx}
\usepackage{booktabs}
\tcbuselibrary{skins,breakable}

\definecolor{examnavy}{HTML}{1E3A5F}
\definecolor{examblue}{HTML}{2563A7}
\definecolor{examred}{HTML}{C2410C}
\definecolor{examgray}{HTML}{4B5563}
\definecolor{examline}{HTML}{D7DEE8}
\definecolor{exambg}{HTML}{F8FAFC}
\definecolor{choicepink}{HTML}{DB2777}
\definecolor{answergreen}{HTML}{15803D}
\definecolor{analysispurple}{HTML}{7C3AED}
\definecolor{analysisbg}{HTML}{F5F3FF}

\hypersetup{colorlinks=true,linkcolor=examnavy,urlcolor=examblue}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.28em}
\linespread{1.08}

\pagestyle{fancy}
\fancyhf{}
\lhead{\small\textcolor{examnavy}{施工章节测试}}
\rhead{\small\textcolor{examred}{复习指南对应题 答案解析版}}
\cfoot{\small\textcolor{examgray}{第 \thepage\ 页 / 共 \pageref{LastPage} 页}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{examline}\leaders\hrule height \headrulewidth\hfill}}

\titleformat{\section}
  {\Large\bfseries\color{examnavy}}
  {\thesection}
  {0.8em}
  {}
\titlespacing*{\section}{0pt}{1.1em}{0.55em}

\newcommand{\chaptermeta}[1]{%
  \vspace{-0.25em}
  {\small\textcolor{examgray}{#1}}\par
  \vspace{0.35em}
  {\color{examline}\rule{\linewidth}{0.55pt}}\vspace{0.25em}
}

\newtcolorbox{analysisbox}[2]{
  enhanced,
  breakable,
  colback=white,
  colframe=examline,
  boxrule=0.55pt,
  arc=1mm,
  left=3mm,
  right=3mm,
  top=2.4mm,
  bottom=2mm,
  before skip=0.65em,
  after skip=0.72em,
  borderline west={1.8pt}{0pt}{analysispurple},
  title={\textcolor{examnavy}{#1}\hfill\textcolor{examgray}{#2}},
  coltitle=examnavy,
  colbacktitle=exambg,
  fonttitle=\bfseries,
  boxed title style={
    colback=exambg,
    colframe=examline,
    boxrule=0.35pt,
    arc=0.8mm
  },
  attach boxed title to top left={xshift=2mm,yshift=-2mm},
  top=6mm
}

\newcommand{\inlineanswer}[1]{%
  \vspace{0.25em}
  \begin{tcolorbox}[
    enhanced,
    breakable,
    colback=answergreen!6,
    colframe=answergreen,
    boxrule=0.55pt,
    arc=0.8mm,
    left=2.5mm,
    right=2.5mm,
    top=1.2mm,
    bottom=1.2mm,
    borderline west={1.6pt}{0pt}{answergreen}
  ]
  \textbf{\textcolor{answergreen}{答案：}}#1
  \end{tcolorbox}
}

\newcommand{\analysiscontent}[1]{%
  \vspace{0.15em}
  \begin{tcolorbox}[
    enhanced,
    breakable,
    colback=analysisbg,
    colframe=analysispurple!30,
    boxrule=0.45pt,
    arc=1mm,
    left=2.5mm,
    right=2.5mm,
    top=1mm,
    bottom=1mm
  ]
  {\small\color{examgray}#1}
  \end{tcolorbox}
}

\begin{document}
"""


def cover(total_questions: int, total_chapters: int) -> str:
    return rf"""
\begin{{titlepage}}
\vspace*{{1.2cm}}
{{\Huge\bfseries\textcolor{{examnavy}}{{施工章节测试}}}}\par
\vspace{{0.35em}}
{{\LARGE\bfseries\textcolor{{examred}}{{复习指南对应题 答案解析版}}}}\par
\vspace{{0.8em}}
{{\color{{examline}}\rule{{0.82\linewidth}}{{0.8pt}}}}\par
\vspace{{1.1em}}
{{\large 题目 + 答案速查表 + 每题详细解析；便于刷题后对照复盘。}}\par
\vspace{{2.2em}}
\begin{{tcolorbox}}[
  enhanced,
  width=0.78\linewidth,
  colback=exambg,
  colframe=examline,
  boxrule=0.6pt,
  arc=1mm,
  left=4mm,
  right=4mm,
  top=3mm,
  bottom=3mm
]
\Large
\textcolor{{examnavy}}{{章节数}}\quad\textbf{{{total_chapters}}}\qquad
\textcolor{{examnavy}}{{题目数}}\quad\textbf{{{total_questions}}}\par
\vspace{{0.45em}}
\normalsize\textcolor{{examgray}}{{建议先独立刷题，再对照答案与解析复盘。}}
\end{{tcolorbox}}
\vfill
{{\small\textcolor{{examgray}}{{依据施工章节测试复习指南对应题刷题版整理}}}}
\end{{titlepage}}
\tableofcontents
\newpage
"""


def answer_table_latex() -> str:
    """生成答案速查表."""
    parts = [
        r"\section{答案速查表}",
        r"\chaptermeta{答题完毕后，对照此表快速核对答案。}",
    ]
    serial = 1
    for ch_idx, (ch_name, ch_title) in enumerate(CHAPTER_NAMES):
        answers = ANSWER_TABLE[ch_idx]
        count = len(answers)
        parts.append(
            r"\noindent\textbf{\textcolor{examnavy}{"
            + ch_name + "  " + ch_title
            + r"}}"
            + r"\\" + r"\vspace{0.3em}"
        )
        rows = []
        for row_start in range(0, count, 10):
            row_end = min(row_start + 10, count)
            rows.append(answers[row_start:row_end])

        cols_spec = "|c|" + "X|" * 10
        table = [r"\begin{tabularx}{\linewidth}{" + cols_spec + "}", r"\hline"]
        hdr = r"\textbf{题号}"
        for i in range(10):
            hdr += rf" & \textbf{{{i+1}}}"
        hdr += r" \\"
        table.append(hdr)
        table.append(r"\hline")
        for row_idx, ans_cells in enumerate(rows):
            row_start_num = serial + row_idx * 10
            row_end_num = row_start_num + len(ans_cells)
            if len(ans_cells) == 1:
                label = f"Q{row_start_num}"
            else:
                label = f"Q{row_start_num}-{row_end_num - 1}"
            row_str = label
            for a in ans_cells:
                row_str += f" & {a}"
            for _ in range(10 - len(ans_cells)):
                row_str += " & "
            row_str += r" \\"
            table.append(row_str)
            table.append(r"\hline")
        table.append(r"\end{tabularx}")
        table.append(r"\vspace{0.6em}")
        parts.append("\n".join(table))
        serial += count
    return "\n\n".join(parts)


def analysis_section(explanations: dict[int, str]) -> str:
    """生成答案解析部分."""
    parts = [
        r"\newpage",
        r"\section{答案解析}",
        r"\chaptermeta{以下对每道题给出正确答案解析和易错点提示。}",
    ]
    serial = 1
    for ch_idx, (ch_name, ch_title) in enumerate(CHAPTER_NAMES):
        answers = ANSWER_TABLE[ch_idx]
        count = len(answers)
        parts.append(rf"\subsection{{{ch_name}  {ch_title}}}")
        for i in range(count):
            q_num = serial + i
            answer = answers[i]
            analysis = explanations.get(q_num, "(解析待补充)")
            parts.append(
                rf"\begin{{analysisbox}}{{第 {q_num} 题}}{{答案：{answer}}}"
            )
            parts.append(rf"\inlineanswer{{{answer}}}")
            parts.append(rf"\analysiscontent{{{tex_escape(analysis)}}}")
            parts.append(r"\end{analysisbox}")
        serial += count
    return "\n\n".join(parts)


def build_document(explanations: dict[int, str]) -> str:
    total_questions = sum(len(a) for a in ANSWER_TABLE)
    parts = [
        preamble(),
        cover(total_questions, len(CHAPTER_NAMES)),
        answer_table_latex(),
        analysis_section(explanations),
        r"\end{document}" + "\n",
    ]
    return "\n\n".join(parts)


def write_project() -> None:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    (PROJECT_DIR / "images").mkdir(parents=True)

    explanations = load_explanations()
    print(f"Loaded {len(explanations)} explanations")

    tex = build_document(explanations)
    (PROJECT_DIR / "main.tex").write_text(tex, encoding="utf-8")
    (PROJECT_DIR / "01_施工章节测试_复习指南对应题_答案解析版.tex").write_text(
        tex, encoding="utf-8"
    )
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试 复习指南对应题 答案解析版\n\n"
        "- `main.tex`: 顺序版，含答案速查表与每题解析。\n"
        "- 编译器请选择 XeLaTeX。\n",
        encoding="utf-8",
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in PROJECT_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_DIR))

    total = sum(len(a) for a in ANSWER_TABLE)
    print(f"project={PROJECT_DIR}")
    print(f"zip={ZIP_PATH}")
    print(f"questions={total}")


if __name__ == "__main__":
    write_project()
