from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


@dataclass
class ImageRef:
    filename: str
    caption: str = ""
    alt: str = ""


@dataclass
class Option:
    letter: str
    text: str
    images: list[ImageRef] = field(default_factory=list)


@dataclass
class Question:
    number: int
    kind: str
    prompt: str
    options: list[Option] = field(default_factory=list)
    answer: str = ""
    images: list[ImageRef] = field(default_factory=list)


@dataclass
class Exam:
    source_name: str
    title: str
    course: str
    questions: list[Question]


class Node:
    def __init__(self, tag: str, attrs: dict[str, str] | None = None, parent: "Node | None" = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list[Node | str] = []
        self.parent = parent


class TinyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("document")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), dict(attrs), self.current)
        self.current.children.append(node)
        if tag.lower() not in {"br", "img", "meta", "link", "hr", "input"}:
            self.current = node

    def handle_endtag(self, tag):
        tag = tag.lower()
        cur = self.current
        while cur.parent is not None:
            if cur.tag == tag:
                self.current = cur.parent
                return
            cur = cur.parent

    def handle_data(self, data):
        self.current.children.append(data)

    def handle_entityref(self, name):
        self.current.children.append(f"&{name};")

    def handle_charref(self, name):
        self.current.children.append(f"&#{name};")


def has_class(node: Node, class_name: str) -> bool:
    return class_name in node.attrs.get("class", "").split()


