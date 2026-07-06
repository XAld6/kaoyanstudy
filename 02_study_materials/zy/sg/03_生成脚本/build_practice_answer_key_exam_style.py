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
PROJECT_DIR = PROJECTS_DIR / "practice_answer_key_exam_style"
ZIP_PATH = ZIP_DIR / "施工章节测试_刷题版_答案在最后_新版排版_Overleaf.zip"


def preamble() -> str:
    text = style.preamble()
    text = text.replace(r"\usepackage{hyperref}", r"\usepackage{longtable}" + "\n" + r"\usepackage{hyperref}")
    text = text.replace("无解析刷题版", "无解析刷题版｜答案置后")
    text = text.replace(
        r"\definecolor{choicepink}{HTML}{DB2777}",
        r"\definecolor{choicepink}{HTML}{DB2777}" + "\n" + r"\definecolor{answergreen}{HTML}{15803D}",
    )
    return text


def cover(total_questions: int, total_chapters: int) -> str:
    return rf"""
\begin{{titlepage}}
\vspace*{{1.2cm}}
{{\Huge\bfseries\textcolor{{examnavy}}{{施工章节测试}}}}\par
\vspace{{0.35em}}
{{\LARGE\bfseries\textcolor{{examred}}{{刷题版：答案置于文末}}}}\par
\vspace{{0.8em}}
{{\color{{examline}}\rule{{0.82\linewidth}}{{0.8pt}}}}\par
\vspace{{1.1em}}
{{\large 正文只保留题目、选项、图片与作答区；答案统一放在最后，方便刷完再核对。}}\par
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
\normalsize\textcolor{{examgray}}{{建议先独立完成，再翻到文末答案表核对。}}
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


def answer_appendix(chapters: list[dict], shuffled_orders: list[tuple[int, str, str, str]]) -> str:
    parts = [
        r"\newpage",
        r"\section*{答案速查表}",
        r"\addcontentsline{toc}{section}{答案速查表}",
        r"{\small\textcolor{examgray}{本页仅列答案，不含解析。建议完成正文后再查看。}}\par",
        r"\vspace{0.6em}",
    ]

    current_chapter = ""
    for serial, chapter_title, source_num, answer in shuffled_orders:
        if chapter_title != current_chapter:
            if current_chapter:
                parts.append(r"\end{longtable}")
                parts.append(r"\vspace{0.4em}")
            current_chapter = chapter_title
            parts.append(rf"\subsection*{{{base.tex_escape(chapter_title)}}}")
            parts.append(r"\begin{longtable}{p{0.16\linewidth}p{0.2\linewidth}p{0.52\linewidth}}")
            parts.append(r"\textbf{\textcolor{examnavy}{题号}} & \textbf{\textcolor{examnavy}{原题号}} & \textbf{\textcolor{answergreen}{答案}} \\")
            parts.append(r"\hline")
        parts.append(
            rf"{serial} & {base.tex_escape(source_num)} & \textbf{{\textcolor{{answergreen}}{{{base.tex_escape(answer)}}}}} \\"
        )

    if current_chapter:
        parts.append(r"\end{longtable}")

    return "\n".join(parts)


def build_document(chapters: list[dict], shuffled: bool = False) -> str:
    total_questions = sum(len(ch["questions"]) for ch in chapters)
    parts = [preamble(), cover(total_questions, len(chapters))]
    serial = 1
    rng = base.random.Random(20260613)
    answer_rows: list[tuple[int, str, str, str]] = []

    for chapter in chapters:
        questions = list(chapter["questions"])
        if shuffled:
            rng.shuffle(questions)
        title = chapter["title"]
        display_title = f"{title}（本章乱序）" if shuffled else title
        parts.append(rf"\section{{{base.tex_escape(display_title)}}}")
        parts.append(rf"\chaptermeta{{本章共 {len(questions)} 题。正文不含解析，答案请见文末速查表。}}")
        for question in questions:
            parts.append(style.write_question(question, serial))
            answer_rows.append((serial, title, str(question["num"]), question.get("answer", "源题未提供")))
            serial += 1

    parts.append(answer_appendix(chapters, answer_rows))
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

    (PROJECT_DIR / "01_施工章节测试_刷题版_答案在最后_新版排版.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "02_施工章节测试_刷题乱序版_答案在最后_新版排版.tex").write_text(shuffled_tex, encoding="utf-8")
    (PROJECT_DIR / "main.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试刷题版 - 答案在最后\n\n"
        "- `main.tex`：顺序刷题版，答案置于文末。\n"
        "- `02_施工章节测试_刷题乱序版_答案在最后_新版排版.tex`：每章内乱序版，答案置于文末。\n"
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
