from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import build_practice_exam_style as style
import build_practice_no_solution as base


ROOT = base.BASE
PROJECTS_DIR = ROOT / "02_LaTeX工程" if (ROOT / "02_LaTeX工程").exists() else ROOT
ZIP_DIR = ROOT / "01_最终成品" / "Overleaf压缩包" if (ROOT / "01_最终成品" / "Overleaf压缩包").exists() else ROOT
PROJECT_DIR = PROJECTS_DIR / "practice_inline_answer_exam_style"
ZIP_PATH = ZIP_DIR / "施工章节测试_答案跟题版_新版排版_Overleaf.zip"


def preamble() -> str:
    text = style.preamble()
    text = text.replace("无解析刷题版", "答案跟题版")
    text = text.replace(
        r"\definecolor{choicepink}{HTML}{DB2777}",
        r"\definecolor{choicepink}{HTML}{DB2777}" + "\n" + r"\definecolor{answergreen}{HTML}{15803D}",
    )
    insert = r"""
\newcommand{\inlineanswer}[1]{%
  \vspace{0.35em}
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
"""
    return text.replace(r"\begin{document}", insert + "\n" + r"\begin{document}")


def cover(total_questions: int, total_chapters: int) -> str:
    return rf"""
\begin{{titlepage}}
\vspace*{{1.2cm}}
{{\Huge\bfseries\textcolor{{examnavy}}{{施工章节测试}}}}\par
\vspace{{0.35em}}
{{\LARGE\bfseries\textcolor{{examred}}{{答案跟题版}}}}\par
\vspace{{0.8em}}
{{\color{{examline}}\rule{{0.82\linewidth}}{{0.8pt}}}}\par
\vspace{{1.1em}}
{{\large 每道题后紧跟答案，方便快速核对与背诵。此版本不另写详细解析。}}\par
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
\normalsize\textcolor{{examgray}}{{选择题直接显示正确选项；源题未给答案的案例题会明确标注。}}
\end{{tcolorbox}}
\vfill
{{\small\textcolor{{examgray}}{{由 cy 章节测试源文件重新整理生成}}}}
\end{{titlepage}}
\tableofcontents
\newpage
"""


def extract_answers(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^###\s+", text)
    answers: list[str] = []

    for block in blocks[1:]:
        block_lines = [line.rstrip() for line in block.splitlines()]
        if not block_lines:
            continue
        if not re.match(r"\d+\.\s*", block_lines[0].strip()):
            continue

        answer = ""
        for raw_line in block_lines[1:]:
            line = raw_line.strip()
            match = re.match(r"答案[：:]\s*(.+)$", line)
            if match:
                answer = base.clean_text(match.group(1))
                break
        answers.append(answer or "源题未提供")

    return answers


def parse_chapter(path: Path) -> dict:
    chapter = base.parse_chapter(path)
    answers = extract_answers(path)
    for question, answer in zip(chapter["questions"], answers):
        question["answer"] = answer
    for question in chapter["questions"][len(answers):]:
        question["answer"] = "源题未提供"
    chapter["answer_count"] = sum(1 for answer in answers if answer != "源题未提供")
    return chapter


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
        lines.append(r"\textcolor{examgray}{本题为简答/计算/案例题。}")

    lines.extend(
        [
            rf"\inlineanswer{{{base.tex_escape(question.get('answer', '源题未提供'))}}}",
            r"\end{questionbox}",
        ]
    )
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
        parts.append(rf"\chaptermeta{{本章共 {len(questions)} 题。答案紧跟在每道题后，便于即时核对。}}")
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
    chapters = [parse_chapter(path) for path in base.CY_DIR.glob("*.md")]
    chapters.sort(key=lambda item: item["rank"])

    normal_tex = build_document(chapters, shuffled=False)
    shuffled_tex = build_document(chapters, shuffled=True)

    (PROJECT_DIR / "01_施工章节测试_答案跟题版_新版排版.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "02_施工章节测试_答案跟题乱序版_新版排版.tex").write_text(shuffled_tex, encoding="utf-8")
    (PROJECT_DIR / "main.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试答案跟题版\n\n"
        "- `main.tex`：顺序版，每道题后紧跟答案。\n"
        "- `02_施工章节测试_答案跟题乱序版_新版排版.tex`：每章内乱序版，每道题后紧跟答案。\n"
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
    print(f"answers={sum(ch.get('answer_count', 0) for ch in chapters)}")


if __name__ == "__main__":
    write_project()
