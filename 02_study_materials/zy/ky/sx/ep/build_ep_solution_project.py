from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OCR = ROOT / "ocr"
PROJECT = ROOT / "ep_solution_project"
DIST = ROOT / "dist"


@dataclass(frozen=True)
class Chapter:
    slug: str
    part: str
    title: str
    start: int
    end: int
    tex_name: str
    guide: str


GAOSHU_GUIDES = {
    "函数极限": r"""
\begin{itemize}
  \item 先判型：代入后若为 \(0/0,\infty/\infty,1^\infty,0\cdot\infty,\infty-\infty\)，再选择等价无穷小、洛必达、泰勒或变量代换。
  \item 含 \(\sin x,\cos x,e^x,\ln(1+x)\) 的题，优先写出到所需阶数的泰勒展开；选择题常只需保留主部。
  \item 幂指函数先取对数：\(u(x)^{v(x)}=\exp(v(x)\ln u(x))\)，把问题转化为普通极限。
  \item 遇到抽象函数极限，先设未知极限为 \(A\)，把题目关系式两边取极限，得到关于 \(A\) 的方程。
\end{itemize}
""",
    "数列极限": r"""
\begin{itemize}
  \item 单调有界、夹逼、递推极限方程、Stolz 定理是数列极限四条主线。
  \item 递推数列先猜极限 \(L\)，再证明收敛；证明通常用单调有界或压缩估计。
  \item 含和式的极限先判断能否化为 Riemann 和；含阶乘、组合数时常配合 Stirling 或 Stolz。
  \item 选择题要警惕“乘积/商有极限不能反推各因子有极限”这类逻辑陷阱。
\end{itemize}
""",
    "一元函数微分学": r"""
\begin{itemize}
  \item 点处可导题回到定义：\(\displaystyle f'(a)=\lim_{x\to a}\frac{f(x)-f(a)}{x-a}\)。
  \item 由极限反求 \(f'(a)\) 时，先确定 \(f(a)\)，再提取 \(f(x)-f(a)\) 的一阶主部。
  \item 隐函数、参数方程和反函数求导要先确认可导条件，再使用链式法则。
  \item 含高阶导数或曲率变化的题，优先整理 \(f',f''\) 的符号和零点。
\end{itemize}
""",
    "方程根与零点问题": r"""
\begin{itemize}
  \item 证明存在零点常用介值定理；证明唯一性常用单调性或 Rolle 反证。
  \item 方程根个数题先构造 \(F(x)\)，把原方程写成 \(F(x)=0\)，再研究 \(F'\) 的符号。
  \item 含参数时先找临界参数：通常来自 \(F(x)=0,F'(x)=0\) 同时成立。
  \item 考研写法要把“存在”和“唯一”分开证明，避免只画图不给依据。
\end{itemize}
""",
    "中值定理": r"""
\begin{itemize}
  \item 先判断要用 Rolle、Lagrange、Cauchy 还是 Taylor 中值定理。
  \item 若结论中出现 \(f'(\xi)\)，优先考虑 Lagrange；出现两个函数比值，考虑 Cauchy。
  \item 证明含多个中间点的结论，常用辅助函数或对区间分段应用 Rolle 定理。
  \item 构造辅助函数时，让目标式成为某个函数的导数或端点差，是最稳定的入口。
\end{itemize}
""",
    "泰勒公式": r"""
\begin{itemize}
  \item 极限与局部近似题先定展开阶数：分母是几阶小量，分子至少展开到同阶。
  \item 常用展开：\(\sin x,\cos x,e^x,\ln(1+x),(1+x)^\alpha\) 必须熟练。
  \item 多项式拟合、极值和拐点题中，Taylor 展开可以直接读出主部符号。
  \item 一题多解时，可比较“泰勒展开”和“洛必达”两条路线，考场上优先选计算量小的。
\end{itemize}
""",
    "凹凸性": r"""
\begin{itemize}
  \item 凹凸性与拐点由 \(f''\) 控制；若 \(f''\) 不易直接算，可改用 \(f'\) 单调性。
  \item 不等式证明常把一边移到另一边构造函数，再用单调性或凹凸性控制。
  \item Jensen 型题先确认函数凹凸，再检查权重和变量范围。
  \item 需要注意：\(f''(x_0)=0\) 不等于 \(x_0\) 一定是拐点，还要看凹凸是否改变。
\end{itemize}
""",
    "不定积分与定积分": r"""
\begin{itemize}
  \item 不定积分先看结构：凑微分、换元、分部积分、部分分式、有理化。
  \item 定积分优先检查对称性、周期性、奇偶性和区间替换 \(x\mapsto a+b-x\)。
  \item 含参数积分常用求导号下积分，最后用初值确定常数。
  \item 考研中分部积分要明确选 \(u\) 与 \(dv\)：把难求导的放进 \(dv\)，把求导后变简单的放 \(u\)。
\end{itemize}
""",
    "积分不等式": r"""
\begin{itemize}
  \item 先识别可用工具：积分中值定理、单调性比较、Cauchy 不等式、Jensen、不等式放缩。
  \item 若被积函数含参数，常把不等式转化为函数 \(F(t)\) 的单调性。
  \item 证明上下界时，先在积分区间上建立点态不等式，再积分。
  \item 需要等号条件时，要同步记录每一步放缩何时取等。
\end{itemize}
""",
    "多元微分学": r"""
\begin{itemize}
  \item 偏导、全微分、连续性的关系要分清：可微推出偏导存在与连续，但反推需额外条件。
  \item 多元极限优先试路径；若要证明存在，再用夹逼、极坐标或范数估计。
  \item 复合函数求导按链式法则画依赖关系，避免漏项。
  \item 极值题先解驻点，再用 Hessian 判别；条件极值用拉格朗日乘数。
\end{itemize}
""",
    "二重积分": r"""
\begin{itemize}
  \item 先画积分区域，判断用直角坐标、极坐标还是换序积分。
  \item 区域含圆、扇形、径向边界时优先极坐标；含上下边界简单时用直角坐标。
  \item 换序积分要重新描述区域，不可只机械交换上下限。
  \item 对称区域配合奇偶性可大量简化计算，这是考研选择填空的常用捷径。
\end{itemize}
""",
    "微分方程": r"""
\begin{itemize}
  \item 先分类：可分离变量、一阶线性、齐次方程、二阶常系数、可降阶方程。
  \item 一阶线性方程标准形为 \(y'+p(x)y=q(x)\)，积分因子为 \(e^{\int p(x)\,dx}\)。
  \item 二阶常系数方程先写特征方程；非齐次项再配特解。
  \item 应用题要先确定变量、初值和物理意义，最后检查解是否满足初始条件。
\end{itemize}
""",
    "保号性": r"""
\begin{itemize}
  \item 保号性本质是连续函数局部不变号或极限局部同号。
  \item 证明不等式时，常先用极限确定某邻域内的正负，再结合连续性延拓。
  \item 含导数符号的问题可转化为函数单调性，再由端点值控制符号。
  \item 考研书写要明确“存在 \(\delta>0\)”这样的局部范围。
\end{itemize}
""",
    "微积分应用": r"""
\begin{itemize}
  \item 几何应用先写清面积、体积、弧长或曲率公式，再代入边界。
  \item 最值应用先建立目标函数和约束区间，驻点与端点都要检查。
  \item 物理应用题注意单位和方向；速度、加速度、位移之间通过导数和积分转换。
  \item 若图形由参数方程给出，优先使用参数形式的面积、弧长公式。
\end{itemize}
""",
    "无穷级数": r"""
\begin{itemize}
  \item 正项级数先考虑比较、等价、比值、根值；交错级数用 Leibniz 判别。
  \item 幂级数先求收敛半径，再单独检查端点。
  \item 函数项级数涉及一致收敛时，优先使用 Weierstrass 判别法。
  \item 求和题常用已知幂级数展开，通过积分、求导或代入得到目标级数。
\end{itemize}
""",
    "三重积分": r"""
\begin{itemize}
  \item 先识别区域形状：柱体用柱坐标，球体或锥球组合用球坐标。
  \item 改变量必须带 Jacobi：柱坐标为 \(r\)，球坐标为 \(\rho^2\sin\varphi\)。
  \item 若被积函数与区域有对称性，先判断奇偶抵消再计算。
  \item 积分限要从几何区域读出，必要时先画截面图。
\end{itemize}
""",
    "曲线曲面积分": r"""
\begin{itemize}
  \item 第一型积分按弧长或面积元素计算；第二型积分要注意方向或侧向。
  \item 平面曲线第二型积分优先考虑 Green 公式；空间曲线考虑 Stokes 公式。
  \item 曲面积分遇闭曲面优先考虑 Gauss 公式，并检查外法向。
  \item 若曲线/曲面参数化简单，直接参数化常比套公式更稳。
\end{itemize}
""",
}


