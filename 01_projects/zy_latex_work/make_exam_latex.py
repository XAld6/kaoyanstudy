import re
from pathlib import Path


OUT = Path(r"D:\latex_exam_output")
TEXT = OUT / "normalized_text.txt"


def normalize_text(s: str) -> str:
    s = s.replace("\ufeff", "").replace("\xa0", " ")
    s = s.replace("　", " ")
    s = s.replace("巳知", "已知")
    s = s.replace("ｄ", "d").replace("Ｄ", "D").replace("Ｋ", "K")
    s = s.replace("／", "/").replace("％", "%")
    circled = {
        "①": "(1)", "②": "(2)", "③": "(3)", "④": "(4)", "⑤": "(5)",
        "⑥": "(6)", "⑦": "(7)", "⑧": "(8)", "⑨": "(9)", "⑩": "(10)",
    }
    for old, new in circled.items():
        s = s.replace(old, new)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def tex_escape(s: str) -> str:
    repl = {
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
    return "".join(repl.get(ch, ch) for ch in s)


def tex_text(s: str) -> str:
    parts = []
    last = 0
    for m in re.finditer(r"_+", s):
        parts.append(tex_escape(s[last : m.start()]))
        parts.append(r"\blankline{}")
        last = m.end()
    parts.append(tex_escape(s[last:]))
    return "".join(parts)


SECTION_NAMES = ("填空题", "选择题", "判断题", "名词解释", "简答题", "问答题", "论述题", "计算题", "分析论述题")


def is_section(line: str) -> bool:
    line = line.strip()
    return bool(re.match(r"^[一二三四五六七八九十]+[、.．]\s*(" + "|".join(SECTION_NAMES) + r")", line))


def is_answer_section(line: str) -> bool:
    return bool(re.match(r"^[一二三四五六七八九十]+[、.．]?\s*$", line.strip()))


def is_question_start(line: str) -> bool:
    return bool(re.match(r"^\s*(?:\d+|l)[、.．]\s*", line))


def split_first_embedded_section(line: str):
    m = re.search(r"([一二三四五六七八九十]+[、.．]\s*(?:" + "|".join(SECTION_NAMES) + r").*)", line)
    if m and m.start() > 0:
        return [line[: m.start()].strip(), line[m.start() :].strip()]
    return [line]


def preprocess_lines(text: str):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        for piece in split_first_embedded_section(line):
            if piece:
                out.append(piece)
    return out


def find_exam_starts(lines):
    starts = []
    for i, line in enumerate(lines):
        if i == 0:
            starts.append((i, "01"))
            continue
        m = re.search(r"试卷编号\s*[:：]?\s*(\d{2})", line)
        if m:
            no = m.group(1)
            is_answer = ("课程名称" in line) or ("标准答案" in line)
            if not is_answer:
                starts.append((i, no))
    # Deduplicate same line and sort
    seen = set()
    result = []
    for item in starts:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return sorted(result)


def parse_exam_blocks(lines):
    starts = find_exam_starts(lines)
    blocks = {}
    for idx, (start, no) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        blocks[no] = lines[start:end]
    return blocks


def split_questions_answers(block_lines, no):
    ans_idx = None
    for i, line in enumerate(block_lines):
        if i == 0 and no != "01":
            continue
        if ("课程名称" in line and f"试卷编号" in line) or "标准答案" in line or "长沙理工大学试卷标准答案" in line:
            ans_idx = i
            break
    if ans_idx is None:
        return block_lines, []
    q = block_lines[:ans_idx]
    a_line = block_lines[ans_idx]
    # Remove answer header from a line that also contains trailing question text.
    if "课程名称" in a_line:
        q_tail = a_line.split("课程名称", 1)[0].strip()
        if q_tail:
            q.append(q_tail)
    return q, block_lines[ans_idx + 1 :]


def parse_sections(lines, answer=False):
    sections = []
    current = None
    before = []
    for line in lines:
        if "课程名称" in line and "试卷编号" in line:
            continue
        if re.fullmatch(r"试卷编号\s*[:：]?\s*\d{2}.*", line):
            continue
        marker = (is_answer_section(line) or is_section(line)) if answer else is_section(line)
        if marker:
            current = {"title": line, "items": []}
            sections.append(current)
            continue
        if current is None:
            before.append(line)
        else:
            current["items"].append(line)
    return before, sections


def section_kind(title: str) -> str:
    for k in SECTION_NAMES:
        if k in title:
            return k
    return "其他"


def split_items(lines):
    items = []
    cur = []
    for line in lines:
        if is_question_start(line) and cur:
            items.append(cur)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        items.append(cur)
    return items


def split_answer_items(lines):
    # First try multi-answer same-line snippets: 1、A 2、B ...
    text = "\n".join(lines).strip()
    if not text:
        return []
    positions = list(re.finditer(r"(?<!\d)(\d+)[、.．]\s*", text))
    if len(positions) >= 2:
        items = []
        for idx, m in enumerate(positions):
            end = positions[idx + 1].start() if idx + 1 < len(positions) else len(text)
            items.append(text[m.start() : end].strip())
        return items
    return split_items(lines)


def extract_short_answers(section):
    answers = {}
    lines = section.get("items", [])
    for item in split_answer_items(lines):
        if isinstance(item, list):
            txt = " ".join(x.strip() for x in item).strip()
        else:
            txt = " ".join(x.strip() for x in item.splitlines()).strip()
        m = re.match(r"(\d+)[、.．]\s*(.*)", txt)
        if m:
            answers[int(m.group(1))] = m.group(2).strip()
    return answers


CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def sec_index(title):
    m = re.match(r"^\s*([一二三四五六七八九十]+)", title)
    if not m:
        return 0
    s = m.group(1)
    if s == "十":
        return 10
    if len(s) == 1:
        return CN_NUM.get(s, 0)
    return sum(CN_NUM.get(ch, 0) for ch in s)


def map_answers(answer_sections):
    by_index = {}
    for sec in answer_sections:
        idx = sec_index(sec["title"])
        kind = section_kind(sec["title"])
        if kind == "其他":
            # Answer sections are often just "一、". Match by order later.
            kind = None
        by_index[idx] = {"kind": kind, "section": sec, "short": extract_short_answers(sec)}
    return by_index


def answer_for_item(answer_info, n):
    if not answer_info:
        return ""
    short = answer_info.get("short", {})
    return short.get(n, "")


def fill_blanks(line, ans):
    if not ans:
        return line
    # Split answers on Chinese commas, semicolons, ASCII commas; keep longer prose intact when no blank count.
    blanks = list(re.finditer(r"_+", line))
    parts = [p.strip() for p in re.split(r"[、,，;；]|\s{2,}", ans) if p.strip()]
    if len(parts) == 1 and len(blanks) > 1 and "E0" in parts[0] and "CBR" in parts[0]:
        parts = ["回弹模量E0", "地基反应模量K", "CBR"]
    if not blanks or not parts:
        return line
    out = []
    last = 0
    for i, m in enumerate(blanks):
        out.append(tex_text(line[last : m.start()]))
        part = parts[i] if i < len(parts) else ""
        if part:
            out.append(r"\ans{" + tex_escape(part) + "}")
        else:
            out.append(r"\blankline{}")
        last = m.end()
    out.append(tex_text(line[last:]))
    return "".join(out)


def fill_parentheses(line, ans):
    if not ans:
        return line
    m = re.search(r"（\s*）|（\s+）|\(\s*\)", line)
    if not m:
        return tex_text(line)
    return tex_text(line[: m.start()]) + "（" + r"\ans{" + tex_escape(ans.replace(" ", "")) + r"}" + "）" + tex_text(line[m.end() :])


def line_to_tex(line, answer_mode=False, kind="", ans=""):
    if answer_mode and kind in ("填空题",):
        filled = fill_blanks(line, ans)
        return filled if filled != line else tex_text(line)
    if answer_mode and kind in ("选择题", "判断题"):
        filled = fill_parentheses(line, ans)
        return filled if filled != line else tex_text(line)
    return tex_text(line)


def render_item(item_lines, answer_mode, kind, ans):
    first = item_lines[0]
    n_match = re.match(r"\s*(\d+|l)[、.．]\s*(.*)", first)
    if n_match:
        num = n_match.group(1)
        body = n_match.group(2)
        if num == "l":
            num = "1"
        body_tex = line_to_tex(body, answer_mode, kind, ans)
        out = [rf"\item {body_tex}"]
    else:
        out = [line_to_tex(first, answer_mode, kind, ans)]

    option_buffer = []
    for line in item_lines[1:]:
        if re.match(r"^[A-E①②③④⑤]", line.strip()):
            option_buffer.append(line)
        else:
            if option_buffer:
                out.append(render_options(option_buffer))
                option_buffer = []
            out.append(line_to_tex(line, answer_mode, kind, ans))
    if option_buffer:
        out.append(render_options(option_buffer))

    if answer_mode and kind not in ("填空题", "选择题", "判断题") and ans:
        out.append(r"\begin{answerblock}" + "\n" + tex_escape(ans) + "\n" + r"\end{answerblock}")
    return "\n".join(out)


def render_options(lines):
    text = " ".join(lines)
    text = re.sub(r"\s+([A-E][．.])", r"@@OPT@@\1", text)
    text = re.sub(r"([。；;])\s*([A-E][．.])", r"\1@@OPT@@\2", text)
    text = re.sub(r"([^\s])([B-E][．.])", r"\1@@OPT@@\2", text)
    rendered = tex_text(text).replace("@@OPT@@", r"\hspace{1.65em}")
    return r"\begin{optionbox}" + rendered + r"\end{optionbox}"


TABLET_PREAMBLE = r"""\documentclass[UTF8,zihao=-4,openany]{ctexbook}
\usepackage[paperwidth=13.333in,paperheight=7.5in,top=0.56in,bottom=0.52in,left=0.72in,right=0.72in]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\usepackage{lastpage}
\usepackage{amsmath,amssymb}
\usepackage{tikz}
\usepackage{eso-pic}
\usepackage{multicol}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=neonblue,urlcolor=hotpink}
\definecolor{bg}{HTML}{F6F0FF}
\definecolor{ink}{HTML}{172033}
\definecolor{deepnavy}{HTML}{1B1B3A}
\definecolor{neonblue}{HTML}{176BFF}
\definecolor{cyanpop}{HTML}{00B8D9}
\definecolor{hotpink}{HTML}{E83E8C}
\definecolor{sun}{HTML}{FFB000}
\definecolor{mint}{HTML}{00B894}
\definecolor{card}{HTML}{FFFFFF}
\definecolor{softblue}{HTML}{EAF5FF}
\definecolor{softpink}{HTML}{FFF0F7}
\definecolor{softyellow}{HTML}{FFF7D6}
\definecolor{answerred}{HTML}{D7263D}
\definecolor{linegray}{HTML}{8DA2B8}
\setCJKmainfont[BoldFont=SimHei]{SimSun}
\setCJKsansfont{Microsoft YaHei}
\setmainfont{Times New Roman}
\linespread{1.12}
\setlength{\parskip}{0.18em}
\setlength{\headheight}{18pt}
\pagecolor{bg}
\pagestyle{fancy}
\fancyhf{}
\lhead{\sffamily\bfseries\color{deepnavy} 路基路面工程题库}
\rhead{\sffamily\color{neonblue} Tablet Edition}
\cfoot{\sffamily\color{deepnavy}\thepage/\pageref{LastPage}}
\renewcommand{\headrulewidth}{0pt}
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture,overlay]
    \fill[bg] (current page.south west) rectangle (current page.north east);
    \fill[neonblue!14] ([xshift=-2.2cm,yshift=1.1cm]current page.north east) circle (3.2cm);
    \fill[hotpink!12] ([xshift=1.0cm,yshift=-1.0cm]current page.south west) circle (2.9cm);
    \fill[sun!13] ([xshift=0.5cm,yshift=0.5cm]current page.south east) circle (1.9cm);
  \end{tikzpicture}%
}
\titleformat{\chapter}[display]{\sffamily\bfseries\Huge\color{deepnavy}}{}{0pt}{}
\titlespacing*{\chapter}{0pt}{-10pt}{18pt}
\titleformat{\section}{\sffamily\Large\bfseries\color{deepnavy}}{\thesection}{0.6em}{}
\titlespacing*{\section}{0pt}{1.2em}{0.55em}
\renewcommand{\contentsname}{快速导航}
\newcommand{\qnum}[1]{\tikz[baseline=(n.base)]\node[inner sep=2.5pt,minimum width=1.65em,rounded corners=5pt,fill=deepnavy,text=white,font=\sffamily\bfseries] (n) {#1};}
\setlist[enumerate]{leftmargin=3.45em,label=\protect\qnum{\arabic*},itemsep=0.78em,topsep=0.55em,parsep=0.24em}
\newcommand{\ans}[1]{\tikz[baseline=(a.base)]\node[inner xsep=5.2pt,inner ysep=2.1pt,rounded corners=4pt,fill=softyellow,draw=answerred!35,text=answerred,font=\bfseries] (a) {#1};}
\newcommand{\blankline}{\textcolor{linegray}{\rule{4.9em}{0.7pt}}}
\newtcolorbox{examcard}[1]{enhanced,breakable,colback=card,colframe=neonblue!45,boxrule=0.8pt,arc=4mm,drop fuzzy shadow=deepnavy!18,left=5.5mm,right=5.5mm,top=5mm,bottom=5mm,before skip=5mm,after skip=5mm,title={#1},fonttitle=\sffamily\bfseries\Large,coltitle=white,attach boxed title to top left={xshift=5mm,yshift=-3mm},boxed title style={arc=3mm,colback=neonblue,boxrule=0pt,left=4mm,right=4mm,top=1.3mm,bottom=1.3mm}}
\newtcolorbox{optionbox}{enhanced,breakable,colback=softblue,colframe=cyanpop!35,boxrule=0.4pt,arc=3mm,left=3.5mm,right=3.5mm,top=2.2mm,bottom=2.2mm,before skip=2.8mm,after skip=2.8mm}
\newenvironment{answerblock}{\begin{tcolorbox}[enhanced,breakable,colback=softpink,colframe=answerred!50,boxrule=0.8pt,arc=3mm,left=4mm,right=4mm,top=3mm,bottom=3mm,before skip=3mm,after skip=3mm,drop fuzzy shadow=answerred!10]\textcolor{answerred}{\sffamily\bfseries 答案：}}{\end{tcolorbox}}
\newcommand{\examtitle}[2]{%
  \clearpage
  \begin{tikzpicture}[remember picture,overlay]
    \fill[deepnavy] ([yshift=-0.15in]current page.north west) rectangle ([yshift=-1.42in]current page.north east);
    \fill[neonblue] ([xshift=0.72in,yshift=-0.52in]current page.north west) circle (0.26in);
    \fill[hotpink] ([xshift=1.10in,yshift=-0.93in]current page.north west) circle (0.13in);
    \node[anchor=west,text=white,font=\sffamily\bfseries\fontsize{32}{34}\selectfont] at ([xshift=1.5in,yshift=-0.66in]current page.north west) {试卷编号 #1};
    \node[anchor=west,text=cyanpop!90,font=\sffamily\bfseries\Large] at ([xshift=1.52in,yshift=-1.08in]current page.north west) {#2};
  \end{tikzpicture}
  \vspace*{1.12in}
}
\newcommand{\coverpage}[2]{%
  \begin{titlepage}
  \begin{tikzpicture}[remember picture,overlay]
    \fill[deepnavy] (current page.south west) rectangle (current page.north east);
    \fill[neonblue!80] ([xshift=-1.2in,yshift=0.6in]current page.north east) circle (2.1in);
    \fill[hotpink!80] ([xshift=0.7in,yshift=-0.5in]current page.south west) circle (1.7in);
    \fill[sun!90] ([xshift=-0.6in,yshift=-0.4in]current page.north east) circle (0.72in);
    \node[anchor=west,text=white,font=\sffamily\bfseries\fontsize{46}{50}\selectfont] at ([xshift=0.9in,yshift=-2.15in]current page.north west) {#1};
    \node[anchor=west,text=cyanpop,font=\sffamily\bfseries\fontsize{22}{24}\selectfont] at ([xshift=0.95in,yshift=-2.85in]current page.north west) {#2};
    \node[anchor=west,text=white!70,font=\sffamily\Large] at ([xshift=0.98in,yshift=0.85in]current page.south west) {Tablet Color Edition · 由原 Word 试题整理};
  \end{tikzpicture}
  \end{titlepage}
}
\newcommand{\tocintro}{%
  \begin{tikzpicture}[remember picture,overlay]
    \fill[deepnavy] ([yshift=-0.15in]current page.north west) rectangle ([yshift=-1.12in]current page.north east);
    \node[anchor=west,text=white,font=\sffamily\bfseries\fontsize{28}{30}\selectfont] at ([xshift=0.78in,yshift=-0.62in]current page.north west) {快速导航};
    \node[anchor=east,text=cyanpop,font=\sffamily\bfseries\Large] at ([xshift=-0.78in,yshift=-0.64in]current page.north east) {Tap / Jump / Review};
  \end{tikzpicture}
  \vspace*{0.78in}
}
\begin{document}
"""


A4_PREAMBLE = r"""\documentclass[UTF8,zihao=-4,openany]{ctexbook}
\usepackage[a4paper,top=2.0cm,bottom=1.8cm,left=1.8cm,right=1.8cm]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\usepackage{lastpage}
\usepackage{amsmath,amssymb}
\usepackage{tikz}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=mainblue,urlcolor=mainblue}
\definecolor{ink}{HTML}{172033}
\definecolor{mainblue}{HTML}{1F5EFF}
\definecolor{deepnavy}{HTML}{1B1B3A}
\definecolor{card}{HTML}{FFFFFF}
\definecolor{softblue}{HTML}{F2F7FF}
\definecolor{softpink}{HTML}{FFF3F7}
\definecolor{softyellow}{HTML}{FFF8D8}
\definecolor{answerred}{HTML}{D7263D}
\definecolor{linegray}{HTML}{7387A0}
\setCJKmainfont[BoldFont=SimHei]{SimSun}
\setCJKsansfont{Microsoft YaHei}
\setmainfont{Times New Roman}
\linespread{1.18}
\setlength{\parskip}{0.22em}
\setlength{\headheight}{16pt}
\pagestyle{fancy}
\fancyhf{}
\lhead{\sffamily\bfseries\color{deepnavy} 路基路面工程题库}
\rhead{\sffamily\color{mainblue} A4 White Edition}
\cfoot{\sffamily\color{deepnavy}\thepage/\pageref{LastPage}}
\renewcommand{\headrulewidth}{0.3pt}
\titleformat{\chapter}[display]{\sffamily\bfseries\Huge\color{deepnavy}}{}{0pt}{}
\titlespacing*{\chapter}{0pt}{-8pt}{16pt}
\titleformat{\section}{\sffamily\Large\bfseries\color{deepnavy}}{\thesection}{0.6em}{}
\titlespacing*{\section}{0pt}{1em}{0.5em}
\renewcommand{\contentsname}{快速导航}
\newcommand{\qnum}[1]{\tikz[baseline=(n.base)]\node[inner sep=2.5pt,minimum width=1.7em,rounded corners=4pt,fill=deepnavy,text=white,font=\sffamily\bfseries] (n) {#1};}
\setlist[enumerate]{leftmargin=3.35em,label=\protect\qnum{\arabic*},itemsep=0.72em,topsep=0.55em,parsep=0.24em}
\newcommand{\ans}[1]{\tikz[baseline=(a.base)]\node[inner xsep=5pt,inner ysep=2pt,rounded corners=3pt,fill=softyellow,draw=answerred!35,text=answerred,font=\bfseries] (a) {#1};}
\newcommand{\blankline}{\textcolor{linegray}{\rule{5.2em}{0.65pt}}}
\newtcolorbox{examcard}[1]{enhanced,breakable,colback=card,colframe=mainblue!45,boxrule=0.7pt,arc=2mm,left=5mm,right=5mm,top=5mm,bottom=5mm,before skip=5mm,after skip=5mm,title={#1},fonttitle=\sffamily\bfseries\large,coltitle=white,attach boxed title to top left={xshift=4mm,yshift=-2.5mm},boxed title style={arc=2mm,colback=mainblue,boxrule=0pt,left=3mm,right=3mm,top=1mm,bottom=1mm}}
\newtcolorbox{optionbox}{enhanced,breakable,colback=softblue,colframe=mainblue!25,boxrule=0.4pt,arc=2mm,left=5mm,right=5mm,top=2.8mm,bottom=2.8mm,before skip=3.2mm,after skip=3.6mm}
\newenvironment{answerblock}{\begin{tcolorbox}[enhanced,breakable,colback=softpink,colframe=answerred!45,boxrule=0.7pt,arc=2mm,left=4mm,right=4mm,top=3mm,bottom=3mm,before skip=3mm,after skip=3mm]\textcolor{answerred}{\sffamily\bfseries 答案：}}{\end{tcolorbox}}
\newcommand{\examtitle}[2]{%
  \clearpage
  \begin{center}
    {\sffamily\bfseries\fontsize{30}{32}\selectfont\color{deepnavy} 试卷编号 #1\par}
    \vspace{0.18cm}
    {\sffamily\bfseries\large\color{mainblue} #2\par}
    \vspace{0.25cm}
    \textcolor{mainblue!45}{\rule{0.82\linewidth}{1.2pt}}
  \end{center}
  \vspace{0.2cm}
}
\newcommand{\coverpage}[2]{%
  \begin{titlepage}
  \centering
  \vspace*{3.2cm}
  {\sffamily\bfseries\fontsize{34}{38}\selectfont\color{deepnavy} #1\par}
  \vspace{0.55cm}
  {\sffamily\bfseries\Large\color{mainblue} #2\par}
  \vfill
  {\sffamily\large\color{ink} A4 White Edition · 由原 Word 试题整理\par}
  \end{titlepage}
}
\newcommand{\tocintro}{%
  \begin{center}
    {\sffamily\bfseries\fontsize{26}{28}\selectfont\color{deepnavy} 快速导航\par}
    \vspace{0.2cm}
    \textcolor{mainblue!40}{\rule{0.82\linewidth}{1pt}}
  \end{center}
  \vspace{0.2cm}
}
\begin{document}
"""


def render_document(blocks, answer_mode=False, layout="tablet"):
    title = "路基路面工程题库（答案版）" if answer_mode else "路基路面工程题库（刷题版）"
    if layout == "a4":
        subtitle = "红色高亮答案 · A4 白底宽松版" if answer_mode else "无答案练习 · A4 白底宽松版"
        preamble = A4_PREAMBLE
    else:
        subtitle = "红色高亮答案 · 平板阅读宽松版" if answer_mode else "无答案练习 · 平板阅读宽松版"
        preamble = TABLET_PREAMBLE
    out = [preamble]
    out.append(rf"\coverpage{{{tex_escape(title)}}}{{{tex_escape(subtitle)}}}")
    out.append(r"\tocintro\begingroup\makeatletter\@starttoc{toc}\makeatother\endgroup\clearpage")
    for no in sorted(blocks.keys()):
        q_lines, a_lines = split_questions_answers(blocks[no], no)
        _, q_sections = parse_sections(q_lines, answer=False)
        _, a_sections = parse_sections(a_lines, answer=True)
        ans_map = map_answers(a_sections)
        out.append(rf"\examtitle{{{no}}}{{Roadbed \& Pavement Engineering}}")
        out.append(rf"\addcontentsline{{toc}}{{chapter}}{{试卷编号 {no}}}")
        for sidx, sec in enumerate(q_sections, start=1):
            kind = section_kind(sec["title"])
            out.append(r"\phantomsection")
            out.append(rf"\addcontentsline{{toc}}{{section}}{{{tex_escape(sec['title'])}}}")
            out.append(rf"\begin{{examcard}}{{{tex_escape(sec['title'])}}}")
            items = split_items(sec["items"])
            answer_info = ans_map.get(sec_index(sec["title"])) or ans_map.get(sidx)
            if items and any(is_question_start(it[0]) for it in items):
                out.append(r"\begin{enumerate}")
                for item in items:
                    m = re.match(r"\s*(\d+|l)[、.．]", item[0])
                    n = int(m.group(1)) if m and m.group(1).isdigit() else 1
                    ans = answer_for_item(answer_info, n) if answer_mode else ""
                    out.append(render_item(item, answer_mode, kind, ans))
                out.append(r"\end{enumerate}")
            else:
                for line in sec["items"]:
                    out.append(tex_text(line) + r"\par")
            out.append(r"\end{examcard}")
        if answer_mode and not q_sections and a_lines:
            out.append(r"\begin{examcard}{参考答案}")
            out.extend(tex_escape(line) + r"\par" for line in a_lines)
            out.append(r"\end{examcard}")
        out.append(r"\clearpage")
    out.append(r"\end{document}")
    return "\n".join(out)


def main():
    text = normalize_text(TEXT.read_text(encoding="utf-8"))
    lines = preprocess_lines(text)
    blocks = parse_exam_blocks(lines)
    jobs = [
        ("路基路面工程题库_刷题版.tex", False, "tablet"),
        ("路基路面工程题库_答案版.tex", True, "tablet"),
        ("路基路面工程题库_A4白底_刷题版.tex", False, "a4"),
        ("路基路面工程题库_A4白底_答案版.tex", True, "a4"),
    ]
    for name, mode, layout in jobs:
        (OUT / name).write_text(render_document(blocks, answer_mode=mode, layout=layout), encoding="utf-8")
        print(OUT / name)


if __name__ == "__main__":
    main()
