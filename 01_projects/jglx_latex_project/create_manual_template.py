import re
from pathlib import Path

root = Path(r"D:/xm/zy/jglx")
audit = root / "manual_correction_audit_dedup.md"
text = audit.read_text(encoding="utf-8")

out = root / "jglx_manual_retype_latex"
(out / "sections").mkdir(parents=True, exist_ok=True)

chapters = {
    1: "几何组成分析",
    2: "理论力学回顾",
    3: "材料力学回顾",
    4: "静定梁和刚架",
    5: "静定桁架",
    6: "组合结构",
    7: "三铰拱",
    8: "静定结构影响线",
    9: "静定结构位移计算",
    10: "力法（一）",
    11: "力法（二）",
    12: "位移法",
    13: "弯矩分配法",
    14: "矩阵位移法/动力学讲解资料",
}

main = r"""\documentclass[UTF8,zihao=-4]{ctexbook}
\usepackage[a4paper,margin=2.2cm]{geometry}
\usepackage{amsmath,amssymb,mathtools}
\usepackage{tikz}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{tcolorbox}
\tcbuselibrary{breakable,skins}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
\setlist[enumerate]{itemsep=0.6em,topsep=0.6em}
\newtcolorbox{problemBox}{breakable,enhanced,colback=white,colframe=black!60,title=题目}
\newtcolorbox{solutionBox}{breakable,enhanced,colback=blue!2,colframe=blue!50!black,title=答案与解析}
\newcommand{\NeedsManual}[1]{\par\noindent\textcolor{red!70!black}{\fbox{需人工精校：#1}}\par}
\title{结构力学基础与技巧班作业精校版}
\author{人工重排 LaTeX 工程}
\date{\today}
\begin{document}
\maketitle
\tableofcontents
\mainmatter
"""
for ch, title in chapters.items():
    main += f"\\include{{sections/ch{ch:02d}}}\n"
main += "\\end{document}\n"
(out / "main.tex").write_text(main, encoding="utf-8")

for ch, title in chapters.items():
    content = f"\\chapter{{第{ch}次：{title}}}\n\n"
    content += "本章为逐题人工精校区。下列条目需逐页对照原 PDF 手工转写题干、结构图、公式推导和最终答案。\n\n"
    content += "\\section{资料来源与校对状态}\n\n"
    content += "\\NeedsManual{当前仅建立精校模板，尚未完成逐题人工转写。}\n\n"
    content += "\\section{题目、答案与解析}\n\n"
    content += "\\begin{enumerate}[label=\\textbf{第\\arabic*题},wide]\n"
    content += "  \\item\n"
    content += "  \\begin{problemBox}\n"
    content += "  \\NeedsManual{对照原 PDF 转写题干，并用 TikZ 重画结构图。}\n"
    content += "  \\end{problemBox}\n\n"
    content += "  \\begin{solutionBox}\n"
    content += "  \\NeedsManual{对照答案 PDF 与讲解笔记补全受力分析、方程、计算过程和最终答案。}\n"
    content += "  \\end{solutionBox}\n"
    content += "\\end{enumerate}\n"
    (out / "sections" / f"ch{ch:02d}.tex").write_text(content, encoding="utf-8")

readme = """# 结构力学基础与技巧班作业精校版

这是为逐题人工转写准备的 LaTeX 工程骨架。当前仓库中的原始资料没有 Word/PPT/TeX 源文件，唯一资料为扫描型 PDF；要达到用户要求的“逐题人工矫正、公式 LaTeX 化、结构图重画”，必须逐页人工辨读并录入。

## 编译

使用 XeLaTeX：

```bash
xelatex main.tex
xelatex main.tex
```

## 状态

- 已按第 1--14 次建立章节。
- 每章包含题目框和答案解析框。
- `\\NeedsManual{...}` 表示需要人工对照原 PDF 精校的位置。
"""
(out / "README.md").write_text(readme, encoding="utf-8")
print(out)
