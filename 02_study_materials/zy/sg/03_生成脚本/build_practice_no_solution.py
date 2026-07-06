from __future__ import annotations

import html
import random
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def find_workspace_root() -> Path:
    for candidate in (SCRIPT_DIR, SCRIPT_DIR.parent):
        if (candidate / "cy").exists() or (candidate / "00_源文件" / "cy").exists():
            return candidate
    return SCRIPT_DIR


BASE = find_workspace_root()
SOURCE_DIR = BASE / "00_源文件" if (BASE / "00_源文件").exists() else BASE
PROJECTS_DIR = BASE / "02_LaTeX工程" if (BASE / "02_LaTeX工程").exists() else BASE
ZIP_DIR = BASE / "01_最终成品" / "Overleaf压缩包" if (BASE / "01_最终成品" / "Overleaf压缩包").exists() else BASE
CY_DIR = SOURCE_DIR / "cy"
OLD_IMAGE_DIRS = [
    PROJECTS_DIR / "overleaf_project" / "images",
    PROJECTS_DIR / "overleaf_upload_clean" / "images",
    BASE / "overleaf_project" / "images",
    BASE / "overleaf_upload_clean" / "images",
]
PROJECT_DIR = PROJECTS_DIR / "practice_no_solution_overleaf"
IMAGE_DIR = PROJECT_DIR / "images"
ZIP_PATH = ZIP_DIR / "施工章节测试_无解析刷题版_Overleaf.zip"


CHAPTER_ORDER = {
    "第一章": 1,
    "第二章": 2,
    "第三章": 3,
    "第四章": 4,
    "第五章": 5,
    "第六章": 6,
    "第七章": 7,
    "第八章": 8,
    "第九章": 9,
    "第十章": 10,
    "第十一章": 11,
}


def chapter_rank(name: str) -> int:
    for key, value in CHAPTER_ORDER.items():
        if key in name:
            return value
    return 999


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = (
        text.replace("Ⅰ", "I")
        .replace("Ⅱ", "II")
        .replace("Ⅲ", "III")
        .replace("Ⅳ", "IV")
        .replace("Ⅴ", "V")
        .replace("①", "(1)")
        .replace("②", "(2)")
        .replace("③", "(3)")
        .replace("④", "(4)")
        .replace("⑤", "(5)")
        .replace("⑥", "(6)")
        .replace("⑦", "(7)")
        .replace("⑧", "(8)")
        .replace("⑨", "(9)")
        .replace("⑩", "(10)")
        .replace("φ", "直径")
        .replace("Φ", "直径")
        .replace("≤", "<=")
        .replace("≥", ">=")
    )
    text = text.replace(r"\(", "（").replace(r"\)", "）")
    text = text.replace(r"\[", "[").replace(r"\]", "]")
    text = re.sub(r"\[图片:\d+\]", "见下图", text)
    text = text.replace(r"\.", ".").replace(r"\+", "+").replace(r"\%", "%")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([，。；：！？、）])", r"\1", text)
    text = re.sub(r"([（])\s+", r"\1", text)
    return text.strip()


