from __future__ import annotations

import json
import re
import shutil
import sys
import zipfile
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import fitz

import build_practice_exam_style as style
import build_practice_no_solution as base


ROOT = base.BASE
PROJECTS_DIR = ROOT / "02_LaTeX工程"
PDF_DIR = ROOT / "01_最终成品" / "PDF"
ZIP_DIR = ROOT / "01_最终成品" / "Overleaf压缩包"
PROJECT_DIR = PROJECTS_DIR / "practice_review_selected_inline_answer"
ZIP_PATH = ZIP_DIR / "施工章节测试_复习指南对应题_去重答案跟题版_Overleaf.zip"

def C(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


QUESTION_PDF_KEYWORD = C(0x590d, 0x4e60, 0x6307, 0x5357, 0x5bf9, 0x5e94, 0x9898)
MISSING = C(0x6e90, 0x9898, 0x672a, 0x63d0, 0x4f9b)


def find_reference_pdf() -> Path:
    candidates = [
        p
        for p in (Path.home() / "Downloads").glob("*.pdf")
        if QUESTION_PDF_KEYWORD in p.name
    ]
    if not candidates:
        raise FileNotFoundError("未在 Downloads 找到包含“复习指南对应题”的 PDF。")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_reference_pdf(pdf_path: Path) -> list[dict]:
    doc = fitz.open(str(pdf_path))
    chapter_re = re.compile(C(0x7b2c) + "[" + C(0x4e00, 0x4e8c, 0x4e09, 0x56db, 0x4e94, 0x516d, 0x4e03, 0x516b, 0x4e5d, 0x5341) + "]+" + C(0x7ae0) + ".*" + C(0x7ae0, 0x8282, 0x6d4b, 0x8bd5))
    q_re = re.compile(C(0x7b2c) + r"\s*(\d+)\s*" + C(0x9898) + r"(.*)")
    guide_prefix = C(0x5bf9, 0x5e94, 0x590d, 0x4e60, 0x6307, 0x5357, 0xff1a)
    answer_table = C(0x7b54, 0x6848, 0x901f, 0x67e5, 0x8868)

    records: list[dict] = []
    chapter = ""
    in_answer_table = False
    for page_index, page in enumerate(doc):
        lines = [line.strip() for line in page.get_text().splitlines() if line.strip()]
        if page_index > 2 and any(line == answer_table for line in lines):
            in_answer_table = True
        if in_answer_table:
            continue
        for i, line in enumerate(lines):
            if chapter_re.search(line):
                chapter = line
            match = q_re.search(line)
            if not match or not chapter:
                continue
            guide = ""
            for next_line in lines[i + 1 : i + 10]:
                if next_line.startswith(guide_prefix):
                    guide = next_line[len(guide_prefix) :].strip()
                    break
            if guide:
                records.append(
                    {
                        "pdf_page": page_index + 1,
                        "chapter": chapter,
                        "serial": int(match.group(1)),
                        "qtype": match.group(2).strip(),
                        "guide": guide,
                    }
                )
    return records


def extract_answers(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^###\s+", text)
    answers: list[str] = []
    for block in blocks[1:]:
        lines = [line.rstrip() for line in block.splitlines()]
        if not lines or not re.match(r"\d+\.\s*", lines[0].strip()):
            continue
        answer = ""
        for raw_line in lines[1:]:
            line = raw_line.strip()
            match = re.match(C(0x7b54, 0x6848) + r"[：:]\s*(.+)$", line)
            if match:
                answer = base.clean_text(match.group(1))
                break
        answers.append(answer or MISSING)
    return answers


def parse_all_questions() -> list[dict]:
    image_dir = PROJECT_DIR / "images"
    base.IMAGE_DIR = image_dir
    chapters = [base.parse_chapter(path) for path in base.CY_DIR.glob("*.md")]
    chapters.sort(key=lambda item: item["rank"])

    chapter_paths = sorted(base.CY_DIR.glob("*.md"), key=lambda p: base.chapter_rank(p.stem))
    answers_by_title: dict[str, list[str]] = {}
    for path in chapter_paths:
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        answers_by_title[title] = extract_answers(path)

    all_questions: list[dict] = []
    serial = 1
    for chapter in chapters:
        answers = answers_by_title.get(chapter["title"], [])
        for idx, question in enumerate(chapter["questions"]):
            item = dict(question)
            item["serial"] = serial
            item["chapter_title"] = chapter["title"]
            item["answer"] = answers[idx] if idx < len(answers) else MISSING
            item["qtype"] = base.question_type(question)
            all_questions.append(item)
            serial += 1
    return all_questions


def norm_text(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[（）()，。；;：:、.!！?？“”\"'《》<>]", "", text)
    return text.lower()


def dedupe_records(records: list[dict], question_by_serial: dict[int, dict]) -> tuple[list[dict], list[dict]]:
    kept: list[dict] = []
    removed: list[dict] = []
    seen_guides: set[str] = set()
    seen_stems: list[tuple[str, int]] = []

    for record in records:
        question = question_by_serial.get(record["serial"])
        if not question:
            removed.append({**record, "reason": "未能在原题库找到该题号"})
            continue
        guide_key = norm_text(record["guide"])
        stem_key = norm_text(question["stem"])

        if guide_key in seen_guides:
            removed.append({**record, "reason": "与已保留题属于同一复习指南知识点"})
            continue

        similar_to = None
        for old_stem, old_serial in seen_stems:
            ratio = SequenceMatcher(None, stem_key, old_stem).ratio()
            if ratio >= 0.82:
                similar_to = old_serial
                break
        if similar_to is not None:
            removed.append({**record, "reason": f"题干与第 {similar_to} 题相似"})
            continue

        kept.append(record)
        seen_guides.add(guide_key)
        seen_stems.append((stem_key, record["serial"]))
    return kept, removed


def preamble() -> str:
    text = style.preamble()
    text = text.replace("无解析刷题版", "复习指南对应题｜答案跟题")
    text = text.replace(
        r"\definecolor{choicepink}{HTML}{DB2777}",
        r"\definecolor{choicepink}{HTML}{DB2777}"
        + "\n"
        + r"\definecolor{answergreen}{HTML}{15803D}",
    )
    insert = r"""
\newcommand{\guidebox}[1]{%
  \begin{tcolorbox}[
    enhanced,
    breakable,
    colback=examblue!5,
    colframe=examline,
    boxrule=0.4pt,
    arc=0.8mm,
    left=2mm,
    right=2mm,
    top=0.9mm,
    bottom=0.9mm
  ]
  {\small\textbf{\textcolor{examblue}{对应复习指南：}}#1}
  \end{tcolorbox}
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
"""
    return text.replace(r"\begin{document}", insert + "\n" + r"\begin{document}")


def cover(total_questions: int, original_count: int, removed_count: int) -> str:
    return rf"""
\begin{{titlepage}}
\vspace*{{1.2cm}}
{{\Huge\bfseries\textcolor{{examnavy}}{{施工章节测试}}}}\par
\vspace{{0.35em}}
{{\LARGE\bfseries\textcolor{{examred}}{{复习指南对应题 去重答案跟题版}}}}\par
\vspace{{0.8em}}
{{\color{{examline}}\rule{{0.82\linewidth}}{{0.8pt}}}}\par
\vspace{{1.1em}}
{{\large 仅保留参考 PDF 中与复习指南对应的题目；同一知识点或题干高度相似的题已去重。}}\par
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
\textcolor{{examnavy}}{{参考题数}}\quad\textbf{{{original_count}}}\qquad
\textcolor{{examnavy}}{{去重后}}\quad\textbf{{{total_questions}}}\qquad
\textcolor{{examnavy}}{{删除相似}}\quad\textbf{{{removed_count}}}\par
\vspace{{0.45em}}
\normalsize\textcolor{{examgray}}{{顺序版；每题后直接附答案，不生成乱序版。}}
\end{{tcolorbox}}
\vfill
{{\small\textcolor{{examgray}}{{依据《施工章节测试\_复习指南对应题\_刷题版4.pdf》重新整理}}}}
\end{{titlepage}}
\tableofcontents
\newpage
"""


def write_question(question: dict, record: dict, number: int) -> str:
    lines = [
        rf"\begin{{questionbox}}{{第 {number} 题（原第 {question['serial']} 题）}}{{{question['qtype']}}}",
        rf"\guidebox{{{base.tex_escape(record['guide'])}}}",
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
            rf"\inlineanswer{{{base.tex_escape(question.get('answer', MISSING))}}}",
            r"\end{questionbox}",
        ]
    )
    return "\n".join(lines)


def build_document(kept: list[dict], question_by_serial: dict[int, dict], original_count: int, removed_count: int) -> str:
    parts = [preamble(), cover(len(kept), original_count, removed_count)]
    current_chapter = ""
    for idx, record in enumerate(kept, 1):
        question = question_by_serial[record["serial"]]
        if record["chapter"] != current_chapter:
            current_chapter = record["chapter"]
            chapter_count = sum(1 for r in kept if r["chapter"] == current_chapter)
            parts.append(rf"\section{{{base.tex_escape(current_chapter)}}}")
            parts.append(rf"\chaptermeta{{本章保留 {chapter_count} 题；题号括号中标注原全卷题号。}}")
        parts.append(write_question(question, record, idx))
    parts.append(r"\end{document}" + "\n")
    return "\n\n".join(parts)


def write_project() -> None:
    reference_pdf = find_reference_pdf()
    records = parse_reference_pdf(reference_pdf)
    if not records:
        raise RuntimeError("没有从参考 PDF 中提取到题目记录。")

    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    (PROJECT_DIR / "images").mkdir(parents=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)

    questions = parse_all_questions()
    question_by_serial = {q["serial"]: q for q in questions}
    kept, removed = dedupe_records(records, question_by_serial)
    tex = build_document(kept, question_by_serial, len(records), len(removed))

    (PROJECT_DIR / "main.tex").write_text(tex, encoding="utf-8")
    (PROJECT_DIR / "01_施工章节测试_复习指南对应题_去重答案跟题版.tex").write_text(tex, encoding="utf-8")
    manifest = {
        "reference_pdf": str(reference_pdf),
        "original_records": len(records),
        "kept": len(kept),
        "removed": len(removed),
        "removed_by_reason": dict(Counter(item["reason"] for item in removed)),
        "kept_records": kept,
        "removed_records": removed,
    }
    (PROJECT_DIR / "selection_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试复习指南对应题 - 去重答案跟题版\n\n"
        "- `main.tex`：顺序版，不含乱序版。\n"
        "- 每题后直接附答案。\n"
        "- `selection_manifest.json` 记录保留和删除的题目。\n"
        "- 编译器请选择 XeLaTeX。\n",
        encoding="utf-8",
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in PROJECT_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_DIR))

    print(f"reference={reference_pdf}")
    print(f"project={PROJECT_DIR}")
    print(f"zip={ZIP_PATH}")
    print(f"original_records={len(records)}")
    print(f"kept={len(kept)}")
    print(f"removed={len(removed)}")
    print("removed_by_reason=" + json.dumps(manifest["removed_by_reason"], ensure_ascii=False))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    write_project()