def iter_nodes(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        if isinstance(child, Node):
            yield from iter_nodes(child)


def find_first(node: Node, tag: str | None = None, class_name: str | None = None) -> Node | None:
    for candidate in iter_nodes(node):
        if tag is not None and candidate.tag != tag:
            continue
        if class_name is not None and not has_class(candidate, class_name):
            continue
        return candidate
    return None


def find_all(node: Node, tag: str | None = None, class_name: str | None = None) -> list[Node]:
    found = []
    for candidate in iter_nodes(node):
        if tag is not None and candidate.tag != tag:
            continue
        if class_name is not None and not has_class(candidate, class_name):
            continue
        found.append(candidate)
    return found


def has_ancestor(node: Node, class_name: str) -> bool:
    cur = node.parent
    while cur is not None:
        if has_class(cur, class_name):
            return True
        cur = cur.parent
    return False


def text_content(node: Node | None) -> str:
    if node is None:
        return ""
    parts: list[str] = []

    def walk(cur: Node | str):
        if isinstance(cur, str):
            parts.append(unescape(cur))
            return
        if cur.tag == "br":
            parts.append("\n")
            return
        for child in cur.children:
            walk(child)

    walk(node)
    text = "".join(parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", stem)
    return stem.strip("_") or "exam"


def decode_data_image(src: str, out_dir: Path, prefix: str, index: int) -> str | None:
    match = re.match(r"data:image/([a-zA-Z0-9.+-]+);base64,(.*)", src, re.S)
    if not match:
        return None
    ext = match.group(1).lower().replace("jpeg", "jpg")
    filename = f"{prefix}_img_{index:02d}.{ext}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / filename).write_bytes(base64.b64decode(match.group(2)))
    return filename


def parse_exam_file(path: Path, figures_dir: Path) -> Exam:
    raw = path.read_text(encoding="utf-8-sig")
    parser = TinyHTMLParser()
    parser.feed(raw)
    root = parser.root
    title = text_content(find_first(root, "h1")) or path.stem
    subtitle = text_content(find_first(root, class_name="xy-print-subtitle"))
    course = subtitle.replace("课程：", "").strip() if subtitle.startswith("课程：") else subtitle
    questions: list[Question] = []
    image_counter = 1
    prefix = safe_stem(path.name)

    def image_from_figure(figure: Node) -> list[ImageRef]:
        nonlocal image_counter
        refs: list[ImageRef] = []
        caption = text_content(find_first(figure, "figcaption"))
        for img in find_all(figure, "img"):
            filename = decode_data_image(img.attrs.get("src", ""), figures_dir, prefix, image_counter)
            if filename:
                refs.append(ImageRef(filename=filename, caption=caption, alt=img.attrs.get("alt", "")))
                image_counter += 1
        return refs

    def extract_images(container: Node) -> list[ImageRef]:
        refs: list[ImageRef] = []
        for figure in find_all(container, class_name="xy-print-image"):
            refs.extend(image_from_figure(figure))
        return refs

    for section in find_all(root, "section", "xy-print-question"):
        header = text_content(find_first(section, "h3"))
        match = re.match(r"(\d+)\.\s*\[(.*?)\]", header)
        number = int(match.group(1)) if match else len(questions) + 1
        kind = match.group(2) if match else header
        prompt_images = []
        used_figures: set[int] = set()
        for figure in find_all(section, class_name="xy-print-image"):
            if has_ancestor(figure, "xy-print-option") or has_ancestor(figure, "xy-print-answer"):
                continue
            prompt_images.extend(image_from_figure(figure))
            used_figures.add(id(figure))
        title_node = find_first(section, class_name="xy-print-title")
        prompt = text_content(title_node)
        if prompt_images:
            prompt = re.sub(r"(\s*\[?图片\]?\s*)+$", "", prompt).strip()
        options: list[Option] = []
        for option_node in find_all(section, class_name="xy-print-option"):
            letter = text_content(find_first(option_node, class_name="xy-print-option-letter")).rstrip(".")
            option_images = extract_images(option_node)
            letter_node = find_first(option_node, class_name="xy-print-option-letter")
            if letter_node and letter_node in option_node.children:
                option_node.children.remove(letter_node)
            option_text = text_content(option_node)
            if option_images and option_text.strip() in {"[图片]", "图片"}:
                option_text = ""
            options.append(Option(letter=letter, text=option_text, images=option_images))
        answer = text_content(find_first(section, class_name="xy-print-answer"))
        answer = re.sub(r"^答案[:：]\s*", "", answer).strip()
        questions.append(Question(number=number, kind=kind, prompt=prompt, options=options, answer=answer, images=prompt_images))
    return Exam(source_name=path.name, title=title, course=course, questions=questions)


def scan_exam_files(source_dir: Path, figures_dir: Path) -> list[Exam]:
    return [parse_exam_file(path, figures_dir) for path in sorted(source_dir.glob("*.doc"), key=lambda p: p.name)]


SPECIALS = {
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


def latex_escape(text: str) -> str:
    return "".join(SPECIALS.get(char, char) for char in text)


def tex_lines(text: str) -> str:
    return "\n\n".join(latex_escape(line.strip()) for line in text.splitlines() if line.strip()) or r"\emph{（空）}"


def document_preamble(title: str) -> str:
    return rf"""\documentclass[UTF8,zihao=-4,openany]{{ctexbook}}
\usepackage[a4paper,top=18mm,bottom=20mm,left=18mm,right=18mm,headheight=24pt]{{geometry}}
\usepackage{{fontspec}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\usepackage{{tcolorbox}}
\usepackage{{titlesec}}
\usepackage{{fancyhdr}}
\usepackage{{hyperref}}
\usepackage{{bookmark}}
\usepackage{{lastpage}}
\usepackage{{needspace}}
\usepackage{{tabularx}}
\usepackage{{array}}
\tcbuselibrary{{breakable,skins}}

\definecolor{{ink}}{{HTML}}{{1F2937}}
\definecolor{{muted}}{{HTML}}{{6B7280}}
\definecolor{{line}}{{HTML}}{{D1D5DB}}
\definecolor{{paper}}{{HTML}}{{F8FAFC}}
\definecolor{{brand}}{{HTML}}{{0F766E}}
\definecolor{{branddark}}{{HTML}}{{115E59}}
\definecolor{{softbrand}}{{HTML}}{{ECFDF5}}
\definecolor{{answer}}{{HTML}}{{EEF2FF}}
\definecolor{{answeredge}}{{HTML}}{{4338CA}}
\definecolor{{warn}}{{HTML}}{{B45309}}

\setmainfont{{Microsoft YaHei}}
\setsansfont{{Microsoft YaHei}}
\setCJKmainfont{{Microsoft YaHei}}
\setCJKsansfont{{Microsoft YaHei}}
\setCJKmonofont{{Microsoft YaHei}}
\hypersetup{{colorlinks=true,linkcolor=branddark,urlcolor=branddark,pdfauthor={{Codex}},pdftitle={{{latex_escape(title)}}}}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{4pt}}
\linespread{{1.08}}
\graphicspath{{{{figures/}}}}

\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{\small\color{{muted}} 桥梁工程期末复习}}
\rhead{{\small\color{{muted}} \leftmark}}
\cfoot{{\small\color{{muted}} 第 \thepage\ 页 / 共 \pageref*{{LastPage}} 页}}
\renewcommand{{\headrulewidth}}{{0.3pt}}
\renewcommand{{\headrule}}{{\hbox to\headwidth{{\color{{line}}\leaders\hrule height \headrulewidth\hfill}}}}

\titleformat{{\chapter}}[display]
  {{\sffamily\bfseries\Huge\color{{branddark}}}}
  {{\large\color{{brand}}\chaptertitlename\ \thechapter}}
  {{4pt}}
  {{}}
  [\vspace{{2pt}}{{\color{{brand}}\titlerule[1.2pt]}}]
\titlespacing*{{\chapter}}{{0pt}}{{-14pt}}{{14pt}}
\titleformat{{\section}}{{\sffamily\bfseries\Large\color{{branddark}}}}{{\thesection}}{{0.6em}}{{}}
\titlespacing*{{\section}}{{0pt}}{{10pt}}{{6pt}}

\newtcolorbox{{questionbox}}[2][]{{%
  enhanced,
  breakable,
  colback=white,
  colframe=line,
  boxrule=0.45pt,
  arc=2mm,
  left=3mm,
  right=3mm,
  top=2.6mm,
  bottom=2.6mm,
  before skip=7pt,
  after skip=7pt,
  borderline west={{1.2mm}}{{0pt}}{{brand}},
  title={{#2}},
  coltitle=ink,
  fonttitle=\sffamily\bfseries,
  attach boxed title to top left={{xshift=2mm,yshift=-2mm}},
  boxed title style={{colback=softbrand,colframe=brand,boxrule=0.35pt,arc=1.5mm,left=1.8mm,right=1.8mm,top=0.7mm,bottom=0.7mm}},
  #1
}}
\newtcolorbox{{answerbox}}{{%
  enhanced,
  breakable,
  colback=answer,
  colframe=answeredge,
  boxrule=0.45pt,
  arc=1.6mm,
  left=2.5mm,
  right=2.5mm,
  top=1.6mm,
  bottom=1.6mm,
  before skip=5pt,
  after skip=1pt,
  fontupper=\small
}}
\newtcolorbox{{answerline}}{{%
  enhanced,
  breakable,
  colback=paper,
  colframe=line,
  boxrule=0.35pt,
  arc=1.2mm,
  left=2mm,
  right=2mm,
  top=1.2mm,
  bottom=1.2mm,
  before skip=3pt,
  after skip=3pt,
  fontupper=\small
}}
\newenvironment{{choices}}{{\begin{{enumerate}}[label=\Alph*.,leftmargin=9mm,labelsep=3mm,itemsep=2pt,topsep=4pt]}}{{\end{{enumerate}}}}
\newcommand{{\qtype}}[1]{{\textcolor{{brand}}{{\sffamily\bfseries #1}}}}
\newcommand{{\sourcefile}}[1]{{\textcolor{{muted}}{{\small\sffamily 来源：#1}}}}
\newcommand{{\reviewfigure}}[2]{{%
  \begin{{center}}
  \includegraphics[width=0.92\linewidth,height=72mm,keepaspectratio]{{#1}}\\[-1mm]
  {{\scriptsize\color{{muted}} #2}}
  \end{{center}}
}}

\begin{{document}}
\frontmatter
\begin{{titlepage}}
\pagecolor{{paper}}
\vspace*{{22mm}}
{{\sffamily\bfseries\fontsize{{30}}{{36}}\selectfont\color{{branddark}} {latex_escape(title)}\par}}
\vspace{{5mm}}
{{\Large\color{{ink}} 桥梁工程期末考试复习题整理\par}}
\vspace{{10mm}}
{{\color{{brand}}\rule{{0.62\linewidth}}{{1.2pt}}\par}}
\vspace{{9mm}}
{{\large\color{{muted}} 由 D:\textbackslash zy 原始题卡自动整理，保留原文件顺序、题目顺序、答案与内嵌图片。\par}}
\vfill
{{\sffamily\color{{muted}} 编译方式：XeLaTeX \quad 页面：A4 \quad 字体：微软雅黑 / Times New Roman\par}}
\end{{titlepage}}
\nopagecolor
\tableofcontents
\mainmatter
"""


def question_title(global_number: int, question: Question) -> str:
    return f"第 {global_number} 题 · {question.kind}"


def render_question(question: Question, global_number: int, inline_answers: bool) -> str:
    parts = [rf"\Needspace{{7\baselineskip}}", rf"\begin{{questionbox}}{{{latex_escape(question_title(global_number, question))}}}"]
    parts.append(rf"\qtype{{{latex_escape(question.kind)}}}\quad {tex_lines(question.prompt)}")
    for image in question.images:
        caption = image.caption or image.alt or "题目图片"
        parts.append(rf"\reviewfigure{{{latex_escape(image.filename)}}}{{{latex_escape(caption)}}}")
    if question.options:
        parts.append(r"\begin{choices}")
        for option in question.options:
            option_parts = []
            if option.text:
                option_parts.append(tex_lines(option.text))
            for image in option.images:
                caption = image.caption or image.alt or "选项图片"
                option_parts.append(rf"\reviewfigure{{{latex_escape(image.filename)}}}{{{latex_escape(caption)}}}")
            parts.append(rf"\item {' '.join(option_parts) if option_parts else r'\emph{（图片选项）}'}")
        parts.append(r"\end{choices}")
    if inline_answers:
        answer = question.answer or "原题未提供答案"
        parts.append(r"\begin{answerbox}")
        parts.append(rf"\textbf{{答案：}} {tex_lines(answer)}")
        parts.append(r"\end{answerbox}")
    parts.append(r"\end{questionbox}")
    return "\n".join(parts)


def render_answer_entry(exam_index: int, exam: Exam, question: Question, global_number: int) -> str:
    answer = question.answer or "原题未提供答案"
    title = f"{global_number}. {exam.title} - 原第 {question.number} 题 [{question.kind}]"
    return "\n".join([
        r"\begin{answerline}",
        rf"\textbf{{{latex_escape(title)}}}\\",
        tex_lines(answer),
        r"\end{answerline}",
    ])


def build_latex_document(exams: list[Exam], mode: str) -> str:
    if mode not in {"inline", "appendix"}:
        raise ValueError("mode must be 'inline' or 'appendix'")
    title = "桥梁工程期末复习题（题后答案版）" if mode == "inline" else "桥梁工程期末复习题（答案汇总版）"
    parts = [document_preamble(title)]
    answer_parts: list[str] = []
    global_number = 1
    for exam_index, exam in enumerate(exams, start=1):
        parts.append(rf"\chapter{{{latex_escape(exam.title)}}}")
        if exam.course:
            parts.append(rf"\sourcefile{{{latex_escape(exam.source_name)}}}\quad \textcolor{{muted}}{{\small\sffamily 课程：{latex_escape(exam.course)}}}")
        else:
            parts.append(rf"\sourcefile{{{latex_escape(exam.source_name)}}}")
        for question in exam.questions:
            parts.append(render_question(question, global_number, inline_answers=(mode == "inline")))
            answer_parts.append(render_answer_entry(exam_index, exam, question, global_number))
            global_number += 1
    if mode == "appendix":
        parts.append(r"\backmatter")
        parts.append(r"\chapter{答案汇总}")
        parts.append(r"\textcolor{muted}{\small 答案按正文全局题号排列，并保留原试卷标题与原题号，便于回查。}")
        parts.extend(answer_parts)
    parts.append(r"\end{document}")
    return "\n\n".join(parts)


def write_outputs(source_dir: Path, output_dir: Path) -> tuple[Path, Path, list[Exam]]:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    exams = scan_exam_files(source_dir, figures_dir)
    inline_path = output_dir / "bridge_review_inline_answers.tex"
    appendix_path = output_dir / "bridge_review_answers_at_end.tex"
    inline_path.write_text(build_latex_document(exams, "inline"), encoding="utf-8")
    appendix_path.write_text(build_latex_document(exams, "appendix"), encoding="utf-8")
    return inline_path, appendix_path, exams


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build LaTeX review books from exported HTML-in-DOC exam cards.")
    parser.add_argument("--source", default=r"D:\zy")
    parser.add_argument("--out", default=r"D:\xm\zy_latex_work")
    args = parser.parse_args()
    inline_path, appendix_path, exams = write_outputs(Path(args.source), Path(args.out))
    question_count = sum(len(exam.questions) for exam in exams)
    image_count = sum(
        len(question.images) + sum(len(option.images) for option in question.options)
        for exam in exams
        for question in exam.questions
    )
    print(f"Wrote {inline_path}")
    print(f"Wrote {appendix_path}")
    print(f"Parsed {len(exams)} files, {question_count} questions, {image_count} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
