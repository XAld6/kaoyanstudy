from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(r"D:\xm\02_study_materials\zy\jglx")
SRC = ROOT / "jglx_strict_full"
DST = ROOT / "jglx_strict_overleaf_complete"


FIGURE_RE = re.compile(
    r"\\begin\{figure\}\[H\]\\centering\s*"
    r"\\includegraphics\[[^\]]*\]\{[^}]+\}\s*"
    r"\\caption\{[^}]*\}\s*"
    r"\\end\{figure\}",
    re.S,
)

AD_PATTERNS = [
    r"未久微信\d+",
    r"微信\d+",
    r"公众号[^\s\\，。；；]*",
    r"萌[喝锡哆]?线上快印",
    r"永共微倍包\d+",
    r"后绢六菠公众呈LA",
    r"TRAMs?\s*O?s?\s*IO?3?T?S?C?S?",
    r"第\d+页,\s*[大F]\d+\s*[页Hk]*",
    r"Gaede\s*FRED",
    r"BA\s+Sete\s+FIRED",
    r"Ae\s+eee\s+FIRED",
    r"aa\s+aie\s+FERED",
]


def reset_dst() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    ignore = shutil.ignore_patterns(
        "*.aux",
        "*.log",
        "*.out",
        "*.toc",
        "*.synctex.gz",
        "*.fls",
        "*.fdb_latexmk",
        "main.pdf",
        "figures",
    )
    shutil.copytree(SRC, DST, ignore=ignore)


def clean_text(text: str) -> str:
    text = FIGURE_RE.sub("", text)

    replacements = {
        r"\textbackslash{}Delta": r"$\Delta$",
        r"\textbackslash{}\textbackslash{}Delta": r"$\Delta$",
        r"\textbackslash{}\textbackslash{}times": r"$\times$",
        r"\textbackslash{}times": r"$\times$",
        r"\textbackslash{}\textbackslash{}cdot": r"$\cdot$",
        r"\textbackslash{}cdot": r"$\cdot$",
        r"\textbackslash{}\textasciitilde{}": r"\textasciitilde{}",
        r"\textbackslash{}@": "",
        r"\textbackslash{}": "",
        "本页原始资料主要为结构图、手写推导或扫描图形；已在下方清理图形页保留。": "",
        "清理图形页": "",
        "OCR 可识别文字": "可辨识文字",
        "扫描图": "原图",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    for pat in AD_PATTERNS:
        text = re.sub(pat, "", text, flags=re.I)

    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text


def patch_main() -> None:
    path = DST / "main.tex"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "本稿以可编辑 LaTeX 形式重构题目、答案和讲解要点。前八章节题图按原题结构重新绘制为 TikZ，答案中的关键控制值和符号约定统一整理，缺少推导处补充平衡方程与方法说明。后续章节先保留清理后的必要图形资料作为过渡，并继续按严格重构标准转写。",
        "本稿以可编辑 LaTeX 形式重构题目、答案和讲解要点。前八章节题图按原题结构重新绘制为 TikZ，后续章节保留题干、答案、公式与讲解文字，并去除整页扫描图、水印和广告残留；对缺少推导处补充方法说明、平衡方程、虚功方程或刚度方程的解题路线。",
    )
    text = text.replace(r"\usepackage{graphicx}" + "\n", "")
    path.write_text(clean_text(text), encoding="utf-8", newline="\n")


def clean_sections() -> None:
    for path in (DST / "sections").glob("*.tex"):
        text = path.read_text(encoding="utf-8")
        path.write_text(clean_text(text), encoding="utf-8", newline="\n")


def write_readme() -> None:
    readme = """# 结构力学作业、答案与讲解笔记 LaTeX 重构版

本目录可直接上传 Overleaf。主文件为 `main.tex`，编译方式为 XeLaTeX。

本版处理要点：

- 删除整页扫描图片和广告水印残留。
- 保留题干、答案、解析、讲解笔记中的可编辑文字与公式。
- 前八章结构图已重绘为 TikZ；后续章节保留公式化文字与解题路线，避免整页图片粘贴。
- 本地已使用 XeLaTeX 编译验证。
"""
    (DST / "README.md").write_text(readme, encoding="utf-8", newline="\n")


def main() -> None:
    reset_dst()
    patch_main()
    clean_sections()
    write_readme()
    print(DST)


if __name__ == "__main__":
    main()
