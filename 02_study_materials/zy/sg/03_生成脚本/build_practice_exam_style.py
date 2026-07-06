from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import build_practice_no_solution as base


ROOT = base.BASE
PROJECTS_DIR = ROOT / "02_LaTeX工程" if (ROOT / "02_LaTeX工程").exists() else ROOT
ZIP_DIR = ROOT / "01_最终成品" / "Overleaf压缩包" if (ROOT / "01_最终成品" / "Overleaf压缩包").exists() else ROOT
PROJECT_DIR = PROJECTS_DIR / "practice_no_solution_exam_style"
ZIP_PATH = ZIP_DIR / "施工章节测试_无解析刷题版_新版排版_Overleaf.zip"


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
\tcbuselibrary{skins,breakable}

\definecolor{examnavy}{HTML}{1E3A5F}
\definecolor{examblue}{HTML}{2563A7}
\definecolor{examred}{HTML}{C2410C}
\definecolor{examgray}{HTML}{4B5563}
\definecolor{examline}{HTML}{D7DEE8}
\definecolor{exambg}{HTML}{F8FAFC}
\definecolor{choicepink}{HTML}{DB2777}

\hypersetup{colorlinks=true,linkcolor=examnavy,urlcolor=examblue}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.28em}
\linespread{1.08}

\pagestyle{fancy}
\fancyhf{}
\lhead{\small\textcolor{examnavy}{施工章节测试}}
\rhead{\small\textcolor{examred}{无解析刷题版}}
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

\newcommand{\choice}[1]{%
  \tcbox[
    on line,
    colback=white,
    colframe=choicepink,
    boxrule=0.55pt,
    arc=0.8mm,
    left=1.35mm,
    right=1.35mm,
    top=0.15mm,
    bottom=0.15mm
  ]{\textbf{\textcolor{choicepink}{#1}}}%
}

\newcommand{\questionstem}[1]{%
  \textbf{\textcolor{examnavy}{#1}}\par\vspace{0.35em}
}

\newcommand{\answerarea}[1]{%
  \vspace{0.2em}
  \begin{tcolorbox}[
    enhanced,
    colback=exambg,
    colframe=examline,
    boxrule=0.45pt,
    arc=0.8mm,
    height=#1,
    left=2mm,
    right=2mm,
    top=1mm,
    bottom=1mm
  ]
  \textcolor{examline}{作答区}
  \end{tcolorbox}
}

\newtcolorbox{questionbox}[2]{
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
  borderline west={1.8pt}{0pt}{examblue},
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

\begin{document}
"""


def cover(total_questions: int, total_chapters: int) -> str:
    return rf"""
\begin{{titlepage}}
\vspace*{{1.2cm}}
{{\Huge\bfseries\textcolor{{examnavy}}{{施工章节测试}}}}\par
\vspace{{0.35em}}
{{\LARGE\bfseries\textcolor{{examred}}{{无解析刷题版}}}}\par
\vspace{{0.8em}}
{{\color{{examline}}\rule{{0.82\linewidth}}{{0.8pt}}}}\par
\vspace{{1.1em}}
{{\large 题目、选项、图片与作答区整理版；不含答案，不含解析。}}\par
\vspace{{2.2em}}
\begin{{tcolorbox}}[
  enhanced,
  width=0.72\linewidth,
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
\normalsize\textcolor{{examgray}}{{建议先独立完成，再回看课堂资料核对。}}
\end{{tcolorbox}}
\vfill
{{\small\textcolor{{examgray}}{{由 cy 章节测试源文件重新整理生成}}}}
\end{{titlepage}}
\tableofcontents
\newpage
"""


def write_question(question: dict, serial: int) -> str:
    qtype = base.question_type(question)
    lines = [
        rf"\begin{{questionbox}}{{第 {serial} 题}}{{{qtype}}}",
        rf"\questionstem{{{base.tex_escape(question['stem'])}}}",
    ]

    for image in question["images"]:
        lines.extend(
            [
                r"\begin{center}",
                rf"\includegraphics[width=0.86\linewidth]{{{base.tex_escape(image)}}}",
                r"\end{center}",
            ]
        )

    if question["options"]:
        lines.append(r"\begin{enumerate}[label=\protect\choice{\Alph*}, leftmargin=*, itemsep=0.32em, topsep=0.2em]")
        for _, option_text in question["options"]:
            lines.append(rf"\item {base.tex_escape(option_text)}")
        lines.append(r"\end{enumerate}")
    else:
        lines.append(r"\textcolor{examgray}{本题为简答/计算题，请在下方作答。}")

    blank_height = "2.15cm" if question["options"] else "4.8cm"
    lines.extend([rf"\answerarea{{{blank_height}}}", r"\end{questionbox}"])
    return "\n".join(lines)


def build_document(chapters: list[dict], shuffled: bool = False) -> str:
    total_questions = sum(len(ch["questions"]) for ch in chapters)
    parts = [preamble(), cover(total_questions, len(chapters))]
    serial = 1
    rng = base.random.Random(20260613)

    for chapter in chapters:
        questions = list(chapter["questions"])
        if shuffled:
            rng.shuffle(questions)
        title = chapter["title"]
        if shuffled:
            title = f"{title}（本章乱序）"
        parts.append(rf"\section{{{base.tex_escape(title)}}}")
        parts.append(rf"\chaptermeta{{本章共 {len(questions)} 题。此版本不含答案与解析，请直接作答。}}")
        for question in questions:
            parts.append(write_question(question, serial))
            serial += 1

    parts.append(r"\end{document}" + "\n")
    return "\n\n".join(parts)


def write_project() -> None:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    image_dir = PROJECT_DIR / "images"
    image_dir.mkdir(parents=True)

    base.IMAGE_DIR = image_dir
    chapters = [base.parse_chapter(path) for path in base.CY_DIR.glob("*.md")]
    chapters.sort(key=lambda item: item["rank"])

    normal_tex = build_document(chapters, shuffled=False)
    shuffled_tex = build_document(chapters, shuffled=True)

    (PROJECT_DIR / "01_施工章节测试_无解析刷题版_新版排版.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "02_施工章节测试_无解析刷题乱序版_新版排版.tex").write_text(shuffled_tex, encoding="utf-8")
    (PROJECT_DIR / "main.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试无解析刷题版 - 新版排版\n\n"
        "- `main.tex`：顺序刷题版。\n"
        "- `02_施工章节测试_无解析刷题乱序版_新版排版.tex`：每章内乱序版。\n"
        "- 编译器请选择 XeLaTeX。\n",
        encoding="utf-8",
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in PROJECT_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_DIR))

    print(f"project={PROJECT_DIR}")
    print(f"zip={ZIP_PATH}")
    print(f"chapters={len(chapters)}")
    print(f"questions={sum(len(ch['questions']) for ch in chapters)}")


if __name__ == "__main__":
    write_project()