def tex_escape(text: str) -> str:
    mapping = {
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
    return "".join(mapping.get(ch, ch) for ch in text)


def image_id_from_url(url: str) -> str:
    match = re.search(r"/file_access/(\d+)", url)
    if match:
        return match.group(1)
    return re.sub(r"\W+", "_", url)[:48]


def sniff_image_extension(data: bytes, content_type: str = "") -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "png" in content_type:
        return ".png"
    return ".png"


def resolve_image(url: str) -> str:
    img_id = image_id_from_url(url)
    for old_dir in OLD_IMAGE_DIRS:
        for old_file in old_dir.glob(f"{img_id}.*"):
            target = IMAGE_DIR / old_file.name
            shutil.copy2(old_file, target)
            return f"images/{target.name}"

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            ext = sniff_image_extension(data, response.headers.get("Content-Type", ""))
    except (urllib.error.URLError, TimeoutError) as exc:
        marker = IMAGE_DIR / f"{img_id}.missing.txt"
        marker.write_text(f"Image download failed:\n{url}\n{exc}\n", encoding="utf-8")
        return ""

    target = IMAGE_DIR / f"{img_id}{ext}"
    target.write_bytes(data)
    return f"images/{target.name}"


def is_answer_or_hint(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("答案：")
        or stripped.startswith("答案:")
        or "查看答案" in stripped
        or stripped.startswith("解析：")
        or stripped.startswith("解析:")
    )


def parse_chapter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    blocks = re.split(r"(?m)^###\s+", text)
    questions = []

    for block in blocks[1:]:
        block_lines = [line.rstrip() for line in block.splitlines()]
        if not block_lines:
            continue
        first = block_lines[0].strip()
        match = re.match(r"(\d+)\.\s*(.*)", first)
        if not match:
            continue

        question = {
            "num": int(match.group(1)),
            "stem_parts": [match.group(2).strip()],
            "options": [],
            "images": [],
        }

        for raw_line in block_lines[1:]:
            line = raw_line.strip()
            if not line or is_answer_or_hint(line):
                continue

            image_match = re.match(r"!\[[^\]]*\]\((https?://[^)]+)\)", line)
            if image_match:
                local_image = resolve_image(image_match.group(1))
                if local_image:
                    question["images"].append(local_image)
                continue

            option_match = re.match(r"-\s*([A-E])\.\s*(.*)", line)
            if option_match:
                question["options"].append(
                    (option_match.group(1), clean_text(option_match.group(2)))
                )
                continue

            question["stem_parts"].append(line)

        stem = clean_text(" ".join(question["stem_parts"]))
        stem = re.sub(r"!\[[^\]]*\]\(https?://[^)]+\)", "", stem).strip()
        if "见下图" in stem:
            before, _, after = stem.partition("见下图")
            before = before.strip()
            after = after.strip()
            if after and before and (after == before or after in before or before in after):
                stem = before + "（见下图）"
            else:
                stem = (before + "（见下图） " + after).strip()
        questions.append(
            {
                "num": question["num"],
                "stem": stem,
                "options": question["options"],
                "images": question["images"],
            }
        )

    return {"title": title, "rank": chapter_rank(title), "questions": questions}


def question_type(question: dict) -> str:
    option_count = len(question["options"])
    if option_count >= 5:
        return "多选题"
    if option_count >= 2:
        return "单选题"
    return "案例/计算题"


def write_question(question: dict, serial: int) -> str:
    qtype = question_type(question)
    lines = [
        rf"\begin{{questionbox}}{{第 {serial} 题}}{{{qtype}}}",
        rf"\questionstem{{{tex_escape(question['stem'])}}}",
    ]

    for image in question["images"]:
        lines.extend(
            [
                r"\begin{center}",
                rf"\includegraphics[width=0.92\linewidth]{{{tex_escape(image)}}}",
                r"\end{center}",
            ]
        )

    if question["options"]:
        lines.append(r"\begin{enumerate}[label=\protect\choice{\Alph*}, leftmargin=*, itemsep=0.42em]")
        for _, option_text in question["options"]:
            lines.append(rf"\item {tex_escape(option_text)}")
        lines.append(r"\end{enumerate}")
    else:
        lines.append(r"\vspace{0.2em}\textcolor{inkgray}{本题为简答/计算题，请在下方作答。}")

    blank_height = "2.7cm" if question["options"] else "5.8cm"
    lines.extend(
        [
            rf"\answerarea{{{blank_height}}}",
            r"\end{questionbox}",
        ]
    )
    return "\n".join(lines)


def preamble() -> str:
    return r"""\documentclass[UTF8,fontset=fandol,11pt]{ctexart}
\usepackage[a4paper,margin=1.75cm,headheight=24pt,footskip=24pt]{geometry}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{tcolorbox}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{titlesec}
\usepackage{hyperref}
\tcbuselibrary{skins,breakable}

\definecolor{deepnavy}{HTML}{172554}
\definecolor{hotpink}{HTML}{DB2777}
\definecolor{orangefire}{HTML}{F97316}
\definecolor{freshgreen}{HTML}{16A34A}
\definecolor{skyblue}{HTML}{0284C7}
\definecolor{violetpop}{HTML}{7C3AED}
\definecolor{warmpaper}{HTML}{FFF7ED}
\definecolor{softmint}{HTML}{ECFDF5}
\definecolor{softblue}{HTML}{EFF6FF}
\definecolor{inkgray}{HTML}{374151}
\definecolor{linegray}{HTML}{CBD5E1}

\hypersetup{colorlinks=true,linkcolor=deepnavy,urlcolor=skyblue}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.35em}
\linespread{1.12}

\pagestyle{fancy}
\fancyhf{}
\lhead{\textcolor{deepnavy}{施工章节测试}}
\rhead{\textcolor{hotpink}{无解析刷题版}}
\cfoot{\textcolor{inkgray}{第 \thepage\ 页 / 共 \pageref{LastPage} 页}}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{orangefire}\leaders\hrule height \headrulewidth\hfill}}

\titleformat{\section}
  {\Large\bfseries\color{deepnavy}}
  {\thesection\quad}
  {0pt}
  {}
\titlespacing*{\section}{0pt}{1.2em}{0.6em}
\newcommand{\sectionbanner}[1]{%
  \vspace{0.2em}%
  \begin{tcolorbox}[enhanced,colback=deepnavy,colframe=orangefire,boxrule=0pt,arc=3mm,left=3mm,right=3mm,top=2mm,bottom=2mm,borderline west={3pt}{0pt}{hotpink}]
  {\color{white}\Large\bfseries #1}
  \end{tcolorbox}%
}

\newcommand{\choice}[1]{%
  \tcbox[
    on line,
    colback=hotpink!12,
    colframe=hotpink,
    boxrule=0.5pt,
    arc=1.2mm,
    left=1.2mm,
    right=1.2mm,
    top=0.2mm,
    bottom=0.2mm
  ]{\textbf{\textcolor{hotpink}{#1}}}%
}

\newcommand{\questionstem}[1]{%
  \textbf{\textcolor{deepnavy}{#1}}\par\vspace{0.35em}
}

\newcommand{\answerarea}[1]{%
  \vspace{0.25em}
  \begin{tcolorbox}[
    enhanced,
    colback=white,
    colframe=linegray,
    boxrule=0.45pt,
    arc=1.5mm,
    height=#1,
    left=2mm,
    right=2mm,
    top=1mm,
    bottom=1mm
  ]
  \textcolor{linegray}{作答区}
  \end{tcolorbox}
}

\newtcolorbox{questionbox}[2]{
  enhanced,
  breakable,
  colback=softblue,
  colframe=skyblue,
  boxrule=0.75pt,
  arc=2mm,
  left=3mm,
  right=3mm,
  top=3mm,
  bottom=2mm,
  before skip=0.85em,
  after skip=0.9em,
  fonttitle=\bfseries,
  title={\textcolor{white}{#1}\hfill\textcolor{white}{#2}},
  coltitle=white,
  colbacktitle=skyblue,
  boxed title style={
    colback=skyblue,
    colframe=skyblue,
    arc=2mm,
    boxrule=0pt
  },
  borderline west={2.4pt}{0pt}{hotpink}
}

\begin{document}
"""


def cover(total_questions: int, total_chapters: int) -> str:
    return rf"""
\begin{{titlepage}}
\begin{{tcolorbox}}[
  enhanced,
  colback=deepnavy,
  colframe=deepnavy,
  arc=0mm,
  boxrule=0pt,
  height=\textheight,
  valign=center,
  left=9mm,
  right=9mm
]
{{\Huge\bfseries\textcolor{{white}}{{施工章节测试}}}}\par
\vspace{{0.45em}}
{{\Huge\bfseries\textcolor{{orangefire}}{{无解析刷题版}}}}\par
\vspace{{1.2em}}
{{\Large\textcolor{{white}}{{只保留题目、选项、图片和作答区；不含答案，不含解析。}}}}\par
\vspace{{2.2em}}
\begin{{tcolorbox}}[
  colback=white,
  colframe=orangefire,
  arc=2mm,
  boxrule=0.8pt,
  width=0.72\linewidth
]
\Large
\textcolor{{deepnavy}}{{章节数：}}\textbf{{{total_chapters}}}\quad
\textcolor{{deepnavy}}{{题目数：}}\textbf{{{total_questions}}}\par
\vspace{{0.5em}}
\textcolor{{hotpink}}{{建议用法：}}先独立作答，再回看课堂资料核对。
\end{{tcolorbox}}
\vfill
\textcolor{{white!80}}{{由当前 cy 章节测试源文件重新整理生成}}
\end{{tcolorbox}}
\end{{titlepage}}
\tableofcontents
\newpage
"""


def build_document(chapters: list[dict], shuffled: bool = False) -> str:
    total_questions = sum(len(ch["questions"]) for ch in chapters)
    parts = [preamble(), cover(total_questions, len(chapters))]
    serial = 1
    rng = random.Random(20260613)

    for chapter in chapters:
        questions = list(chapter["questions"])
        if shuffled:
            rng.shuffle(questions)
        title = chapter["title"]
        if shuffled:
            title = f"{title}（本章乱序）"
        parts.append(rf"\section{{{tex_escape(title)}}}")
        parts.append(
            rf"\textcolor{{inkgray}}{{本章共 {len(questions)} 题。此版本不含答案与解析，请直接作答。}}"
        )
        for question in questions:
            parts.append(write_question(question, serial))
            serial += 1

    parts.append(r"\end{document}" + "\n")
    return "\n\n".join(parts)


def write_project() -> None:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    IMAGE_DIR.mkdir(parents=True)

    chapters = [parse_chapter(path) for path in CY_DIR.glob("*.md")]
    chapters.sort(key=lambda item: item["rank"])

    normal_tex = build_document(chapters, shuffled=False)
    shuffled_tex = build_document(chapters, shuffled=True)
    main_tex = normal_tex

    (PROJECT_DIR / "01_施工章节测试_无解析刷题版.tex").write_text(normal_tex, encoding="utf-8")
    (PROJECT_DIR / "02_施工章节测试_无解析刷题乱序版.tex").write_text(shuffled_tex, encoding="utf-8")
    (PROJECT_DIR / "main.tex").write_text(main_tex, encoding="utf-8")
    (PROJECT_DIR / "README.md").write_text(
        "# 施工章节测试无解析刷题版\n\n"
        "- `01_施工章节测试_无解析刷题版.tex`：按章节顺序排版。\n"
        "- `02_施工章节测试_无解析刷题乱序版.tex`：每章内题目乱序。\n"
        "- 编译器请选择 XeLaTeX。\n"
        "- 本包不含答案、不含解析，适合刷题自测。\n",
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
