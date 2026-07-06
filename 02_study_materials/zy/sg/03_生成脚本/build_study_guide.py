from __future__ import annotations

import html
import json
import random
import re
import shutil
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
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
CY_DIR = SOURCE_DIR / "cy"
PPT_DIR = SOURCE_DIR / "ppt"
OUT_DIR = PROJECTS_DIR / "latex_out"
OUT_DIR.mkdir(exist_ok=True)
OVERLEAF_DIR = PROJECTS_DIR / "overleaf_project"
IMAGE_DIR = OVERLEAF_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

CHAPTER_RANK = {
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


def tex_escape(text: str) -> str:
    if text is None:
        return ""
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


def normalize_ws(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def clean_markdown_text(text: str) -> str:
    text = html.unescape(text)
    replacements = {
        r"\(": "",
        r"\)": "",
        r"\[": "[",
        r"\]": "]",
        r"\.": ".",
        r"\+": "+",
        r"\%": "%",
        r"\_": "_",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+([，。；：！？、）])", r"\1", text)
    text = re.sub(r"([（])\s+", r"\1", text)
    return normalize_ws(text)


def image_id_from_url(url: str) -> str:
    m = re.search(r"/file_access/(\d+)", url)
    if m:
        return m.group(1)
    return re.sub(r"\W+", "_", url)[:40]


def sniff_image_extension(data: bytes, content_type: str = "") -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if "png" in content_type:
        return ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    return ".png"


def download_image(url: str) -> str:
    img_id = image_id_from_url(url)
    existing = list(IMAGE_DIR.glob(f"{img_id}.*"))
    if existing:
        return f"images/{existing[0].name}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            ext = sniff_image_extension(data, response.headers.get("Content-Type", ""))
    except (urllib.error.URLError, TimeoutError) as exc:
        marker = IMAGE_DIR / f"{img_id}.missing.txt"
        marker.write_text(f"Failed to download image:\n{url}\n{exc}\n", encoding="utf-8")
        return ""
    target = IMAGE_DIR / f"{img_id}{ext}"
    target.write_bytes(data)
    return f"images/{target.name}"


def chapter_rank(title: str) -> int:
    for prefix, rank in CHAPTER_RANK.items():
        if title.startswith(prefix):
            return rank
    return 999


def chapter_short_title(title: str) -> str:
    return title.replace("章节测试", "").strip()


def parse_chapter_test(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()

    blocks = re.split(r"(?m)^###\s+", text)
    questions = []
    for block in blocks[1:]:
        lines = [line.rstrip() for line in block.splitlines()]
        if not lines:
            continue
        first = lines[0]
        m = re.match(r"(\d+)\.\s*(.*)", first)
        if not m:
            continue
        num = int(m.group(1))
        stem_parts = [m.group(2).strip()]
        options = []
        images = []
        answer = ""
        mode = "stem"
        for line in lines[1:]:
            s = line.strip()
            if not s:
                continue
            markdown_image = re.match(r"!\[[^\]]*\]\((https?://[^)]+)\)", s)
            if markdown_image:
                local_path = download_image(markdown_image.group(1))
                if local_path:
                    images.append(local_path)
                continue
            if s.startswith("- "):
                mode = "options"
                optm = re.match(r"-\s*([A-E])\.\s*(.*)", s)
                if optm:
                    options.append((optm.group(1), clean_markdown_text(optm.group(2))))
                continue
            if s.startswith("答案：") or s.startswith("绛旀锛"):
                answer = s.split("：", 1)[-1].strip()
                continue
            if mode == "stem":
                stem_parts.append(s)
        stem = clean_markdown_text(" ".join(stem_parts))
        stem = re.sub(r"!\[[^\]]*\]\(https?://[^)]+\)", "", stem)
        stem = re.sub(r"\\?\[图片:\d+\\?\]", "（见下图）", stem)
        stem = clean_markdown_text(stem)
        questions.append(
            {
                "num": num,
                "stem": stem,
                "options": options,
                "answer": answer,
                "images": images,
            }
        )
    return {"file": path.name, "title": title, "questions": questions}


def extract_ppt_slides(path: Path) -> list[list[str]]:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    slides = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        names.sort(key=lambda s: int(re.search(r"(\d+)", s).group(1)))
        for name in names:
            root = ET.fromstring(zf.read(name))
            texts = [normalize_ws(t.text) for t in root.findall(".//a:t", ns) if t.text and normalize_ws(t.text)]
            slides.append(texts)
    return slides


def summarize_ppt(path: Path) -> dict:
    slides = extract_ppt_slides(path)
    title = path.stem
    bullets: list[str] = []
    seen = set()
    for slide in slides:
        for t in slide:
            if not t or t in {"如切如磋", "如琢如磨", "如切如磋 如琢如磨"}:
                continue
            if t.isdigit():
                continue
            if t in seen:
                continue
            seen.add(t)
            bullets.append(t)
    return {"file": path.name, "title": title, "slides": slides, "bullets": bullets}


def latex_preamble() -> str:
    return r"""
\documentclass[UTF8,fontset=fandol,11pt]{ctexart}
\usepackage[a4paper,margin=1.75cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{enumitem}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{tabularx}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{array}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
\pagestyle{fancy}
\fancyhf{}
\lhead{\small 工程管理复习讲义}
\rhead{\small \thepage}
\setlength{\parindent}{0pt}
\setlist[enumerate]{leftmargin=2em,itemsep=0.3em}
\setlist[itemize]{leftmargin=1.8em,itemsep=0.2em}
\definecolor{mainblue}{HTML}{2454D6}
\definecolor{deepblue}{HTML}{13204B}
\definecolor{softblue}{HTML}{EEF5FF}
\definecolor{mainpurple}{HTML}{7B2CBF}
\definecolor{softpurple}{HTML}{F5ECFF}
\definecolor{mainorange}{HTML}{F77F00}
\definecolor{softorange}{HTML}{FFF3E0}
\definecolor{maingreen}{HTML}{138A36}
\definecolor{softgreen}{HTML}{EAF8ED}
\definecolor{answerred}{HTML}{D62828}
\newtcolorbox{mainbox}[1][]{enhanced,colback=softblue,colframe=mainblue,boxrule=0.9pt,arc=2mm,left=2.5mm,right=2.5mm,top=1.5mm,bottom=1.5mm,#1}
\newtcolorbox{quizbox}[1][]{enhanced,breakable,colback=white,colframe=mainpurple,coltitle=white,colbacktitle=mainpurple,fonttitle=\bfseries,boxrule=0.8pt,arc=2mm,left=2.8mm,right=2.8mm,top=1.6mm,bottom=1.6mm,#1}
\newtcolorbox{answerbox}[1][]{enhanced,breakable,colback=softgreen,colframe=maingreen,coltitle=white,colbacktitle=maingreen,fonttitle=\bfseries,boxrule=0.7pt,arc=2mm,left=2.5mm,right=2.5mm,top=1mm,bottom=1mm,#1}
\newtcolorbox{reviewbox}[1][]{enhanced,breakable,colback=softorange,colframe=mainorange,coltitle=white,colbacktitle=mainorange,fonttitle=\bfseries,boxrule=0.7pt,arc=2mm,left=2.5mm,right=2.5mm,top=1mm,bottom=1mm,#1}
\newcommand{\chaptertitle}[1]{\vspace{0.5em}\begin{tcolorbox}[enhanced,colback=deepblue,colframe=deepblue,arc=2mm,boxrule=0pt]\begin{center}\Large\bfseries\color{white}#1\end{center}\end{tcolorbox}\vspace{0.5em}}
\newcommand{\sectitle}[1]{\vspace{0.5em}\noindent{\Large\bfseries\color{mainblue}#1}\par\vspace{0.25em}{\color{mainorange}\hrule height 1.2pt}\vspace{0.45em}}
\newcommand{\answerline}{\textcolor{answerred}{\rule{2.4cm}{0.7pt}}}
""".strip()


def render_question(q: dict, with_answer: bool, chapter_title: str = "", with_explanation: bool = False) -> str:
    parts = [
        fr"\begin{{quizbox}}[title={{第 {q['num']} 题}}]",
        tex_escape(q["stem"]) + r"\\",
    ]
    for image_path in q.get("images", []):
        parts.append(r"\begin{center}")
        parts.append(r"\includegraphics[width=0.9\linewidth,height=0.32\textheight,keepaspectratio]{" + tex_escape(image_path) + r"}")
        parts.append(r"\end{center}")
    if q["options"]:
        parts.append(r"\begin{enumerate}[label=\Alph*.]")
        for _, opt in q["options"]:
            parts.append(latex_item(opt))
        parts.append(r"\end{enumerate}")
    if with_answer:
        parts.append(r"\textbf{答案：} " + tex_escape(q["answer"] or "未标注"))
        if with_explanation:
            parts.append(r"\vspace{0.25em}")
            parts.append(r"\begin{answerbox}[title={考点解析}]")
            parts.append(build_explanation(chapter_title, q))
            parts.append(r"\end{answerbox}")
    else:
        parts.append(r"\textbf{\textcolor{answerred}{答案：}} \answerline")
    parts.append(r"\end{quizbox}")
    return "\n".join(parts)


def latex_item(text: str) -> str:
    escaped = tex_escape(text)
    if escaped.startswith("["):
        escaped = r"\relax{}" + escaped
    return r"\item " + escaped


def detect_question_type(q: dict) -> str:
    text = q["stem"]
    if any(k in text for k in ["计算", "多少", "最早", "总时差", "自由时差", "含水量", "工程量", "强度"]):
        return "计算与参数判定"
    if any(k in text for k in ["安全", "危大", "专项施工方案", "专家论证", "脚手架"]):
        return "安全管理与规范要求"
    if any(k in text for k in ["质量", "验收", "验槽", "检测", "合格", "压实"]):
        return "质量验收与检测"
    if any(k in text for k in ["施工", "工艺", "开挖", "回填", "浇筑", "张拉", "砌筑", "抹灰", "防水"]):
        return "施工工艺与顺序"
    if any(k in text for k in ["组织", "单位", "负责人", "总监理工程师", "建设单位", "施工单位"]):
        return "组织程序与责任主体"
    return "基本概念与适用条件"


def answer_option_text(q: dict) -> list[str]:
    answer = q.get("answer") or ""
    option_map = {label: text for label, text in q.get("options", [])}
    return [f"{label}. {option_map[label]}" for label in answer if label in option_map]


def distractor_summary(q: dict) -> list[str]:
    answer = set(q.get("answer") or "")
    lines = []
    for label, text in q.get("options", []):
        if label not in answer:
            lines.append(f"{label}. {text}")
    return lines[:4]


def build_explanation(chapter_title: str, q: dict) -> str:
    qtype = detect_question_type(q)
    correct = answer_option_text(q)
    chapter = chapter_short_title(chapter_title)
    lines = [
        rf"\textbf{{考点：}} {tex_escape(chapter)}中的{tex_escape(qtype)}。",
    ]
    if correct:
        lines.append(r"\textbf{解析：} 本题应抓住题干关键词，正确选项对应教材或课件中的核心表述：")
        lines.append(r"\begin{itemize}")
        for item in correct:
            lines.append(latex_item(item))
        lines.append(r"\end{itemize}")
    else:
        lines.append(r"\textbf{解析：} 原题未给出可查答案，建议按题干关键词回到对应章节的课件重点中定位。")
    distractors = distractor_summary(q)
    if distractors:
        lines.append(r"\textbf{排除提示：} 其余选项多属于概念混淆、适用条件不符或责任主体错误，复习时重点对照下列干扰项：")
        lines.append(r"\begin{itemize}")
        for item in distractors:
            lines.append(latex_item(item))
        lines.append(r"\end{itemize}")
    if qtype == "计算与参数判定":
        lines.append(r"\textbf{记忆方法：} 先辨认题型，再列公式或时间参数，最后代入单位；不要只凭数字选项猜答案。")
    elif qtype == "施工工艺与顺序":
        lines.append(r"\textbf{记忆方法：} 按“准备条件—施工顺序—质量控制—成品保护”四步背。")
    elif qtype == "安全管理与规范要求":
        lines.append(r"\textbf{记忆方法：} 把责任主体、审批签字、论证条件和实施前提分开记。")
    elif qtype == "质量验收与检测":
        lines.append(r"\textbf{记忆方法：} 关注“谁组织、谁参加、用什么方法、合格后做什么”。")
    else:
        lines.append(r"\textbf{记忆方法：} 先背关键词，再背适用条件，最后用题目选项做反向检查。")
    return "\n".join(lines)


def chapter_banner(ch: dict) -> str:
    title = tex_escape(ch["title"])
    return "\n".join(
        [
            fr"\chaptertitle{{{title}}}",
            r"\begin{mainbox}",
            fr"\textbf{{\textcolor{{mainblue}}{{章节：}}}} {title}\\",
            fr"\textbf{{\textcolor{{answerred}}{{题量：}}}} {len(ch['questions'])} 题",
            r"\end{mainbox}",
        ]
    )


def flatten_questions(chapters: list[dict]) -> list[dict]:
    flat = []
    for ch in chapters:
        for q in ch["questions"]:
            item = dict(q)
            item["chapter_title"] = ch["title"]
            item["chapter_file"] = ch["file"]
            flat.append(item)
    return flat


def clip_text(text: str, limit: int = 150) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def key_terms_from_questions(questions: list[dict], limit: int = 10) -> list[str]:
    stop_words = {
        "以下", "关于", "正确", "错误", "说法", "的是", "的是", "工程", "施工", "可以", "应当", "必须",
        "采用", "进行", "下列", "符合", "要求", "单位", "答案", "问题", "其中", "分别", "有关",
    }
    counts: dict[str, int] = {}
    for q in questions:
        text = re.sub(r"[A-Za-z0-9\\/:：，。；、“”‘’（）()《》\[\]!\-_.]+", " ", q["stem"])
        for term in re.findall(r"[\u4e00-\u9fff]{2,8}", text):
            if term in stop_words or len(term) < 2:
                continue
            counts[term] = counts.get(term, 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def selected_ppt_points(ppts: list[dict], point_limit: int = 8) -> list[str]:
    points = []
    for p in ppts:
        for bullet in p["bullets"][:8]:
            if len(bullet) < 3:
                continue
            if bullet in points:
                continue
            points.append(f"{p['title']}：{clip_text(bullet, 95)}")
            if len(points) >= point_limit:
                return points
    return points


def typical_questions(questions: list[dict], limit: int = 6) -> list[dict]:
    priority_words = ["正确", "错误", "不宜", "应", "必须", "质量", "验收", "安全", "计算", "工期", "顺序"]
    scored = []
    for q in questions:
        score = sum(1 for word in priority_words if word in q["stem"])
        score += min(len(q["options"]), 5) * 0.1
        scored.append((score, q["num"], q))
    return [q for _, _, q in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]]


def normalize_tex_symbols(text: str) -> str:
    replacements = {
        "≤": r"$\leq$",
        "≥": r"$\geq$",
        "Ⅰ": "I",
        "Ⅱ": "II",
        "Ⅲ": "III",
        "①": "(1)",
        "②": "(2)",
        "③": "(3)",
        "④": "(4)",
        "⑤": "(5)",
        "⑥": "(6)",
        "⑦": "(7)",
        "⑧": "(8)",
        "⑨": "(9)",
        "﹤": "<",
        "﹥": ">",
        "△": r"$\triangle$",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def write_tex(path: Path, body: str) -> None:
    path.write_text(normalize_tex_symbols(body), encoding="utf-8")


def copy_to_overleaf(filename: str) -> None:
    shutil.copy2(OUT_DIR / filename, OVERLEAF_DIR / filename)


def write_overleaf_readme() -> None:
    text = """# 工程施工复习资料 Overleaf 项目

上传方式：
1. 打开 Overleaf，选择 New Project -> Upload Project。
2. 上传本目录打包得到的 `sg_overleaf_project.zip`。
3. Menu -> Compiler 选择 XeLaTeX。
4. 主文件建议选择 `main.tex`。

文件说明：
- `main.tex`：总入口，依次汇总练习版、乱序版、解析版、PPT提要、综合背诵版。
- `01_章节测验_无答案版.tex`：顺序练习。
- `01B_章节测验_乱序无答案版.tex`：乱序练习。
- `02_章节测验_解析版.tex`：含答案、考点、解析、排除提示、记忆方法。
- `03_PPT重点提要.tex`：PPT 重点提要。
- `04_PPT与章节测验综合版.tex`：重排后的综合背诵版。
- `images/`：章节测验中的网络计划图和表格图。
"""
    (OVERLEAF_DIR / "README.md").write_text(text, encoding="utf-8")


def render_overleaf_main(chapters: list[dict], ppts: list[dict], ppt_lookup: dict, chapter_to_keywords: dict) -> str:
    body = [
        latex_preamble(),
        r"\begin{document}",
        r"\chaptertitle{工程施工复习资料总册}",
        r"\begin{reviewbox}[title={使用说明}]",
        r"\textbf{说明：} 本文件是 Overleaf 上传后的默认主文件，已包含图片资源。若只想编译单独版本，可在 Overleaf 中切换主文件。\\",
        r"\textbf{学习顺序：} 先做无答案版，再刷乱序版，最后看解析版和综合背诵版。",
        r"\end{reviewbox}",
        r"\tableofcontents",
        r"\newpage",
    ]
    body.append(r"\section*{章节测验练习（无答案）}")
    body.append(r"\addcontentsline{toc}{section}{章节测验练习（无答案）}")
    for ch in chapters:
        body.append(chapter_banner(ch))
        for q in ch["questions"]:
            body.append(render_question(q, with_answer=False, chapter_title=ch["title"]))
    body.append(r"\newpage")

    body.append(r"\section*{章节测验解析（含考点）}")
    body.append(r"\addcontentsline{toc}{section}{章节测验解析（含考点）}")
    for ch in chapters:
        body.append(chapter_banner(ch))
        for q in ch["questions"]:
            body.append(render_question(q, with_answer=True, chapter_title=ch["title"], with_explanation=True))
    body.append(r"\newpage")

    body.append(r"\section*{PPT 与章节测验综合背诵}")
    body.append(r"\addcontentsline{toc}{section}{PPT 与章节测验综合背诵}")
    for ch in chapters:
        chap_name = ch["title"].split("章节测试")[0]
        body.append(fr"\subsection*{{{tex_escape(chap_name)}}}")
        keywords = chapter_to_keywords.get(chap_name[:3], [])
        matched = [ppt_lookup[k] for k in keywords if k in ppt_lookup]
        if matched:
            body.append(r"\sectitle{PPT 重点压缩}")
            body.append(r"\begin{reviewbox}")
            body.append(r"\begin{enumerate}[label=\arabic*.]")
            for point in selected_ppt_points(matched, point_limit=8):
                body.append(latex_item(point))
            body.append(r"\end{enumerate}")
            body.append(r"\end{reviewbox}")
        terms = key_terms_from_questions(ch["questions"], limit=12)
        if terms:
            body.append(r"\begin{mainbox}")
            body.append(r"\textbf{题目高频词：} " + tex_escape("、".join(terms)))
            body.append(r"\end{mainbox}")
        body.append(r"\begin{enumerate}[label=\arabic*.]")
        for q in typical_questions(ch["questions"], limit=6):
            answer = q.get("answer") or "未标注"
            body.append(latex_item(f"第{q['num']}题：{q['stem']}（答案：{answer}）"))
            for image_path in q.get("images", []):
                body.append(r"\begin{center}")
                body.append(r"\includegraphics[width=0.82\linewidth,height=0.24\textheight,keepaspectratio]{" + tex_escape(image_path) + r"}")
                body.append(r"\end{center}")
        body.append(r"\end{enumerate}")
        body.append(r"\newpage")
    body.append(r"\end{document}")
    return "\n\n".join(body)


def build():
    if OVERLEAF_DIR.exists():
        shutil.rmtree(OVERLEAF_DIR)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    chapters = [parse_chapter_test(p) for p in sorted(CY_DIR.glob("*.md"))]
    chapters.sort(key=lambda ch: chapter_rank(ch["title"]))
    ppts = [summarize_ppt(p) for p in sorted(PPT_DIR.glob("*.pptx"))]
    ppt_lookup = {p["file"].removesuffix(".pptx"): p for p in ppts}

    chapter_to_keywords = {
        "第一章": ["土方工程概述", "土方工程的机械化施工", "土方开挖", "土方回填", "地下水处理", "流砂及其防治", "基坑验槽方法", "边坡开挖"],
        "第二章": ["地基处理技术与桩的类型", "钢筋混凝土预制桩", "钢筋混凝土灌注桩", "桩基检测技术"],
        "第三章": ["基坑支护施工技术", "基坑监测", "基坑验槽方法", "地下水处理", "流砂及其防治", "边坡开挖", "危险性较大的分部分项工程安全管理规定"],
        "第四章": ["混凝土工程", "大体积混凝土工程", "模板工程", "钢筋工程"],
        "第五章": ["预应力混凝土概述", "预应力施加方法"],
        "第六章": ["砌筑砂浆", "砖砌体工程", "混凝土小型空心砌块砌体工程", "填充墙砌体工程", "砌筑工程季节性施工"],
        "第七章": ["脚手架的种类", "脚手架工程的安全技术要求", "危险性较大的分部分项工程安全管理规定"],
        "第八章": ["抹灰工程施工", "拓展：装饰工程"],
        "第九章": ["建筑防水材料的特性与应用", "屋面防水工程施工", "拓展：防水工程"],
        "第十章": ["有节奏流水施工", "非（无）节奏流水施工"],
        "第十一章": ["双代号网络计划1", "双代号网络计划2", "双代号时标网络计划", "网络优化"],
    }

    # 1. No-answer version
    body = [latex_preamble(), r"\begin{document}", r"\tableofcontents", r"\newpage", r"\chaptertitle{章节测验练习册（无答案版）}"]
    for ch in chapters:
        body.append(chapter_banner(ch))
        for q in ch["questions"]:
            body.append(render_question(q, with_answer=False, chapter_title=ch["title"]))
            body.append(r"\vspace{0.2em}")
    body.append(r"\end{document}")
    write_tex(OUT_DIR / "01_章节测验_无答案版.tex", "\n\n".join(body))

    # 1B. Randomized no-answer version
    shuffled = flatten_questions(chapters)
    random.Random(20260607).shuffle(shuffled)
    body = [
        latex_preamble(),
        r"\begin{document}",
        r"\tableofcontents",
        r"\newpage",
        r"\chaptertitle{章节测验练习册（乱序无答案版）}",
        r"\begin{mainbox}",
        r"\textbf{使用建议：} 乱序版用于二刷和考前自测。做完后按题目上方的章节标签回到解析版订正。",
        r"\end{mainbox}",
    ]
    for idx, q in enumerate(shuffled, 1):
        body.append(fr"\begin{{quizbox}}[title={{乱序第 {idx} 题｜{tex_escape(chapter_short_title(q['chapter_title']))}}}]")
        body.append(tex_escape(q["stem"]) + r"\\")
        for image_path in q.get("images", []):
            body.append(r"\begin{center}")
            body.append(r"\includegraphics[width=0.9\linewidth,height=0.32\textheight,keepaspectratio]{" + tex_escape(image_path) + r"}")
            body.append(r"\end{center}")
        if q["options"]:
            body.append(r"\begin{enumerate}[label=\Alph*.]")
            for _, opt in q["options"]:
                body.append(latex_item(opt))
            body.append(r"\end{enumerate}")
        body.append(r"\textbf{\textcolor{answerred}{答案：}} \answerline")
        body.append(r"\end{quizbox}")
        body.append(r"\vspace{0.2em}")
    body.append(r"\end{document}")
    write_tex(OUT_DIR / "01B_章节测验_乱序无答案版.tex", "\n\n".join(body))

    # 2. Explanation version
    body = [latex_preamble(), r"\begin{document}", r"\tableofcontents", r"\newpage", r"\chaptertitle{章节测验解析版（含考点解析）}"]
    for ch in chapters:
        body.append(chapter_banner(ch))
        for q in ch["questions"]:
            body.append(render_question(q, with_answer=True, chapter_title=ch["title"], with_explanation=True))
            body.append(r"\vspace{0.2em}")
    body.append(r"\end{document}")
    write_tex(OUT_DIR / "02_章节测验_解析版.tex", "\n\n".join(body))

    # 3. PPT notes
    body = [latex_preamble(), r"\begin{document}", r"\tableofcontents", r"\newpage", r"\chaptertitle{PPT 重点提要}"]
    for idx, p in enumerate(ppts, 1):
        body.append(fr"\section*{{{idx}. {tex_escape(p['title'])}}}")
        body.append(r"\addcontentsline{toc}{section}{" + tex_escape(f"{idx}. {p['title']}") + r"}")
        body.append(r"\begin{mainbox}")
        body.append(r"\textbf{提要：} 以下内容按课件自动提炼，适合快速背诵。")
        body.append(r"\end{mainbox}")
        body.append(r"\begin{enumerate}[label=\arabic*.]")
        for bullet in p["bullets"][:24]:
            body.append(latex_item(clip_text(bullet, 170)))
        body.append(r"\end{enumerate}")
        body.append(r"\newpage")
    body.append(r"\end{document}")
    write_tex(OUT_DIR / "03_PPT重点提要.tex", "\n\n".join(body))

    # 4. Combined version
    body = [
        latex_preamble(),
        r"\begin{document}",
        r"\tableofcontents",
        r"\newpage",
        r"\chaptertitle{PPT 与章节测验综合背诵版（重排美化版）}",
        r"\begin{mainbox}",
        r"\textbf{使用方式：} 每章先背“课件重点”，再用“高频词”抓题眼，最后做“典型练习”。这一版按背诵节奏重排，不再堆满原始材料。",
        r"\end{mainbox}",
        r"\newpage",
    ]
    for ch in chapters:
        chap_name = ch["title"].split("章节测试")[0]
        body.append(fr"\section*{{{tex_escape(chap_name)}}}")
        body.append(r"\addcontentsline{toc}{section}{" + tex_escape(chap_name) + r"}")
        body.append(r"\begin{mainbox}")
        body.append(fr"\textbf{{本章定位：}} 共 {len(ch['questions'])} 道章节题。先抓概念边界，再背工艺顺序、质量控制和责任主体。")
        body.append(r"\end{mainbox}")
        keywords = chapter_to_keywords.get(chap_name[:3], [])
        matched = [ppt_lookup[k] for k in keywords if k in ppt_lookup]
        if matched:
            body.append(r"\sectitle{一、PPT 重点压缩}")
            body.append(r"\begin{reviewbox}")
            body.append(r"\begin{enumerate}[label=\arabic*.]")
            for point in selected_ppt_points(matched, point_limit=8):
                body.append(latex_item(point))
            body.append(r"\end{enumerate}")
            body.append(r"\end{reviewbox}")

        terms = key_terms_from_questions(ch["questions"], limit=12)
        if terms:
            body.append(r"\sectitle{二、题目高频词}")
            body.append(r"\begin{mainbox}")
            body.append(r"\textbf{看到这些词要立刻回忆：} " + tex_escape("、".join(terms)))
            body.append(r"\end{mainbox}")

        body.append(r"\sectitle{三、典型练习题眼}")
        body.append(r"\begin{enumerate}[label=\arabic*.]")
        for q in typical_questions(ch["questions"], limit=8):
            answer = q.get("answer") or "未标注"
            body.append(latex_item(f"第{q['num']}题：{q['stem']}（答案：{answer}）"))
            for image_path in q.get("images", []):
                body.append(r"\begin{center}")
                body.append(r"\includegraphics[width=0.82\linewidth,height=0.24\textheight,keepaspectratio]{" + tex_escape(image_path) + r"}")
                body.append(r"\end{center}")
        body.append(r"\end{enumerate}")

        body.append(r"\sectitle{四、背诵口令}")
        body.append(r"\begin{reviewbox}")
        body.append(r"\begin{itemize}")
        body.append(latex_item("概念题：先背定义，再背适用条件。"))
        body.append(latex_item("工艺题：按施工顺序记，遇到“先后、分层、对称、及时”重点标记。"))
        body.append(latex_item("质量安全题：按责任主体、检查方法、合格条件、整改要求四步背。"))
        body.append(r"\end{itemize}")
        body.append(r"\end{reviewbox}")
        body.append(r"\newpage")
    body.append(r"\end{document}")
    write_tex(OUT_DIR / "04_PPT与章节测验综合版.tex", "\n\n".join(body))

    main_tex = render_overleaf_main(chapters, ppts, ppt_lookup, chapter_to_keywords)
    (OVERLEAF_DIR / "main.tex").write_text(normalize_tex_symbols(main_tex), encoding="utf-8")
    for filename in [
        "01_章节测验_无答案版.tex",
        "01B_章节测验_乱序无答案版.tex",
        "02_章节测验_解析版.tex",
        "03_PPT重点提要.tex",
        "04_PPT与章节测验综合版.tex",
    ]:
        copy_to_overleaf(filename)
    write_overleaf_readme()

    zip_base = BASE / "sg_overleaf_project"
    zip_path = shutil.make_archive(str(zip_base), "zip", root_dir=OVERLEAF_DIR)

    summary = {
        "chapters": len(chapters),
        "chapter_question_counts": {ch["title"]: len(ch["questions"]) for ch in chapters},
        "ppts": len(ppts),
        "images": len(list(IMAGE_DIR.glob("*.*"))),
        "overleaf_zip": zip_path,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