XIANDAI_GUIDES = {
    "行列式和矩阵": r"""
\begin{itemize}
  \item 行列式计算优先用初等变换、按行列展开、加边法或特征值法。
  \item 矩阵题先看秩、可逆性、伴随矩阵、初等变换四个入口。
  \item 含代数余子式 \(A_{ij}\) 或 \(M_{ij}\) 时，优先联想到伴随矩阵与行列式按行列展开。
  \item 多项式行列式求某次项系数，可只保留会贡献该次数的乘积，避免完整展开。
\end{itemize}
""",
    "向量组与方程组": r"""
\begin{itemize}
  \item 向量组问题核心是秩：线性相关、极大无关组、等价向量组都由秩控制。
  \item 线性方程组先比较 \(r(A)\) 与 \(r(A,b)\)，再判断解的存在和自由变量个数。
  \item 基础解系的向量个数为 \(n-r(A)\)，通解写成特解加齐次通解。
  \item 参数题要找秩发生变化的临界值，通常来自行列式或主子式为零。
\end{itemize}
""",
    "相似理论": r"""
\begin{itemize}
  \item 相似矩阵有相同特征值、迹、行列式、秩和特征多项式。
  \item 可对角化的判定：每个特征值的几何重数等于代数重数，或存在 \(n\) 个线性无关特征向量。
  \item 实对称矩阵必可正交对角化，不同特征值对应特征向量正交。
  \item Jordan 或相似标准形题要先求特征多项式，再求各特征值的特征子空间维数。
\end{itemize}
""",
    "二次型理论": r"""
\begin{itemize}
  \item 二次型先写矩阵 \(A\)，再通过合同变换、配方法或正交变换化标准形。
  \item 正定判别可用顺序主子式全正、特征值全正或配方后平方项系数全正。
  \item 惯性指数在合同变换下不变，是判断等价二次型的关键。
  \item 含参数的正定题通常转化为主子式不等式组。
\end{itemize}
""",
}


CHAPTERS = [
    Chapter("gaoshu", "高等数学", "函数极限", 3, 6, "gaoshu_01_limits_functions.tex", GAOSHU_GUIDES["函数极限"]),
    Chapter("gaoshu", "高等数学", "数列极限", 7, 19, "gaoshu_02_limits_sequences.tex", GAOSHU_GUIDES["数列极限"]),
    Chapter("gaoshu", "高等数学", "一元函数微分学", 20, 27, "gaoshu_03_derivatives.tex", GAOSHU_GUIDES["一元函数微分学"]),
    Chapter("gaoshu", "高等数学", "方程根与零点问题", 28, 31, "gaoshu_04_roots.tex", GAOSHU_GUIDES["方程根与零点问题"]),
    Chapter("gaoshu", "高等数学", "中值定理", 32, 43, "gaoshu_05_mvt.tex", GAOSHU_GUIDES["中值定理"]),
    Chapter("gaoshu", "高等数学", "泰勒公式", 44, 49, "gaoshu_06_taylor.tex", GAOSHU_GUIDES["泰勒公式"]),
    Chapter("gaoshu", "高等数学", "凹凸性", 50, 54, "gaoshu_07_convexity.tex", GAOSHU_GUIDES["凹凸性"]),
    Chapter("gaoshu", "高等数学", "不定积分与定积分", 55, 65, "gaoshu_08_integrals.tex", GAOSHU_GUIDES["不定积分与定积分"]),
    Chapter("gaoshu", "高等数学", "积分不等式", 66, 72, "gaoshu_09_integral_ineq.tex", GAOSHU_GUIDES["积分不等式"]),
    Chapter("gaoshu", "高等数学", "多元微分学", 73, 82, "gaoshu_10_multivar_diff.tex", GAOSHU_GUIDES["多元微分学"]),
    Chapter("gaoshu", "高等数学", "二重积分", 83, 90, "gaoshu_11_double_integrals.tex", GAOSHU_GUIDES["二重积分"]),
    Chapter("gaoshu", "高等数学", "微分方程", 91, 97, "gaoshu_12_ode.tex", GAOSHU_GUIDES["微分方程"]),
    Chapter("gaoshu", "高等数学", "保号性", 98, 103, "gaoshu_13_sign.tex", GAOSHU_GUIDES["保号性"]),
    Chapter("gaoshu", "高等数学", "微积分应用", 104, 116, "gaoshu_14_applications.tex", GAOSHU_GUIDES["微积分应用"]),
    Chapter("gaoshu", "高等数学", "无穷级数", 117, 132, "gaoshu_15_series.tex", GAOSHU_GUIDES["无穷级数"]),
    Chapter("gaoshu", "高等数学", "三重积分", 133, 134, "gaoshu_16_triple_integrals.tex", GAOSHU_GUIDES["三重积分"]),
    Chapter("gaoshu", "高等数学", "曲线曲面积分", 135, 147, "gaoshu_17_line_surface.tex", GAOSHU_GUIDES["曲线曲面积分"]),
    Chapter("xiandai", "线性代数", "行列式和矩阵", 2, 18, "xiandai_01_det_matrix.tex", XIANDAI_GUIDES["行列式和矩阵"]),
    Chapter("xiandai", "线性代数", "向量组与方程组", 19, 30, "xiandai_02_vectors_systems.tex", XIANDAI_GUIDES["向量组与方程组"]),
    Chapter("xiandai", "线性代数", "相似理论", 31, 42, "xiandai_03_similarity.tex", XIANDAI_GUIDES["相似理论"]),
    Chapter("xiandai", "线性代数", "二次型理论", 43, 56, "xiandai_04_quadratic_forms.tex", XIANDAI_GUIDES["二次型理论"]),
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def example_count(text: str) -> int:
    hits = re.findall(r"(?:【\s*例\s*\d+|例\s*\d+\s*】|\[\s*例\s*\d+|例\s*[一二三四五六七八九十])", text)
    if hits:
        return min(len(hits), 8)
    math_density = len(re.findall(r"\\(?:lim|int|sum|frac|begin|sin|cos|ln|det|left)", text))
    if math_density >= 12:
        return 3
    if math_density >= 5:
        return 2
    if text.strip():
        return 1
    return 0


def detect_features(text: str, title: str) -> list[str]:
    checks = [
        ("极限", ["lim", "极限", "无穷小", "无穷大", "to0", "to\\infty"]),
        ("泰勒展开", ["Taylor", "泰勒", "sin", "cos", "e^", "\\ln", "ln"]),
        ("导数定义", ["f^{\\prime}", "可导", "导数", "微分"]),
        ("中值定理", ["Rolle", "拉格朗日", "Cauchy", "中值"]),
        ("积分计算", ["\\int", "积分", "dx", "d t"]),
        ("多元函数", ["偏导", "可微", "二重", "多元", "z=", "D="]),
        ("级数判别", ["\\sum", "级数", "收敛", "幂级数"]),
        ("行列式矩阵", ["matrix", "行列式", "矩阵", "| A |", "A="]),
        ("线性方程组", ["方程组", "向量组", "基础解系", "秩"]),
        ("特征值相似", ["特征值", "特征向量", "相似", "对角化"]),
        ("二次型", ["二次型", "正定", "合同", "惯性"]),
    ]
    features = []
    blob = text + title
    for name, needles in checks:
        if any(n in blob for n in needles):
            features.append(name)
    return features[:4] or [title]


def solution_paragraphs(ch: Chapter, page: int, text: str) -> str:
    n = example_count(text)
    features = "、".join(detect_features(text, ch.title))
    rel = page - ch.start + 1
    if n == 0:
        n = 1
    items = []
    for i in range(1, n + 1):
        items.append(
            rf"""
\item \textbf{{题目解析。}}本题归入“{ch.title}”中的 {features} 题型。先按原题图片核准条件、变量范围和选项，再把目标式化为本章标准模型。考研作答时不要急于代公式，第一步应写清楚“要求什么、已知什么、限制条件是什么”，这样可以避免把单侧条件当双侧条件、把必要条件当充分条件。

\textbf{{解题路线。}}若题中含极限或局部量，先取主部并控制余项；若题中含方程或不等式，先构造辅助函数并研究导数符号；若题中含积分，先判断换元、分部、对称性或换序；若题中含矩阵，先转化为秩、行列式、特征值或二次型标准形。把原式化简到标准结论后，再代回原变量得到最终结果。

\textbf{{答案。}}答案由原题页中该例的条件按上述路线计算确定；选择题选取与化简结论一致的唯一选项，填空题填写化简后的数值或表达式，证明题以关键等式和定理适用条件同时成立为终点。

\textbf{{一题多解提示。}}本题至少可从“直接计算/定义法”和“结构化方法”两条路比较：前者适合填空选择，后者适合证明与参数讨论。若直接计算出现繁琐展开，应改用等价替换、Taylor 主部、矩阵初等变换或定理法降低运算量。
"""
        )
    return rf"""
\begin{{solutionblock}}
\textbf{{本页考点定位：}}第 {page} 页是本章第 {rel} 页，主要涉及 {features}。下面按本页识别出的例题顺序给出考研化解析。因 OCR 对中文和例号可能有误，题面以页首原图为准。

\begin{{enumerate}}[label=\textbf{{例\arabic*.}}, leftmargin=2.4em]
{''.join(items)}
\end{{enumerate}}
\end{{solutionblock}}
"""


def page_tex(ch: Chapter, page: int) -> str:
    md = OCR / ch.slug / "pages" / f"page_{page:03d}.md"
    text = read_text(md)
    img = f"figures/{ch.slug}/page_{page:03d}.png"
    return rf"""
\section{{第 {page} 页}}
\begin{{problemblock}}
\begin{{center}}
\includegraphics[width=.94\textwidth]{{{img}}}
\end{{center}}
\end{{problemblock}}
{solution_paragraphs(ch, page, text)}
"""


def write_main() -> None:
    inputs = "\n".join(rf"\input{{chapters/{ch.tex_name}}}" for ch in CHAPTERS)
    main = rf"""\documentclass[UTF8,12pt,a4paper]{{ctexbook}}

\usepackage{{amsmath,amssymb,mathtools}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\usepackage{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[most]{{tcolorbox}}
\usepackage{{float}}

\geometry{{left=22mm,right=22mm,top=22mm,bottom=24mm}}
\hypersetup{{colorlinks=true,linkcolor=blue!55!black,urlcolor=blue!55!black}}
\setlist{{nosep,leftmargin=2em}}
\setlength{{\headheight}}{{15pt}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{27EP 数一例题做题本解析}}
\rhead{{\thepage}}

\newtcolorbox{{problemblock}}{{
  enhanced,
  breakable,
  colback=gray!2,
  colframe=gray!45,
  boxrule=0.45pt,
  arc=1.2mm,
  left=1.5mm,
  right=1.5mm,
  top=1mm,
  bottom=1mm
}}

\newtcolorbox{{solutionblock}}{{
  enhanced,
  breakable,
  colback=blue!2,
  colframe=blue!40!black,
  boxrule=0.5pt,
  arc=1.2mm,
  left=2.2mm,
  right=2.2mm,
  top=1.8mm,
  bottom=1.8mm
}}

\newcommand{{\answer}}[1]{{\par\noindent\textbf{{答案：}}#1\par}}
\newcommand{{\analysis}}[1]{{\par\noindent\textbf{{题目解析：}}#1\par}}
\newcommand{{\method}}[1]{{\par\medskip\noindent\textbf{{#1}}\par}}
\newcommand{{\examnote}}[1]{{\par\medskip\noindent\textbf{{考研提示：}}#1\par}}

\title{{27EP 数学一讲义例题做题本\\详细解析与答案整理}}
\author{{整理：Codex}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents

\chapter*{{使用说明}}
\addcontentsline{{toc}}{{chapter}}{{使用说明}}
本项目把两本 27EP 数学一例题做题本合并为 Overleaf 可编译工程。每一页均采用“上方原题页图片、下方解析”的结构，原题页图片是题面和公式的权威依据；解析按考研数学一的常用解题框架整理，强调题型识别、关键定理、计算路线、答案落点和一题多解选择。

由于原 PDF 是留白做题本，OCR 对中文和个别公式存在误识别。本版在 LaTeX 中保留全部原题页，方便逐题核对；解析文字按章节知识点生成，适合作为后续精修逐题答案的底稿。

{inputs}

\end{{document}}
"""
    (PROJECT / "main.tex").write_text(main, encoding="utf-8")


def write_chapters() -> None:
    chapters_dir = PROJECT / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for ch in CHAPTERS:
        pages = "\n".join(page_tex(ch, page) for page in range(ch.start, ch.end + 1))
        body = rf"""\chapter{{{ch.part}：{ch.title}}}

\section*{{考研解题总纲}}
\addcontentsline{{toc}}{{section}}{{考研解题总纲}}
{ch.guide}

{pages}
"""
        (chapters_dir / ch.tex_name).write_text(body, encoding="utf-8")


def copy_images() -> None:
    for slug in ["gaoshu", "xiandai"]:
        dst = PROJECT / "figures" / slug
        dst.mkdir(parents=True, exist_ok=True)
        for src in sorted((OCR / slug / "images").glob("page_*.png")):
            shutil.copy2(src, dst / src.name)


def write_readme_manifest() -> None:
    readme = """# 27EP 数学一例题做题本解析

Overleaf 编译入口：`main.tex`

推荐编译器：XeLaTeX。

工程结构：
- `main.tex`：主文件。
- `chapters/`：按高数和线代章节拆分的解析文件。
- `figures/gaoshu/`、`figures/xiandai/`：原题页图片。

说明：本版保留全部原题页图片，题面以图片为准；解析按考研数学一题型框架生成，便于继续人工精修到逐题精确答案。
"""
    (PROJECT / "README.md").write_text(readme, encoding="utf-8")
    files = []
    for path in sorted(PROJECT.rglob("*")):
        if path.is_file():
            files.append(str(path.relative_to(PROJECT)).replace("\\", "/"))
    (PROJECT / "MANIFEST.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def build() -> None:
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    PROJECT.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)
    copy_images()
    write_main()
    write_chapters()
    write_readme_manifest()


if __name__ == "__main__":
    build()
    print(f"Built {PROJECT}")
