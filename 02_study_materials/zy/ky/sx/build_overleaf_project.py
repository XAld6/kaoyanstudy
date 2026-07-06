from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
PDF = next(ROOT.glob("*.pdf"))
PROJECT = ROOT / "overleaf_solution_project"
FIGURES = PROJECT / "figures" / "original_pages"
CHAPTERS = PROJECT / "chapters"
DIST = ROOT / "dist"


CHAPTERS_META = [
    ("ch01", "函数、极限、连续", 2, 18),
    ("ch02", "一元函数微分学", 19, 38),
    ("ch03", "一元函数积分学", 39, 62),
    ("ch04", "常微分方程", 63, 75),
    ("ch05", "多元函数微分学", 76, 95),
    ("ch06", "二重积分", 96, 111),
    ("ch07", "无穷级数", 112, 129),
    ("ch08", "向量代数与空间解析几何及多元微分学在几何上的应用", 130, 140),
    ("ch09", "多元函数积分学及其应用", 141, 160),
]


MAIN_TEX = r"""\documentclass[UTF8,12pt,a4paper]{ctexbook}

\usepackage{amsmath,amssymb,mathtools}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage[most]{tcolorbox}
\usepackage{newunicodechar}

\geometry{left=24mm,right=24mm,top=24mm,bottom=26mm}
\hypersetup{colorlinks=true,linkcolor=blue!55!black,urlcolor=blue!55!black}
\setlist{nosep,leftmargin=2em}
\setlength{\headheight}{15pt}
\pagestyle{fancy}
\fancyhf{}
\lhead{武忠祥高数强化严选题数一做题本解析}
\rhead{\thepage}

\newunicodechar{①}{\ifmmode\text{(1)}\else(1)\fi}
\newunicodechar{②}{\ifmmode\text{(2)}\else(2)\fi}
\newunicodechar{③}{\ifmmode\text{(3)}\else(3)\fi}
\newunicodechar{④}{\ifmmode\text{(4)}\else(4)\fi}
\newunicodechar{⑤}{\ifmmode\text{(5)}\else(5)\fi}
\newunicodechar{⑥}{\ifmmode\text{(6)}\else(6)\fi}
\newunicodechar{⑦}{\ifmmode\text{(7)}\else(7)\fi}
\newunicodechar{⑧}{\ifmmode\text{(8)}\else(8)\fi}
\newunicodechar{⑨}{\ifmmode\text{(9)}\else(9)\fi}

\newtcolorbox{problemblock}{
  enhanced,
  breakable,
  colback=gray!3,
  colframe=gray!45,
  boxrule=0.5pt,
  arc=2mm,
  left=2mm,
  right=2mm,
  top=1.5mm,
  bottom=1.5mm
}

\newtcolorbox{solutionblock}{
  enhanced,
  breakable,
  colback=blue!2,
  colframe=blue!35!black,
  boxrule=0.5pt,
  arc=2mm,
  left=2mm,
  right=2mm,
  top=1.5mm,
  bottom=1.5mm
}

\newcommand{\answer}[1]{\par\noindent\textbf{答案：}#1\par}
\newcommand{\analysis}[1]{\par\noindent\textbf{题目解析：}#1\par}
\newcommand{\method}[1]{\par\medskip\noindent\textbf{#1}\par}
\newcommand{\examnote}[1]{\par\medskip\noindent\textbf{考研提示：}#1\par}

\title{武忠祥高数强化严选题（数学一）\\详细解析讲义}
\author{整理：Codex}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

\chapter*{使用说明}
\addcontentsline{toc}{chapter}{使用说明}
本项目按原做题本章节编排，解析目标是服务考研数学一复习：先判断题型和考点，再给出关键思路、完整推导、答案，并在适合的题目中补充一题多解或易错提醒。原题页图片已放入 \verb|figures/original_pages|，用于核对题面与公式。

\input{chapters/ch01.tex}
\input{chapters/ch02.tex}
\input{chapters/ch03.tex}
\input{chapters/ch04.tex}
\input{chapters/ch05.tex}
\input{chapters/ch06.tex}
\input{chapters/ch07.tex}
\input{chapters/ch08.tex}
\input{chapters/ch09.tex}

\end{document}
"""


CH01_TEX = r"""\chapter{函数、极限、连续}

\section{原题页索引}
本章原题对应做题本第 2--18 页。遇到抽取公式不清楚时，以本项目中的原题页图片为准。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_002.png}
\end{center}

\section{选择题}

\begin{problemblock}
\textbf{1.} 函数
\[
f(x)=x\tan x\,e^{\sin x}
\]
是（\quad）

A. 单调函数 \qquad B. 周期函数 \qquad C. 偶函数 \qquad D. 无界函数
\end{problemblock}

\begin{solutionblock}
\analysis{本题考查函数性质判断。考研选择题中遇到“单调、周期、奇偶、有界”四个性质并列时，优先检查最容易被破坏的性质：含有因子 \(x\) 通常破坏周期性；含有 \(\tan x\) 通常带来无界性与间断点；含有 \(e^{\sin x}\) 通常破坏奇偶性。}

\method{方法一：直接抓无界性}
在定义域内取
\[
x_n=\frac{\pi}{2}-\frac{1}{n}\quad (n\to\infty).
\]
则 \(\tan x_n\to+\infty\)，且 \(x_n\to \frac{\pi}{2}\)，\(e^{\sin x_n}\to e\)。因此
\[
f(x_n)=x_n\tan x_n e^{\sin x_n}\to+\infty,
\]
函数无界。

\method{方法二：排除其他选项}
由于存在 \(\tan x\)，函数在 \(\frac{\pi}{2}+k\pi\) 附近趋于无穷，不可能在整个定义域上单调有界。又因乘有 \(x\)，即使 \(\tan x\) 与 \(e^{\sin x}\)具有周期特征，整体也不满足周期函数定义。奇偶性方面，
\[
f(-x)=(-x)\tan(-x)e^{\sin(-x)}=x\tan x e^{-\sin x},
\]
一般既不等于 \(f(x)\)，也不等于 \(-f(x)\)。故只能选无界。

\answer{D}
\examnote{考研选择题不必把每个性质都严格证明到底；先用特殊点列击中“无界”，是最快路线。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 下列四个函数中
\[
\text{① }x\sin\frac1x,\qquad
\text{② }\frac1x\sin\frac1x,\qquad
\text{③ }\frac{\sin x}{x},\qquad
\text{④ }x\sin x,
\]
在区间 \((0,+\infty)\) 上有界的共有（\quad）

A. 1 个 \qquad B. 2 个 \qquad C. 3 个 \qquad D. 4 个
\end{problemblock}

\begin{solutionblock}
\analysis{本题核心是分别检查 \(x\to0^+\) 与 \(x\to+\infty\) 两端。区间是 \((0,+\infty)\)，所以两个端点都可能导致无界。}

① 对 \(x\sin\frac1x\)，当 \(0<x\le 1\) 时
\[
\left|x\sin\frac1x\right|\le x\le 1;
\]
当 \(x\ge1\) 时令 \(t=1/x\)，利用 \(|\sin t|\le |t|\)，得
\[
\left|x\sin\frac1x\right|\le x\cdot\frac1x=1.
\]
故①有界。

② 对 \(\frac1x\sin\frac1x\)，取
\[
x_n=\frac{1}{\frac{\pi}{2}+2n\pi},
\]
则 \(x_n\to0^+\)，且 \(\sin\frac1{x_n}=1\)，于是
\[
\frac1{x_n}\sin\frac1{x_n}=\frac1{x_n}\to+\infty.
\]
故②无界。

③ 对 \(\frac{\sin x}{x}\)，当 \(0<x\le1\) 时由 \(\lim_{x\to0}\frac{\sin x}{x}=1\)，在右邻域有界；当 \(x\ge1\) 时
\[
\left|\frac{\sin x}{x}\right|\le \frac1x\le1.
\]
故③有界。

④ 对 \(x\sin x\)，取 \(x_n=\frac{\pi}{2}+2n\pi\)，则 \(\sin x_n=1\)，
\[
x_n\sin x_n=x_n\to+\infty,
\]
故④无界。

所以有界的只有①③，共 2 个。

\answer{B}
\examnote{这类题常用“端点分治”：\(0^+\) 看振荡是否被 \(x\) 压住，\(+\infty\) 看是否有线性增长因子。}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 设有数列 \(\{x_n\}\) 与 \(\{y_n\}\)，以下结论正确的是（\quad）

A. 若 \(\lim_{n\to\infty}x_ny_n=0\)，则必有 \(\lim_{n\to\infty}x_n=0\) 或 \(\lim_{n\to\infty}y_n=0\)。

B. 若 \(\lim_{n\to\infty}x_ny_n=\infty\)，则必有 \(\lim_{n\to\infty}x_n=\infty\) 或 \(\lim_{n\to\infty}y_n=\infty\)。

C. 若 \(\{x_ny_n\}\) 有界，则必有 \(\{x_n\}\) 与 \(\{y_n\}\) 都有界。

D. 若 \(\{x_ny_n\}\) 无界，则必有 \(\{x_n\}\) 无界或 \(\{y_n\}\) 无界。
\end{problemblock}

\begin{solutionblock}
\analysis{本题是数列乘积与因子性质的逻辑判断。考研中应特别注意：乘积收敛或有界，通常不能反推每个因子；但若两个因子都有限制，则可推出乘积有限制。}

\method{排除法}
A 错。取 \(x_n=n,\ y_n=\frac1{n^2}\)，则
\[
x_ny_n=\frac1n\to0,
\]
但 \(x_n\not\to0\)，而 \(y_n\to0\)。这个例子仍有一个趋零；若要否定“极限存在且等于 0”的严谨版本，可取 \(x_n=(-1)^n,\ y_n=0\)，此时 \(x_n\) 极限不存在，不能说 \(\lim x_n=0\)。命题中的“必有极限等于 0”不成立。

B 错。取 \(x_n=y_n=(-1)^n n\)，则
\[
x_ny_n=n^2\to+\infty,
\]
但 \(x_n,y_n\) 均不趋于 \(+\infty\)，因为它们符号振荡。

C 错。取 \(x_n=n,\ y_n=\frac1n\)，则
\[
x_ny_n=1
\]
有界，但 \(x_n\) 无界。

D 对。用反证法：若 \(\{x_n\}\) 与 \(\{y_n\}\) 都有界，则存在 \(M,N>0\)，使
\[
|x_n|\le M,\qquad |y_n|\le N.
\]
于是
\[
|x_ny_n|\le MN,
\]
即 \(\{x_ny_n\}\) 有界。这与“\(\{x_ny_n\}\) 无界”矛盾。因此乘积无界时，至少有一个因子数列无界。

\answer{D}
\examnote{“乘积有界不能推出因子有界；乘积无界能推出至少一个因子无界”，这是常考逻辑。}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 设
\[
\lim_{n\to\infty}x_ny_n=\infty,
\]
则下列结论错误的是（\quad）

A. \(\lim_{n\to\infty}x_n=\infty\) 与 \(\lim_{n\to\infty}y_n=\infty\) 至少有一个成立。

B. \(\{x_n\}\) 与 \(\{y_n\}\) 中至少有一个为无界变量。

C. 若 \(\{x_n\}\) 是无穷小量，则 \(\{y_n\}\) 必为无界变量。

D. 若 \(\lim_{n\to\infty}x_n=a\ne\infty\)，则 \(\{y_n\}\) 必为无穷大量。
\end{problemblock}

\begin{solutionblock}
\analysis{题干给出的是乘积趋于无穷。考研中要区分“乘积趋于无穷”与“每个因子趋于无穷”：后者不能由前者直接推出，因为符号振荡、一个因子有界但不收敛等情况都会破坏结论。}

\method{反例判断 A}
取
\[
x_n=(-1)^n n,\qquad y_n=(-1)^n.
\]
则
\[
x_ny_n=n\to+\infty,
\]
但 \(x_n\) 由于正负振荡，不趋于 \(+\infty\)；\(y_n\) 也不趋于 \(+\infty\)。因此 A 的“至少有一个极限为 \(+\infty\)”不成立，A 错。

\method{验证其余选项}
B 正确。若 \(\{x_n\}\)、\(\{y_n\}\) 都有界，则 \(\{x_ny_n\}\) 必有界，矛盾。

C 正确。若 \(x_n\to0\) 而 \(\{y_n\}\) 有界，则 \(x_ny_n\to0\)，不可能趋于无穷。

D 正确。若 \(x_n\to a\) 且 \(a\) 为有限数，当 \(a\ne0\) 时 \(y_n=\frac{x_ny_n}{x_n}\) 的绝对值趋于无穷；当 \(a=0\) 时，如果 \(y_n\) 不为无穷大量，则乘积不可能趋于无穷。故 \(\{y_n\}\) 必为无穷大量。

\answer{A}
\examnote{这类题常用“反例优先”。A 中的错误在于把乘积的正无穷误认为某个因子必须正无穷。}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 设函数 \(f(x)\) 连续，则下列函数中，必为偶函数的是（\quad）
\[
\text{A. }\int_0^x f(t^2)\,dt,\qquad
\text{B. }\int_0^x f^2(t)\,dt,
\]
\[
\text{C. }\int_0^x t\bigl[f(t)-f(-t)\bigr]\,dt,\qquad
\text{D. }\int_0^x t\bigl[f(t)+f(-t)\bigr]\,dt.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{本题考查“变上限积分函数的奇偶性”。核心规律是：若 \(g(t)\) 为奇函数，则 \(G(x)=\int_0^x g(t)\,dt\) 为偶函数；若 \(g(t)\) 为偶函数，则 \(G(x)\) 为奇函数。}

\method{方法一：判断被积函数奇偶性}
对 D，令
\[
g(t)=t\bigl[f(t)+f(-t)\bigr].
\]
其中 \(f(t)+f(-t)\) 是偶函数，乘以 \(t\) 后 \(g(t)\) 是奇函数。于是
\[
G(x)=\int_0^x g(t)\,dt.
\]
验证：
\[
G(-x)=\int_0^{-x}g(t)\,dt
=-\int_0^x g(-u)\,du
=-\int_0^x[-g(u)]\,du
=G(x).
\]
故 D 必为偶函数。

\method{方法二：排除其他选项}
A 中 \(f(t^2)\) 是偶函数，因此积分函数通常为奇函数，例如 \(f\equiv1\) 时得到 \(x\)，不是偶函数。

B 中 \(f^2(t)\) 不一定是偶函数，例如 \(f(t)=t+1\)，则 \((t+1)^2\) 不是偶函数，积分函数不必为偶函数。

C 中 \(f(t)-f(-t)\) 是奇函数，乘以 \(t\) 后为偶函数，积分函数通常为奇函数，例如取 \(f(t)=t\)，被积函数为 \(2t^2\)，积分为 \(\frac23x^3\)，不是偶函数。

\answer{D}
\examnote{记住一句话：从 \(0\) 到 \(x\) 的变上限积分会让奇偶性“反转”：奇被积函数积分成偶函数，偶被积函数积分成奇函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 设数列 \(\{a_n\},\{b_n\}\) 对任意正整数 \(n\) 满足
\[
a_n\le b_n\le a_{n+1},
\]
则（\quad）

A. 数列 \(\{a_n\},\{b_n\}\) 均收敛，且 \(\lim a_n=\lim b_n\)。

B. 数列 \(\{a_n\},\{b_n\}\) 均发散，且 \(\lim a_n=\lim b_n=+\infty\)。

C. 数列 \(\{a_n\},\{b_n\}\) 具有相同的敛散性。

D. 数列 \(\{a_n\},\{b_n\}\) 具有不同的敛散性。
\end{problemblock}

\begin{solutionblock}
\analysis{由 \(a_n\le b_n\le a_{n+1}\) 可立即得到 \(a_n\le a_{n+1}\)，所以 \(\{a_n\}\) 单调递增。单调数列只有两种情况：收敛到有限极限，或发散到 \(+\infty\)。}

\method{情况一：\(\{a_n\}\) 收敛}
设 \(a_n\to A\)。因为 \(a_{n+1}\to A\)，且
\[
a_n\le b_n\le a_{n+1},
\]
由夹逼准则，
\[
b_n\to A.
\]
此时两数列均收敛，且极限相同。

\method{情况二：\(\{a_n\}\) 发散}
由于 \(\{a_n\}\) 单调递增，若不收敛，则必有
\[
a_n\to+\infty.
\]
又 \(b_n\ge a_n\)，故
\[
b_n\to+\infty.
\]
此时两数列均发散。

两种情况合起来说明 \(\{a_n\}\) 与 \(\{b_n\}\) 具有相同的敛散性。

\answer{C}
\examnote{从不等式链中先抽出 \(a_n\le a_{n+1}\) 是破题关键；之后就是单调数列定理加夹逼准则。}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 设 \(\lim_{x\to0}\varphi(x)=0\)，则下列命题中正确的个数为（\quad）
\[
\text{① }\lim_{x\to0}\frac{\sin\varphi(x)}{\varphi(x)}=1,
\qquad
\text{② }\lim_{x\to0}\bigl(1+\varphi(x)\bigr)^{1/\varphi(x)}=e,
\]
\[
\text{③ 若 }f'(x_0)=A,\text{ 则 }
\lim_{x\to0}\frac{f(x_0+\varphi(x))-f(x_0)}{\varphi(x)}=A,
\]
\[
\text{④ 若 }\lim_{u\to0}f(u)=A,\text{ 则 }
\lim_{x\to0}f(\varphi(x))=A.
\]

A. 0 个 \qquad B. 2 个 \qquad C. 3 个 \qquad D. 4 个
\end{problemblock}

\begin{solutionblock}
\analysis{本题考查复合极限。前三个命题本质上是把 \(\varphi(x)\) 当作新的无穷小代入标准极限或导数定义；第四个命题则涉及复合极限定理的附加条件，是本题陷阱。}

① 因为 \(\varphi(x)\to0\)，由标准极限
\[
\lim_{u\to0}\frac{\sin u}{u}=1
\]
可得
\[
\lim_{x\to0}\frac{\sin\varphi(x)}{\varphi(x)}=1.
\]

② 同理，由
\[
\lim_{u\to0}(1+u)^{1/u}=e
\]
可得
\[
\lim_{x\to0}(1+\varphi(x))^{1/\varphi(x)}=e.
\]

③ 由 \(f'(x_0)=A\)，有
\[
\lim_{\Delta x\to0}
\frac{f(x_0+\Delta x)-f(x_0)}{\Delta x}=A.
\]
令 \(\Delta x=\varphi(x)\)，且 \(\varphi(x)\to0\)，便得到③成立。

④ 不一定成立。复合极限定理通常要求当 \(x\to0\) 时，内层 \(\varphi(x)\) 在去心邻域内不恒等于外层极限点 \(0\)，或者外层函数在 \(0\) 处连续。反例：令
\[
\varphi(x)\equiv0,\qquad
f(u)=
\begin{cases}
1,&u=0,\\
0,&u\ne0.
\end{cases}
\]
则
\[
\lim_{u\to0}f(u)=0,
\]
但
\[
f(\varphi(x))=f(0)=1,
\]
所以 \(\lim_{x\to0}f(\varphi(x))\ne0\)。④错误。

因此正确的是①②③，共 3 个。

\answer{C}
\examnote{考研中“复合极限”最常考的坑：外函数极限存在，不代表随便代入内函数都行；要注意内函数是否可能总取到外层极限点。}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 极限
\[
\lim_{x\to\infty}
\frac{e^{\sin(1/x)}-1}
{(1+1/x)^\alpha-(1+1/x)}
=A\ne0
\]
的充要条件是（\quad）

A. \(\alpha>1\) \qquad B. \(\alpha\ne1\) \qquad C. \(\alpha>0\) \qquad D. 与 \(\alpha\) 无关
\end{problemblock}

\begin{solutionblock}
\analysis{这是无穷远处的等价无穷小题。令 \(t=1/x\)，则 \(x\to\infty\) 等价于 \(t\to0^+\)，题目转化为比较分子、分母的一阶主部。}

令 \(t=\frac1x\)，原极限为
\[
\lim_{t\to0^+}
\frac{e^{\sin t}-1}{(1+t)^\alpha-(1+t)}.
\]
分子：
\[
\sin t\sim t,\qquad e^{\sin t}-1\sim \sin t\sim t.
\]
分母用二项展开：
\[
(1+t)^\alpha=1+\alpha t+\frac{\alpha(\alpha-1)}2t^2+o(t^2),
\]
所以
\[
(1+t)^\alpha-(1+t)
=(\alpha-1)t+\frac{\alpha(\alpha-1)}2t^2+o(t^2).
\]
若 \(\alpha\ne1\)，分母主部为 \((\alpha-1)t\)，于是
\[
\lim_{t\to0^+}
\frac{e^{\sin t}-1}{(1+t)^\alpha-(1+t)}
=\frac{1}{\alpha-1},
\]
这是非零有限常数。

若 \(\alpha=1\)，分母恒为
\[
(1+t)-(1+t)=0,
\]
原式无意义，不可能等于非零常数 \(A\)。因此充要条件为 \(\alpha\ne1\)。

\answer{B}
\examnote{题干写 \(A\ne0\) 时，重点不是求 \(A\)，而是保证分子分母同阶且分母主系数不为零。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 已知
\[
\lim_{x\to0}\frac{\ln(1+2x)+xf(x)}{x^2}=1,
\]
则
\[
\lim_{x\to0}\frac{2+f(x)}{x}=
\]
（\quad）

A. 1 \qquad B. 2 \qquad C. 3 \qquad D. 4
\end{problemblock}

\begin{solutionblock}
\analysis{题目要求 \(\frac{2+f(x)}x\)，而已知式中有 \(xf(x)\)。应先把分子整理成 \(x[2+f(x)]\) 的形式，再用 \(\ln(1+2x)\) 的 Taylor 展开。}

由 Taylor 公式，
\[
\ln(1+2x)=2x-2x^2+o(x^2).
\]
代入已知分子：
\[
\ln(1+2x)+xf(x)
=2x-2x^2+xf(x)+o(x^2)
=x\bigl(2+f(x)\bigr)-2x^2+o(x^2).
\]
于是
\[
\frac{\ln(1+2x)+xf(x)}{x^2}
=\frac{2+f(x)}x-2+o(1).
\]
已知左端极限为 1，所以
\[
\lim_{x\to0}\left(\frac{2+f(x)}x-2\right)=1,
\]
从而
\[
\lim_{x\to0}\frac{2+f(x)}x=3.
\]

\method{另解：设主部}
由已知式有限可知分子中一阶项必须相消，因此
\[
f(x)=-2+O(x).
\]
设 \(f(x)=-2+kx+o(x)\)，则
\[
\ln(1+2x)+xf(x)
=(2x-2x^2)+x(-2+kx)+o(x^2)
=(k-2)x^2+o(x^2).
\]
已知极限为 1，故 \(k-2=1\)，即 \(k=3\)。而
\[
\frac{2+f(x)}x\to k=3.
\]

\answer{C}
\examnote{遇到“已知极限反求函数主部”，可直接设 \(f(x)\) 的低阶展开，效率很高。}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 设 \(f(x)\) 连续，
\[
\lim_{x\to0}\frac{f(x)}{1-\cos x}=2,
\]
且当 \(x\to0\) 时
\[
\int_0^{\sin^2x} f(t)\,dt
\]
是 \(x\) 的 \(n\) 阶无穷小，则 \(n\) 等于（\quad）

A. 3 \qquad B. 4 \qquad C. 5 \qquad D. 6
\end{problemblock}

\begin{solutionblock}
\analysis{由已知极限先确定 \(f(x)\) 在 0 附近的主部，再代入变上限积分。}
因为
\[
1-\cos x\sim \frac{x^2}{2},
\qquad
\frac{f(x)}{1-\cos x}\to2,
\]
所以
\[
f(x)\sim2(1-\cos x)\sim x^2.
\]
于是 \(t\to0\) 时 \(f(t)\sim t^2\)。又 \(\sin^2x\sim x^2\)，故
\[
\int_0^{\sin^2x}f(t)\,dt
\sim\int_0^{\sin^2x}t^2\,dt
=\frac{(\sin^2x)^3}{3}
\sim\frac{x^6}{3}.
\]
因此它是 \(x\) 的 6 阶无穷小。

\answer{D}
\examnote{变上限积分的阶数可用公式记忆：若 \(f(t)\sim Ct^p\)，上限 \(u(x)\sim x^q\)，则 \(\int_0^{u(x)}f(t)dt\) 的阶数是 \(q(p+1)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 已知当 \(x\to0\) 时，
\[
f(x)=\arctan x-\sin ax,\qquad
g(x)=bx\ln\sqrt{a+x^2}
\]
是等价无穷小，则（\quad）

A. \(a=b=1\) \qquad B. \(a=2,b=\frac13\) \qquad C. \(a=1,b=\frac12\) \qquad D. \(a=1,b=-\frac13\)
\end{problemblock}

\begin{solutionblock}
\analysis{等价无穷小要求二者同阶且主系数相等。先看一次项能否相消。}
展开
\[
\arctan x=x-\frac{x^3}{3}+o(x^3),\qquad
\sin ax=ax-\frac{a^3x^3}{6}+o(x^3).
\]
所以
\[
f(x)=(1-a)x+\left(\frac{a^3}{6}-\frac13\right)x^3+o(x^3).
\]
另一方面
\[
g(x)=\frac{b}{2}x\ln(a+x^2).
\]
若 \(a\ne1\)，则 \(g(x)\sim \frac{b}{2}\ln a\cdot x\)。结合选项，只有 \(a=1\) 时才可能匹配高阶主部。令 \(a=1\)，则
\[
f(x)=\arctan x-\sin x
=-\frac{x^3}{6}+o(x^3),
\]
且
\[
g(x)=bx\ln\sqrt{1+x^2}
=\frac{b}{2}x\ln(1+x^2)
\sim\frac{b}{2}x^3.
\]
等价要求 \(\frac{b}{2}=-\frac16\)，故
\[
b=-\frac13.
\]

\answer{D}
\examnote{此题的关键是先让一次项消失，即 \(a=1\)，否则阶数很难与选项中的 \(g(x)\) 匹配。}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 已知当 \(x\to0\) 时，函数
\[
f(x)=3\sin x-\sin3x
\]
与 \(cx^k\) 是等价无穷小，则（\quad）

A. \(k=1,c=4\) \qquad B. \(k=1,c=-4\) \qquad C. \(k=3,c=4\) \qquad D. \(k=3,c=-4\)
\end{problemblock}

\begin{solutionblock}
\analysis{本题可用三倍角公式迅速降阶，也可用 Taylor 展开。}

\method{方法一：三倍角公式}
\[
\sin3x=3\sin x-4\sin^3x,
\]
所以
\[
3\sin x-\sin3x=4\sin^3x\sim4x^3.
\]
因此 \(k=3,c=4\)。

\method{方法二：Taylor 展开}
\[
3\sin x=3x-\frac{x^3}{2}+o(x^3),
\quad
\sin3x=3x-\frac{27x^3}{6}+o(x^3).
\]
两式相减得
\[
3\sin x-\sin3x=4x^3+o(x^3).
\]

\answer{C}
\examnote{含 \(\sin3x\) 的题优先想到三倍角公式，通常比展开更快。}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 当 \(x\to0^+\) 时，下列无穷小量中最高阶的是（\quad）
\[
\text{A. }\sqrt{1+x^4}-e^{x^2/2},\quad
\text{B. }\tan x-\sin x,
\]
\[
\text{C. }\int_0^{\sin x}\sin t^2\,dt,\quad
\text{D. }\int_0^{1-\cos x}\sin^{3/2}t\,dt.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{“最高阶”就是趋零最快，比较各选项的主部阶数即可。}
\[
\sqrt{1+x^4}=1+\frac{x^4}{2}+o(x^4),\qquad
e^{x^2/2}=1+\frac{x^2}{2}+O(x^4),
\]
故 A 为 2 阶无穷小。
\[
\tan x-\sin x
=\left(x+\frac{x^3}{3}+o(x^3)\right)
-\left(x-\frac{x^3}{6}+o(x^3)\right)
=\frac{x^3}{2}+o(x^3),
\]
故 B 为 3 阶。
对 C，
\[
\sin t^2\sim t^2,\qquad \sin x\sim x,
\]
所以
\[
\int_0^{\sin x}\sin t^2\,dt
\sim\int_0^x t^2\,dt=\frac{x^3}{3},
\]
为 3 阶。
对 D，
\[
\sin^{3/2}t\sim t^{3/2},\qquad 1-\cos x\sim\frac{x^2}{2},
\]
于是
\[
\int_0^{1-\cos x}\sin^{3/2}t\,dt
\sim\int_0^{x^2/2}t^{3/2}\,dt
=C x^5\quad(C>0),
\]
为 5 阶，阶数最高。

\answer{D}
\examnote{积分上限本身也是无穷小，比较阶数时不要漏掉上限带来的复合阶数。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 函数
\[
f(x)=\frac{(e^{1/x}+e)\tan x}{x(e^{1/x}-e)}
\]
在 \([-\pi,\pi]\) 上的第一类间断点是 \(x=\)（\quad）

A. \(0\) \qquad B. \(1\) \qquad C. \(-\frac{\pi}{2}\) \qquad D. \(\frac{\pi}{2}\)
\end{problemblock}

\begin{solutionblock}
\analysis{第一类间断点要求左右极限都存在且有限。逐个考察可能出问题的点：\(x=0\)、\(x=1\)、\(x=\pm\frac{\pi}{2}\)。}
当 \(x\to0^+\) 时，\(e^{1/x}\to+\infty\)，故
\[
\frac{e^{1/x}+e}{e^{1/x}-e}\to1,\qquad \frac{\tan x}{x}\to1,
\]
从而右极限为 1。
当 \(x\to0^-\) 时，\(e^{1/x}\to0\)，故
\[
\frac{e^{1/x}+e}{e^{1/x}-e}\to -1,\qquad \frac{\tan x}{x}\to1,
\]
左极限为 \(-1\)。左右极限有限但不相等，因此 \(x=0\) 是跳跃间断点，属于第一类间断点。

当 \(x=1\) 时，\(e^{1/x}-e=0\)，而 \(\tan1\ne0\)，为无穷间断点。\(x=\pm\frac{\pi}{2}\) 处 \(\tan x\) 无界，也不是第一类间断点。

\answer{A}
\examnote{第一类间断点包括可去与跳跃；无穷间断点、振荡间断点都属于第二类。}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 函数
\[
f(x)=\frac{x^2-x}{x^2-1}\sqrt{1+\frac1{x^2}}
\]
的无穷间断点的个数为（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. 3
\end{problemblock}

\begin{solutionblock}
\analysis{先找定义域中的可疑点：\(x=0,\pm1\)。再分别判断极限类型。}
对 \(x\ne1\)，
\[
\frac{x^2-x}{x^2-1}
=\frac{x(x-1)}{(x-1)(x+1)}
=\frac{x}{x+1}.
\]
在 \(x=1\) 处约去后极限有限，故为可去间断点，不是无穷间断点。

当 \(x\to0^\pm\) 时，
\[
\sqrt{1+\frac1{x^2}}=\frac{\sqrt{x^2+1}}{|x|},
\]
所以
\[
f(x)\sim \frac{x}{x+1}\cdot\frac1{|x|}
\to
\begin{cases}
1,&x\to0^+,\\
-1,&x\to0^-.
\end{cases}
\]
这是跳跃间断点，不是无穷间断点。

当 \(x\to-1\) 时，分母 \(x^2-1\to0\)，而 \(x^2-x\to2\)，根号因子有限且非零，因此函数趋于无穷。故无穷间断点只有 \(x=-1\) 一个。

\answer{B}
\examnote{根号中的 \(1/x^2\) 看似会在 0 处爆掉，但前面的 \(x\) 会抵消一个阶；要算左右极限，不能只凭直觉。}
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 函数
\[
f(x)=\frac{|x|^2-1}{x(x+1)\ln|x|}
\]
的可去间断点的个数为（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. 3
\end{problemblock}

\begin{solutionblock}
\analysis{因为 \(|x|^2=x^2\)，先因式分解并检查 \(x=0,\pm1\)。}
有
\[
|x|^2-1=x^2-1=(x-1)(x+1).
\]
当 \(x\ne-1\) 时可约去 \(x+1\)，得
\[
f(x)=\frac{x-1}{x\ln|x|}.
\]
在 \(x=1\) 处，
\[
\lim_{x\to1}\frac{x-1}{x\ln x}=1,
\]
所以 \(x=1\) 是可去间断点。

在 \(x=-1\) 处，约去后分母 \(x\ln|x|\to0\)，而分子 \(x-1\to-2\)，故为无穷间断点。\(x=0\) 处原式分母趋于 0 而分子趋于 \(-1\)，也不是可去间断点。

\answer{B}
\examnote{可去间断点必须“极限有限”。出现 \(0/0\) 只是候选，不等于一定可去。}
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 已知函数
\[
f(x)=\frac{(x^2+a^2)(x-1)}{e^{1/x}+b}
\]
在 \((-\infty,+\infty)\) 上有一个可去间断点和一个跳跃间断点，则（\quad）

A. \(a=1,b=-1\) \qquad B. \(a=0,b=1\) \qquad C. \(a\ne0,b=-e\) \qquad D. \(a=0,b=-e\)
\end{problemblock}

\begin{solutionblock}
\analysis{间断点来自两处：一是 \(x=0\) 处的 \(e^{1/x}\)，二是分母 \(e^{1/x}+b=0\) 的点。}
若 \(b=-e\)，则
\[
e^{1/x}+b=0
\iff e^{1/x}=e
\iff x=1.
\]
此时分子含有因子 \(x-1\)，所以 \(x=1\) 是可去间断点。

再看 \(x=0\)。当 \(x\to0^+\) 时，\(e^{1/x}\to+\infty\)，故
\[
f(x)\to0.
\]
当 \(x\to0^-\) 时，\(e^{1/x}\to0\)，若 \(b=-e\)，则
\[
f(x)\to\frac{a^2(-1)}{-e}=\frac{a^2}{e}.
\]
若 \(a\ne0\)，左右极限有限但不相等，故 \(x=0\) 是跳跃间断点。于是 \(b=-e,a\ne0\) 符合要求。

若 \(a=0,b=-e\)，则 \(x=0\) 左右极限都为 0，会变成可去间断点，从而不是“一可去一跳跃”。

\answer{C}
\examnote{含 \(e^{1/x}\) 的间断点，几乎总要分别看 \(0^+\) 和 \(0^-\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 设
\[
f(x)=\lim_{n\to\infty}
\frac{2e^{(n+1)x}+1}{e^{nx}+x^n+1},
\]
则 \(f(x)\)（\quad）

A. 仅有一个可去间断点 \qquad B. 仅有一个跳跃间断点

C. 有两个可去间断点 \qquad D. 有两个跳跃间断点
\end{problemblock}

\begin{solutionblock}
\analysis{先按 \(x\) 的范围求极限函数，再判断间断点。关键比较 \(e^{nx}\) 与 \(x^n\) 的增长或衰减。}
当 \(x>0\) 时，因为 \(e^x>x\)，所以 \(e^{nx}\) 支配 \(x^n\)，
\[
f(x)=\lim_{n\to\infty}
\frac{2e^x e^{nx}+1}{e^{nx}+x^n+1}
=2e^x.
\]
当 \(-1<x<0\) 时，\(e^{nx}\to0,\ x^n\to0\)，故
\[
f(x)=1.
\]
当 \(x<-1\) 时，\(|x^n|\to\infty\)，分母由 \(x^n\) 支配，而分子趋于 1，故
\[
f(x)=0.
\]
当 \(x=0\) 时，
\[
f(0)=\frac{2e^0+1}{e^0+0^n+1}=\frac32.
\]
当 \(x=-1\) 时，分母中 \(x^n=(-1)^n\) 振荡，使原数列极限不存在，因此 \(f(-1)\) 不存在。

于是
\[
f(x)=
\begin{cases}
0,&x<-1,\\
1,&-1<x<0,\\
\frac32,&x=0,\\
2e^x,&x>0.
\end{cases}
\]
在 \(x=-1\) 处，左极限为 0，右极限为 1，是跳跃间断点；在 \(x=0\) 处，左极限为 1，右极限为 2，也是跳跃间断点。因此共有两个跳跃间断点。

\answer{D}
\examnote{先求极限函数再谈连续性。不要只盯着 \(x=0\)，这里 \(x=-1\) 由 \(x^n\) 的振荡造成另一个间断点。}
\end{solutionblock}

\section{填空题与计算题}

\begin{problemblock}
\textbf{19.}
\[
\lim_{x\to0}\frac{x-\arcsin x}{(\arcsin x)^3}= \underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{本题考查反三角函数的 Taylor 展开。}
由
\[
\arcsin x=x+\frac{x^3}{6}+o(x^3)
\]
得
\[
x-\arcsin x=-\frac{x^3}{6}+o(x^3),
\qquad
(\arcsin x)^3\sim x^3.
\]
所以
\[
\lim_{x\to0}\frac{x-\arcsin x}{(\arcsin x)^3}
=-\frac16.
\]
\answer{\(-\frac16\)}
\examnote{\(\arcsin x\) 的三阶项是 \(+\frac{x^3}{6}\)，符号很容易写反。}
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 已知
\[
\lim_{x\to0}
\frac{\alpha x^\alpha}
{\sqrt{1+x\arctan x}-\sqrt{\cos x}}
=\frac83,
\]
则 \(\alpha=\underline{\qquad}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先求分母最低阶主部，再让分子同阶。}
当 \(x\to0\) 时，
\[
x\arctan x=x^2+o(x^2),
\]
故
\[
\sqrt{1+x\arctan x}=1+\frac{x^2}{2}+o(x^2).
\]
又
\[
\cos x=1-\frac{x^2}{2}+o(x^2),
\]
所以
\[
\sqrt{\cos x}=1-\frac{x^2}{4}+o(x^2).
\]
分母为
\[
\sqrt{1+x\arctan x}-\sqrt{\cos x}
=\frac{3}{4}x^2+o(x^2).
\]
极限为非零常数，必须有 \(\alpha=2\)。此时
\[
\frac{\alpha x^\alpha}{\frac34x^2}
=\frac{2}{3/4}=\frac83,
\]
满足题意。
\answer{2}
\examnote{“非零有限极限”通常先锁定同阶，再比较主系数。}
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 已知曲线 \(y=f(x)\) 在点 \((0,0)\) 处的切线过点 \((1,2)\)，则
\[
\lim_{x\to0}\left(\cos x+\int_0^x f(t)\,dt\right)^{1/x^2}
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{切线过 \((0,0)\) 与 \((1,2)\)，斜率为 2，所以 \(f(0)=0,\ f'(0)=2\)。}
由可导性，
\[
f(t)=2t+o(t).
\]
于是
\[
\int_0^x f(t)\,dt
=\int_0^x(2t+o(t))\,dt
=x^2+o(x^2).
\]
又
\[
\cos x=1-\frac{x^2}{2}+o(x^2),
\]
故底数
\[
\cos x+\int_0^x f(t)\,dt
=1+\frac{x^2}{2}+o(x^2).
\]
因此
\[
\lim_{x\to0}\left(1+\frac{x^2}{2}+o(x^2)\right)^{1/x^2}
=e^{1/2}.
\]
\answer{\(\sqrt e\)}
\examnote{看到 \(1/x^2\) 型指数，目标是把底数化为 \(1+Cx^2+o(x^2)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{22.}
\[
\lim_{x\to0}
\left[
\frac1{\ln\left(x+\sqrt{1+x^2}\right)}
-\frac1{\ln(1+x)}
\right]
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{利用 \(\ln(x+\sqrt{1+x^2})=\operatorname{arsinh}x\) 的展开。}
有
\[
\ln\left(x+\sqrt{1+x^2}\right)
=x-\frac{x^3}{6}+o(x^3),
\]
而
\[
\ln(1+x)=x-\frac{x^2}{2}+\frac{x^3}{3}+o(x^3).
\]
记
\[
A=\ln\left(x+\sqrt{1+x^2}\right),\qquad B=\ln(1+x).
\]
则
\[
\frac1A-\frac1B=\frac{B-A}{AB}.
\]
其中
\[
B-A=-\frac{x^2}{2}+O(x^3),\qquad AB\sim x^2.
\]
故极限为
\[
-\frac12.
\]
\answer{\(-\frac12\)}
\examnote{两个倒数相减，不要分别展开成很长的倒数级数；先通分更稳。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 设 \(n\) 为正整数，则
\[
\lim_{x\to\infty}
\left[
\frac{x^n}{(x-1)(x-2)\cdots(x-n)}
\right]^x
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是 \(1^\infty\) 型极限，取对数处理。}
令原式为 \(L\)。则
\[
\ln L
=\lim_{x\to\infty}
x\ln\left[
\prod_{k=1}^n\frac1{1-k/x}
\right]
=-\lim_{x\to\infty}x\sum_{k=1}^n\ln\left(1-\frac{k}{x}\right).
\]
因为
\[
\ln(1-u)=-u+o(u),
\]
所以
\[
\ln L
=\lim_{x\to\infty}x\sum_{k=1}^n\left(\frac{k}{x}+o\left(\frac1x\right)\right)
=\sum_{k=1}^n k
=\frac{n(n+1)}2.
\]
故
\[
L=e^{n(n+1)/2}.
\]
\answer{\(e^{\frac{n(n+1)}2}\)}
\examnote{有限个因子连乘，取对数后可以逐项用 \(\ln(1+u)\sim u\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{24.}
\[
\lim_{x\to0}
\left(
\frac{\ln\left(x+\sqrt{1+x^2}\right)}{x}
\right)^{1/x^2}
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{同样使用 \(\operatorname{arsinh}x\) 展开，并化成 \(1^\infty\) 型。}
\[
\ln\left(x+\sqrt{1+x^2}\right)
=x-\frac{x^3}{6}+o(x^3).
\]
因此
\[
\frac{\ln\left(x+\sqrt{1+x^2}\right)}{x}
=1-\frac{x^2}{6}+o(x^2).
\]
于是
\[
\lim_{x\to0}
\left(1-\frac{x^2}{6}+o(x^2)\right)^{1/x^2}
=e^{-1/6}.
\]
\answer{\(e^{-1/6}\)}
\examnote{\((1+Cx^2+o(x^2))^{1/x^2}\to e^C\)，这里 \(C=-\frac16\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 设
\[
x_n=\left(1+\frac1{n^2}\right)
\left(1+\frac2{n^2}\right)\cdots
\left(1+\frac n{n^2}\right),
\]
则
\[
\lim_{n\to\infty}x_n=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{连乘极限优先取对数，把乘积变成求和。}
\[
\ln x_n=\sum_{k=1}^n\ln\left(1+\frac{k}{n^2}\right).
\]
因为 \(0\le k/n^2\le1/n\to0\)，可一致使用
\[
\ln(1+u)=u+O(u^2).
\]
于是
\[
\ln x_n
=\sum_{k=1}^n\frac{k}{n^2}
O\left(\sum_{k=1}^n\frac{k^2}{n^4}\right).
\]
其中
\[
\sum_{k=1}^n\frac{k}{n^2}
=\frac{n(n+1)}{2n^2}\to\frac12,
\qquad
\sum_{k=1}^n\frac{k^2}{n^4}=O\left(\frac1n\right)\to0.
\]
所以 \(\ln x_n\to\frac12\)，从而
\[
x_n\to e^{1/2}=\sqrt e.
\]
\answer{\(\sqrt e\)}
\examnote{乘积中每一项都趋于 1 时，通常是“取对数 + 等价求和”。}
\end{solutionblock}

\begin{problemblock}
\textbf{26.}
\[
\lim_{n\to\infty}
\frac{\sqrt1+\sqrt2+\cdots+\sqrt n}
{\sqrt{n(1+2+\cdots+n)}}
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{分子是幂和，分母可直接化简。}
分母
\[
\sqrt{n(1+2+\cdots+n)}
=\sqrt{n\cdot\frac{n(n+1)}2}
\sim\frac{n^{3/2}}{\sqrt2}.
\]
分子用 Riemann 和：
\[
\sqrt1+\sqrt2+\cdots+\sqrt n
=n^{1/2}\sum_{k=1}^n\sqrt{\frac{k}{n}}
\sim n^{1/2}\cdot n\int_0^1\sqrt t\,dt
=n^{3/2}\cdot\frac23.
\]
因此极限为
\[
\frac{2/3}{1/\sqrt2}
=\frac{2\sqrt2}{3}.
\]
\answer{\(\frac{2\sqrt2}{3}\)}
\examnote{\(\sum_{k=1}^n k^\alpha\sim \frac{n^{\alpha+1}}{\alpha+1}\) 是考研常用结论。}
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 确定常数 \(a,b\)，使 \(x\to0\) 时
\[
f(x)=e^x-\frac{1+ax}{1+bx}
\]
为 \(x\) 的三阶无穷小。
\end{problemblock}

\begin{solutionblock}
\analysis{要成为三阶无穷小，常数项、一次项、二次项都要相消，三次项不为零。}
展开
\[
e^x=1+x+\frac{x^2}{2}+\frac{x^3}{6}+o(x^3).
\]
又
\[
\frac{1+ax}{1+bx}
=(1+ax)(1-bx+b^2x^2-b^3x^3+o(x^3)),
\]
即
\[
\frac{1+ax}{1+bx}
=1+(a-b)x+(b^2-ab)x^2+(ab^2-b^3)x^3+o(x^3).
\]
令 \(f(x)\) 的一次、二次项系数为 0：
\[
1-(a-b)=0,
\]
\[
\frac12-(b^2-ab)=0.
\]
由第一式 \(a-b=1\)。于是
\[
b^2-ab=b(b-a)=-b(a-b)=-b.
\]
代入第二式得
\[
\frac12+b=0,\qquad b=-\frac12.
\]
因此
\[
a=b+1=\frac12.
\]
此时三次项系数为
\[
\frac16-(ab^2-b^3)
=\frac16-b^2(a-b)
=\frac16-\frac14
=-\frac1{12}\ne0,
\]
故确为三阶无穷小。

\answer{\(a=\frac12,\ b=-\frac12\)}
\examnote{“三阶无穷小”不是只让一阶项消失，而是要消到二阶，三阶项保留。}
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 当 \(x\to0\) 时，
\[
1-\cos x\cos2x\cos3x
\]
与 \(ax^n\) 为等价无穷小，求 \(n\) 与 \(a\) 的值。
\end{problemblock}

\begin{solutionblock}
\analysis{多个余弦相乘时，只需保留到 \(x^2\) 项。}
\[
\cos kx=1-\frac{k^2x^2}{2}+o(x^2).
\]
因此
\[
\cos x\cos2x\cos3x
=\left(1-\frac{x^2}{2}\right)
\left(1-2x^2\right)
\left(1-\frac{9x^2}{2}\right)+o(x^2).
\]
乘积的一阶主部为
\[
1-\frac{1+4+9}{2}x^2+o(x^2)
=1-7x^2+o(x^2).
\]
故
\[
1-\cos x\cos2x\cos3x
=7x^2+o(x^2).
\]
\answer{\(n=2,\ a=7\)}
\examnote{\(\prod(1+u_k)=1+\sum u_k+o(u)\)，保留同阶项即可，不必完全展开。}
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 已知
\[
\lim_{x\to0}
\frac{(1+\sin2x^2)^{1/x^2}-e^2}{x^n}
=a\quad(a\ne0),
\]
求 \(a\) 和 \(n\) 的值。
\end{problemblock}

\begin{solutionblock}
\analysis{这是指数型函数与常数 \(e^2\) 的差值，先展开指数的对数。}
设
\[
H(x)=(1+\sin2x^2)^{1/x^2}.
\]
则
\[
\ln H(x)=\frac1{x^2}\ln(1+\sin2x^2).
\]
因为
\[
\sin2x^2=2x^2+o(x^4),
\]
且
\[
\ln(1+u)=u-\frac{u^2}{2}+o(u^2),
\]
所以
\[
\ln(1+\sin2x^2)
=2x^2-\frac{(2x^2)^2}{2}+o(x^4)
=2x^2-2x^4+o(x^4).
\]
从而
\[
\ln H(x)=2-2x^2+o(x^2),
\]
\[
H(x)=e^2e^{-2x^2+o(x^2)}
=e^2\bigl(1-2x^2+o(x^2)\bigr).
\]
于是
\[
H(x)-e^2=-2e^2x^2+o(x^2).
\]
因此
\[
n=2,\qquad a=-2e^2.
\]
\answer{\(n=2,\ a=-2e^2\)}
\examnote{指数型差值 \(e^{A+\varepsilon}-e^A\sim e^A\varepsilon\)，这里 \(\varepsilon=-2x^2\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 确定常数 \(a,b,c\) 的值，使
\[
\lim_{x\to0}
\frac{ax-\sin x}
{\displaystyle\int_b^x\frac{\ln(1+t^3)}{t}\,dt}
=c\quad(c\ne0).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{要使极限为非零有限数，分子和分母必须同阶趋于 0。}
若 \(b\ne0\)，则当 \(x\to0\) 时分母趋于常数
\[
\int_b^0\frac{\ln(1+t^3)}{t}\,dt,
\]
而分子趋于 0，极限不可能为非零常数。因此必须
\[
b=0.
\]
此时
\[
\frac{\ln(1+t^3)}{t}\sim\frac{t^3}{t}=t^2,
\]
所以
\[
\int_0^x\frac{\ln(1+t^3)}{t}\,dt
\sim\int_0^x t^2\,dt=\frac{x^3}{3}.
\]
分子
\[
ax-\sin x=(a-1)x+\frac{x^3}{6}+o(x^3).
\]
为了与分母同为三阶，必须
\[
a=1.
\]
于是
\[
ax-\sin x=x-\sin x\sim\frac{x^3}{6}.
\]
故
\[
c=\frac{1/6}{1/3}=\frac12.
\]
\answer{\(a=1,\ b=0,\ c=\frac12\)}
\examnote{含参数积分下限时，先判断分母是否趋于 0；否则不可能得到非零有限极限。}
\end{solutionblock}

\begin{problemblock}
\textbf{31.}
\[
\lim_{x\to0}
\left[
\frac1{\ln(1+x^2)}-\frac1{\sin^2x}
\right].
\]
\end{problemblock}

\begin{solutionblock}
\analysis{两个倒数相减，通分后比较四阶主部。}
通分得
\[
\frac1{\ln(1+x^2)}-\frac1{\sin^2x}
=\frac{\sin^2x-\ln(1+x^2)}
{\ln(1+x^2)\sin^2x}.
\]
展开
\[
\sin^2x=x^2-\frac{x^4}{3}+o(x^4),
\]
\[
\ln(1+x^2)=x^2-\frac{x^4}{2}+o(x^4).
\]
所以
\[
\sin^2x-\ln(1+x^2)
=\frac{x^4}{6}+o(x^4),
\]
而分母
\[
\ln(1+x^2)\sin^2x\sim x^4.
\]
故极限为
\[
\frac16.
\]
\answer{\(\frac16\)}
\examnote{这里二阶项相同，必须展开到四阶。}
\end{solutionblock}

\begin{problemblock}
\textbf{32.}
\[
\lim_{x\to0^+}
\frac{x^x-(\sin x)^x}{x^2\ln(1+x)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{幂函数底数和指数都含 \(x\)，先写成指数形式。}
\[
x^x=e^{x\ln x},\qquad
(\sin x)^x=e^{x\ln(\sin x)}.
\]
又
\[
\ln(\sin x)=\ln x+\ln\frac{\sin x}{x}.
\]
当 \(x\to0^+\) 时，
\[
\frac{\sin x}{x}=1-\frac{x^2}{6}+o(x^2),
\]
所以
\[
\ln\frac{\sin x}{x}=-\frac{x^2}{6}+o(x^2).
\]
因此
\[
x\ln(\sin x)
=x\ln x-\frac{x^3}{6}+o(x^3).
\]
于是
\[
x^x-(\sin x)^x
=e^{x\ln x}\left(1-e^{-x^3/6+o(x^3)}\right)
\sim \frac{x^3}{6},
\]
因为 \(e^{x\ln x}\to1\)。分母
\[
x^2\ln(1+x)\sim x^3.
\]
故极限为
\[
\frac16.
\]
\answer{\(\frac16\)}
\examnote{本题的细节在 \(x\ln x\to0\)，所以 \(e^{x\ln x}\to1\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{33.}
\[
\lim_{x\to0}
\frac{\ln(1+x^2)-\ln(1+\sin^2x)}
{x\sin^3x}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{分子是两个对数之差，可先看内部变量 \(x^2\) 与 \(\sin^2x\) 的差。}
由
\[
\sin x=x-\frac{x^3}{6}+o(x^3)
\]
可得
\[
\sin^2x=x^2-\frac{x^4}{3}+o(x^4).
\]
因此
\[
x^2-\sin^2x=\frac{x^4}{3}+o(x^4).
\]
利用
\[
\ln(1+u)-\ln(1+v)\sim u-v
\]
在 \(u,v\to0\) 且 \(u-v\) 为主部时成立，得
\[
\ln(1+x^2)-\ln(1+\sin^2x)
\sim\frac{x^4}{3}.
\]
分母
\[
x\sin^3x\sim x\cdot x^3=x^4.
\]
故极限为
\[
\frac13.
\]
\answer{\(\frac13\)}
\examnote{差值型对数题常用 \(\ln(1+u)-\ln(1+v)=\ln\left(1+\frac{u-v}{1+v}\right)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{34.}
\[
\lim_{x\to+\infty}
\frac{\displaystyle\int_1^x\left[t^2\left(e^{1/t}-1\right)-t\right]\,dt}
{x^2\ln\left(1+\frac1x\right)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先求被积函数在 \(t\to+\infty\) 时的主部。}
\[
e^{1/t}-1=\frac1t+\frac1{2t^2}+\frac1{6t^3}+O\left(\frac1{t^4}\right).
\]
所以
\[
t^2(e^{1/t}-1)-t
=t+\frac12+\frac1{6t}+O\left(\frac1{t^2}\right)-t
=\frac12+O\left(\frac1t\right).
\]
因此分子
\[
\int_1^x\left[t^2(e^{1/t}-1)-t\right]dt
=\frac{x}{2}+O(\ln x).
\]
分母
\[
x^2\ln\left(1+\frac1x\right)\sim x^2\cdot\frac1x=x.
\]
故极限为
\[
\frac12.
\]
\answer{\(\frac12\)}
\examnote{积分上限趋于无穷时，先判断被积函数主部，再积分。}
\end{solutionblock}

\begin{problemblock}
\textbf{35.} 求下列极限：
\[
(1)\ \lim_{x\to0}\left(\frac{\ln(1+x)}x\right)^{1/(e^x-1)};
\]
\[
(2)\ \lim_{x\to0}\left(\frac{e^x+e^{2x}+\cdots+e^{nx}}n\right)^{1/x};
\]
\[
(3)\ \lim_{n\to\infty}\left(n\tan\frac1n\right)^{n^2};
\qquad
(4)\ \lim_{n\to\infty}\tan^n\left(\frac\pi4+\frac2n\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{四个都是 \(1^\infty\) 型，统一取对数。}
(1) 设极限为 \(L_1\)，则
\[
\ln L_1
=\lim_{x\to0}\frac{\ln\left(\frac{\ln(1+x)}x\right)}{e^x-1}.
\]
因为
\[
\frac{\ln(1+x)}x=1-\frac{x}{2}+o(x),
\]
所以分子 \(\sim-\frac{x}{2}\)，分母 \(\sim x\)，故
\[
L_1=e^{-1/2}.
\]

(2) 平均值展开为
\[
\frac{e^x+e^{2x}+\cdots+e^{nx}}n
=1+\frac{1+2+\cdots+n}{n}x+o(x)
=1+\frac{n+1}{2}x+o(x).
\]
故极限为
\[
e^{(n+1)/2}.
\]

(3) 因为
\[
\tan\frac1n=\frac1n+\frac1{3n^3}+O\left(\frac1{n^5}\right),
\]
所以
\[
n\tan\frac1n=1+\frac1{3n^2}+O\left(\frac1{n^4}\right),
\]
极限为
\[
e^{1/3}.
\]

(4) 令 \(u=\frac2n\)。在 \(x=\frac\pi4\) 处，
\[
\left(\ln\tan x\right)'=\frac{\sec^2x}{\tan x}=2.
\]
因此
\[
\ln\tan\left(\frac\pi4+\frac2n\right)
=2\cdot\frac2n+o\left(\frac1n\right)=\frac4n+o\left(\frac1n\right).
\]
所以极限为
\[
e^4.
\]

\answer{(1) \(e^{-1/2}\)；(2) \(e^{(n+1)/2}\)；(3) \(e^{1/3}\)；(4) \(e^4\)}
\examnote{\(1^\infty\) 型不要硬算原式，取对数后只保留一阶主部。}
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 求下列极限：
\[
(1)\ \lim_{x\to+\infty}\left(x+\sqrt{1+x^2}\right)^{1/x};
\qquad
(2)\ \lim_{x\to+\infty}\left(x^{1/x}-1\right)^{1/\ln x}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{仍然取对数。}
(1)
\[
\frac1x\ln\left(x+\sqrt{1+x^2}\right)
\sim\frac{\ln(2x)}x\to0,
\]
故极限为 \(e^0=1\)。

(2) 令 \(y=\frac{\ln x}{x}\)，则 \(y\to0^+\)，
\[
x^{1/x}-1=e^y-1\sim y=\frac{\ln x}{x}.
\]
于是
\[
\ln\left[\left(x^{1/x}-1\right)^{1/\ln x}\right]
=\frac{\ln(x^{1/x}-1)}{\ln x}
\sim\frac{\ln(\ln x)-\ln x}{\ln x}\to-1.
\]
故极限为 \(e^{-1}\)。

\answer{(1) \(1\)；(2) \(e^{-1}\)}
\examnote{第二题的底数趋于 0，不是 \(1^\infty\)，但取对数仍是最稳路线。}
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 已知函数 \(f(x)\) 在 \(x=0\) 的某邻域内可导，且
\[
\lim_{x\to0}\left(\frac{\sin x}{x^2}+\frac{f(x)}x\right)=2,
\]
求 \(f(0),f'(0)\) 及
\[
\lim_{x\to0}\frac{x}{f(x)+e^x}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{要让极限有限，\(\frac1x\) 型发散项必须相消。}
设
\[
f(x)=f(0)+f'(0)x+o(x).
\]
又
\[
\frac{\sin x}{x^2}=\frac1x-\frac{x}{6}+o(x).
\]
因此
\[
\frac{\sin x}{x^2}+\frac{f(x)}x
=\frac{1+f(0)}x+f'(0)+o(1).
\]
极限有限，必须
\[
1+f(0)=0,\qquad f(0)=-1.
\]
此时极限等于 \(f'(0)\)，所以
\[
f'(0)=2.
\]
于是
\[
f(x)=-1+2x+o(x),\qquad e^x=1+x+o(x),
\]
故
\[
f(x)+e^x=3x+o(x),
\]
从而
\[
\lim_{x\to0}\frac{x}{f(x)+e^x}=\frac13.
\]
\answer{\(f(0)=-1,\ f'(0)=2,\ \lim=\frac13\)}
\examnote{有限极限常常来自发散项相消，这是反求函数值的高频技巧。}
\end{solutionblock}

\begin{problemblock}
\textbf{38.}
\[
\lim_{n\to\infty}
\left(
\frac1{\sqrt{n^6+n}}+
\frac{2^2}{\sqrt{n^6+2n}}+\cdots+
\frac{n^2}{\sqrt{n^6+n^2}}
\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{分母统一提取 \(n^3\)。}
第 \(k\) 项为
\[
\frac{k^2}{\sqrt{n^6+kn}}
=\frac{k^2}{n^3\sqrt{1+k/n^5}}.
\]
因为 \(1\le k\le n\)，有 \(k/n^5\to0\)，故
\[
\frac{k^2}{\sqrt{n^6+kn}}\sim\frac{k^2}{n^3}.
\]
于是
\[
\sum_{k=1}^n\frac{k^2}{\sqrt{n^6+kn}}
\sim\frac1{n^3}\sum_{k=1}^n k^2
\to\frac13.
\]
\answer{\(\frac13\)}
\examnote{\(\sum k^2\sim n^3/3\)，这是数列极限中最常用的幂和主部。}
\end{solutionblock}

\begin{problemblock}
\textbf{39.}
\[
\lim_{n\to\infty}
\left(
\frac1{\sqrt{n^2}}+
\frac1{\sqrt{n^2-1^2}}+\cdots+
\frac1{\sqrt{n^2-(n-1)^2}}
\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{化成 Riemann 和，注意右端点是 1 附近的广义积分。}
\[
\frac1{\sqrt{n^2-k^2}}
=\frac1n\cdot\frac1{\sqrt{1-(k/n)^2}}.
\]
因此原和为
\[
\frac1n\sum_{k=0}^{n-1}
\frac1{\sqrt{1-(k/n)^2}}
\to\int_0^1\frac{dt}{\sqrt{1-t^2}}
=\frac\pi2.
\]
\answer{\(\frac\pi2\)}
\examnote{虽然 \(t=1\) 处被积函数无界，但广义积分收敛，Riemann 和仍可对应。}
\end{solutionblock}

\begin{problemblock}
\textbf{40.}
\[
\lim_{n\to\infty}
\left(
\frac{n+1}{1^2+n^2}+
\frac{n+\frac12}{2^2+n^2}+\cdots+
\frac{n+\frac1n}{n^2+n^2}
\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把分子拆成 \(n\) 与 \(1/k\) 两部分。}
原和等于
\[
\sum_{k=1}^n\frac{n}{k^2+n^2}
+\sum_{k=1}^n\frac{1/k}{k^2+n^2}.
\]
第一部分
\[
\sum_{k=1}^n\frac{n}{k^2+n^2}
=\frac1n\sum_{k=1}^n\frac1{1+(k/n)^2}
\to\int_0^1\frac{dt}{1+t^2}
=\frac\pi4.
\]
第二部分估计为
\[
0\le
\sum_{k=1}^n\frac{1/k}{k^2+n^2}
\le \frac1{n^2}\sum_{k=1}^n\frac1k
\to0.
\]
故极限为
\[
\frac\pi4.
\]
\answer{\(\frac\pi4\)}
\examnote{复杂分子先拆项，主要部分做 Riemann 和，次要部分用估计压掉。}
\end{solutionblock}

\begin{problemblock}
\textbf{41.} 求函数
\[
f(x)=
\begin{cases}
\dfrac{x|x|+1}{\ln|x|},&x\ne0,\\
1,&x=0
\end{cases}
\]
的间断点并指出类型。
\end{problemblock}

\begin{solutionblock}
\analysis{可疑点来自 \(x=0\)、\(\ln|x|=0\) 以及绝对值表达式的分段点，即 \(x=-1,0,1\)。}
当 \(x\to0\) 时，
\[
\frac{x|x|+1}{\ln|x|}\to0,
\]
但 \(f(0)=1\)，故 \(x=0\) 为可去间断点。

当 \(x\to1\) 时，分子趋于 2，分母 \(\ln|x|\to0\)，故 \(x=1\) 为无穷间断点。

当 \(x\to-1\) 时，附近 \(x<0\)，故 \(|x|=-x\)，于是
\[
x|x|+1=1-x^2=(1-x)(1+x).
\]
令 \(h=x+1\)，则 \(x=-1+h\)，
\[
\ln|x|=\ln|1-h|\sim-h.
\]
同时
\[
1-x^2=1-(-1+h)^2=2h-h^2\sim2h.
\]
故
\[
\lim_{x\to-1}\frac{x|x|+1}{\ln|x|}
=\lim_{h\to0}\frac{2h-h^2}{-h}=-2.
\]
极限存在且有限，但原函数在 \(x=-1\) 无定义，所以 \(x=-1\) 为可去间断点。

\answer{\(x=-1\) 与 \(x=0\) 为可去间断点；\(x=1\) 为无穷间断点。}
\examnote{绝对值题一定分左右，尤其在绝对值零点处。}
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 设
\[
f(x)=\lim_{n\to\infty}
\frac{x^{2n-1}+ax^2+bx}{x^{2n}+1}
\]
在 \((-\infty,+\infty)\) 内连续，试确定常数 \(a\) 和 \(b\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先求极限函数，再在分界点 \(x=\pm1\) 处拼接连续。}
当 \(|x|<1\) 时，\(x^{2n}\to0,\ x^{2n-1}\to0\)，
\[
f(x)=ax^2+bx.
\]
当 \(|x|>1\) 时，分子分母同除以 \(x^{2n}\)，
\[
f(x)=\frac1x.
\]
在 \(x=1\) 处，
\[
f(1)=\frac{1+a+b}{2},
\]
连续要求左右极限相同，即
\[
a+b=1.
\]
在 \(x=-1\) 处，
\[
f(-1)=\frac{a-b-1}{2},
\]
连续要求
\[
a-b=-1.
\]
解方程组
\[
\begin{cases}
a+b=1,\\
a-b=-1
\end{cases}
\]
得
\[
a=0,\qquad b=1.
\]
\answer{\(a=0,\ b=1\)}
\examnote{含 \(x^{2n}\) 的极限函数通常按 \(|x|<1, |x|>1, x=\pm1\) 分段。}
\end{solutionblock}

\begin{problemblock}
\textbf{43.} 设 \(f(x)\) 是区间 \([0,+\infty)\) 上单调减且非负的连续函数，
\[
a_n=\sum_{k=1}^n f(k)-\int_1^n f(x)\,dx\quad(n=1,2,\cdots),
\]
证明数列 \(\{a_n\}\) 的极限存在。
\end{problemblock}

\begin{solutionblock}
\analysis{证明极限存在，常用“单调有界”。}
先看单调性：
\[
a_{n+1}-a_n
=f(n+1)-\int_n^{n+1}f(x)\,dx.
\]
由于 \(f\) 单调减，\(x\in[n,n+1]\) 时
\[
f(x)\ge f(n+1),
\]
所以
\[
\int_n^{n+1}f(x)\,dx\ge f(n+1).
\]
因此
\[
a_{n+1}-a_n\le0,
\]
即 \(\{a_n\}\) 单调递减。

再证有下界。对 \(k=1,\dots,n-1\)，由单调减知
\[
\int_k^{k+1}f(x)\,dx\le f(k).
\]
于是
\[
\int_1^n f(x)\,dx
\le\sum_{k=1}^{n-1}f(k).
\]
故
\[
a_n=\sum_{k=1}^n f(k)-\int_1^n f(x)\,dx
\ge f(n)\ge0.
\]
所以 \(\{a_n\}\) 单调递减且有下界，极限存在。
\examnote{单调函数与积分比较，是考研证明数列收敛的经典套路。}
\end{solutionblock}

\begin{problemblock}
\textbf{44.} 设
\[
x_1=\sqrt2,\qquad x_{n+1}=\sqrt{3+2x_n}\quad(n=1,2,\cdots),
\]
证明数列 \(\{x_n\}\) 收敛并求它的极限。
\end{problemblock}

\begin{solutionblock}
\analysis{递推根式题通常先猜极限，再证单调有界。}
若极限为 \(L\)，则
\[
L=\sqrt{3+2L},
\]
即
\[
L^2-2L-3=0.
\]
因 \(x_n>0\)，故 \(L=3\)。

证明收敛：先证 \(x_n<3\)。\(x_1=\sqrt2<3\)，若 \(x_n<3\)，则
\[
x_{n+1}=\sqrt{3+2x_n}<\sqrt9=3.
\]
再证单调递增。当 \(0<x_n<3\) 时，
\[
x_{n+1}>x_n
\iff 3+2x_n>x_n^2
\iff (3-x_n)(x_n+1)>0,
\]
成立。因此 \(\{x_n\}\) 单调递增且有上界 3，必收敛，极限为 3。
\answer{收敛，极限为 \(3\)}
\examnote{根式递推题的标准链条：正性、上界、单调、代入求极限。}
\end{solutionblock}

\begin{problemblock}
\textbf{45.} 设数列 \(\{x_n\}\) 满足
\[
x_1=1,\qquad x_{n+1}=\frac{x_n+2}{x_n+1}\quad(n=1,2,\cdots),
\]
试证
\[
\lim_{n\to\infty}x_n=\sqrt2.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{递推函数的不动点为 \(\sqrt2\)，用误差压缩最简洁。}
显然 \(x_n>0\)。计算误差：
\[
x_{n+1}-\sqrt2
=\frac{x_n+2}{x_n+1}-\sqrt2
=\frac{x_n+2-\sqrt2(x_n+1)}{x_n+1}.
\]
分子可化为
\[
x_n+2-\sqrt2x_n-\sqrt2
=(1-\sqrt2)x_n+(2-\sqrt2)
=-(\sqrt2-1)(x_n-\sqrt2).
\]
所以
\[
|x_{n+1}-\sqrt2|
=\frac{\sqrt2-1}{x_n+1}|x_n-\sqrt2|
\le(\sqrt2-1)|x_n-\sqrt2|.
\]
由于 \(0<\sqrt2-1<1\)，反复迭代得
\[
|x_n-\sqrt2|\le(\sqrt2-1)^{n-1}|x_1-\sqrt2|\to0.
\]
因此
\[
\lim_{n\to\infty}x_n=\sqrt2.
\]
\examnote{分式递推证明收敛时，误差压缩法往往比单调有界更干净。}
\end{solutionblock}

\begin{problemblock}
\textbf{46.} 设函数
\[
f(x)=\ln x+\frac1x.
\]
(1) 求 \(f(x)\) 的最小值；

(2) 设数列 \(\{x_n\}\) 满足
\[
\ln x_n+\frac1{x_{n+1}}<1,
\]
证明 \(\lim_{n\to\infty}x_n\) 存在，并求此极限。
\end{problemblock}

\begin{solutionblock}
\analysis{先用函数最小值建立数列不等式。}
(1) 定义域为 \(x>0\)，
\[
f'(x)=\frac1x-\frac1{x^2}=\frac{x-1}{x^2}.
\]
所以 \(f(x)\) 在 \((0,1)\) 上递减，在 \((1,+\infty)\) 上递增，最小值为
\[
f(1)=1.
\]

(2) 由 (1) 知对任意 \(x_n>0\)，
\[
\ln x_n+\frac1{x_n}\ge1.
\]
又已知
\[
\ln x_n+\frac1{x_{n+1}}<1,
\]
两式比较得
\[
\frac1{x_n}>\frac1{x_{n+1}},
\]
故
\[
x_{n+1}>x_n.
\]
此外由已知式有 \(\ln x_n<1\)，即
\[
x_n<e.
\]
所以 \(\{x_n\}\) 单调递增且有上界，极限存在。设极限为 \(L\)，则 \(L>0\)。由
\[
\ln x_n+\frac1{x_{n+1}}<1
\]
取极限得
\[
\ln L+\frac1L\le1.
\]
但由 (1) 又有
\[
\ln L+\frac1L\ge1.
\]
故
\[
\ln L+\frac1L=1.
\]
等号只在 \(L=1\) 处取得，所以
\[
\lim_{n\to\infty}x_n=1.
\]
\answer{(1) 最小值为 \(1\)；(2) 极限存在且为 \(1\)。}
\examnote{函数最值与数列单调有界结合，是考研证明题常见设计。}
\end{solutionblock}

\begin{problemblock}
\textbf{47.} 设
\[
x_1>0,\qquad x_{n+1}=\ln(1+x_n)\quad(n=1,2,\cdots).
\]
证明：(1) \(\{x_n\}\) 收敛并求极限；

(2) 计算
\[
\lim_{n\to\infty}\left(\frac{x_{n+1}}{x_n}\right)^{1/x_n}
\quad\text{及}\quad
\lim_{n\to\infty}\left(\frac1{x_n}-\frac1{x_{n+1}}\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先由递推式证明 \(x_n\to0\)，再把两个极限转成 \(x_n\to0\) 的函数极限。}
当 \(x>0\) 时，
\[
0<\ln(1+x)<x.
\]
因此
\[
0<x_{n+1}<x_n,
\]
数列单调递减且有下界 0，故收敛。设极限为 \(L\ge0\)，由递推式取极限得
\[
L=\ln(1+L).
\]
该方程在 \(L\ge0\) 上唯一解为 \(L=0\)，所以
\[
x_n\to0.
\]

对第一个极限，
\[
\frac{x_{n+1}}{x_n}
=\frac{\ln(1+x_n)}{x_n}
=1-\frac{x_n}{2}+o(x_n).
\]
故
\[
\left(\frac{x_{n+1}}{x_n}\right)^{1/x_n}\to e^{-1/2}.
\]

对第二个极限，
\[
\frac1{x_n}-\frac1{x_{n+1}}
=\frac{x_{n+1}-x_n}{x_nx_{n+1}}.
\]
而
\[
x_{n+1}=x_n-\frac{x_n^2}{2}+o(x_n^2),
\]
且 \(x_{n+1}\sim x_n\)，所以
\[
\frac{x_{n+1}-x_n}{x_nx_{n+1}}
\to -\frac12.
\]
\answer{(1) 收敛，极限为 \(0\)；(2) 两个极限分别为 \(e^{-1/2}\)、\(-\frac12\)。}
\examnote{递推数列极限题，先证明趋向 0，再用标准展开处理后续极限。}
\end{solutionblock}

\begin{problemblock}
\textbf{48.} 设 \(f(x)\) 在 \([0,2a]\ (a>0)\) 上连续，且
\[
f(0)=f(2a).
\]
求证存在 \(\xi\in[0,a]\)，使
\[
f(\xi)=f(\xi+a).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{构造差函数，把结论变成零点存在问题。}
令
\[
g(x)=f(x)-f(x+a),\qquad x\in[0,a].
\]
由于 \(f\) 连续，\(g\) 在 \([0,a]\) 上连续。并且
\[
g(0)=f(0)-f(a),
\]
\[
g(a)=f(a)-f(2a)=f(a)-f(0)=-g(0).
\]
若 \(g(0)=0\)，取 \(\xi=0\) 即可。若 \(g(0)\ne0\)，则 \(g(0)\) 与 \(g(a)\) 异号，由零点定理，存在 \(\xi\in(0,a)\)，使
\[
g(\xi)=0.
\]
即
\[
f(\xi)=f(\xi+a).
\]
\examnote{端点条件呈对称形式时，优先构造 \(f(x)-f(x+a)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{49.} 设 \(f(x)\) 在 \([a,b]\) 上连续，\(x_i\in[a,b]\)，\(t_i>0\ (i=1,2,\cdots,n)\)，且
\[
\sum_{i=1}^n t_i=1.
\]
试证至少存在一点 \(\xi\in[a,b]\)，使
\[
f(\xi)=t_1f(x_1)+t_2f(x_2)+\cdots+t_nf(x_n).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是连续函数介值定理与加权平均的结合。}
因为 \(f\) 在闭区间 \([a,b]\) 上连续，所以存在最小值 \(m\) 与最大值 \(M\)，使
\[
m\le f(x)\le M,\qquad x\in[a,b].
\]
于是对每个 \(i\)，
\[
m\le f(x_i)\le M.
\]
由 \(t_i>0\) 且 \(\sum t_i=1\)，加权求和得
\[
m\le \sum_{i=1}^n t_if(x_i)\le M.
\]
记
\[
S=\sum_{i=1}^n t_if(x_i).
\]
由于 \(S\in[m,M]\)，而连续函数 \(f\) 在 \([a,b]\) 上能取遍 \([m,M]\) 中的每个值，由介值定理，存在 \(\xi\in[a,b]\)，使
\[
f(\xi)=S.
\]
即结论成立。
\examnote{“权重为正且和为 1”意味着加权平均不会超出最小值和最大值之间。}
\end{solutionblock}

"""

CH02_TEX = r"""\chapter{一元函数微分学}

\section{原题页索引}
本章原题对应做题本第 19--38 页。原题页图片已随 Overleaf 项目打包。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_019.png}
\end{center}

\section{选择题}

\begin{problemblock}
\textbf{1.} 设 \(f(x)\) 在 \(x=0\) 处连续，则 \(f(x)\) 在 \(x=0\) 处可导的充分条件是（\quad）

A. \(\displaystyle\lim_{x\to0}\frac{f(x)-f(-x)}{2x}\) 存在。

B. \(\displaystyle\lim_{x\to0}\frac{f(\ln(1+x^2))-f(0)}{x^2}\) 存在。

C. \(\displaystyle\lim_{x\to0}\frac{f(x)-f(0)}{\sqrt[3]{x}}\) 存在。

D. \(\displaystyle\lim_{x\to\infty}x f\left(\frac1x\right)\) 存在。
\end{problemblock}

\begin{solutionblock}
\analysis{题目问“充分条件”，要找能推出导数定义极限存在的选项。}
对 D，令 \(t=\frac1x\)，则 \(x\to\infty\) 等价于 \(t\to0\)，且
\[
x f\left(\frac1x\right)=\frac{f(t)}{t}.
\]
若该极限存在且有限，由 \(f\) 在 0 处连续可知 \(f(t)\to f(0)\)。若 \(\frac{f(t)}t\) 有有限极限，则必有 \(f(0)=0\)，否则 \(\frac{f(t)}t\) 会发散。因此
\[
f'(0)=\lim_{t\to0}\frac{f(t)-f(0)}t
=\lim_{t\to0}\frac{f(t)}t
\]
存在，故 D 是充分条件。

其余选项不能推出可导。A 只控制对称差商，例如 \(f(x)=|x|\) 时 A 中极限为 0，但 \(f\) 在 0 不可导。B 只沿 \(\ln(1+x^2)\ge0\) 的右侧路径控制变化，不能保证双侧导数。C 中分母是 \(\sqrt[3]x\)，即使极限存在，也不能推出 \(\frac{f(x)-f(0)}x\) 存在。

\answer{D}
\examnote{可导的核心是 \(\frac{f(x)-f(0)}x\) 的双侧极限；偏路径、对称差商、换错尺度都不够。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 设
\[
f(x)=
\begin{cases}
x^2\sin\frac1x,&x\ne0,\\
0,&x=0,
\end{cases}
\]
则在点 \(x=0\) 处函数 \(f(x)\)（\quad）

A. 不连续 \qquad B. 连续但不可导

C. 可导但导数不连续 \qquad D. 可导但导数连续
\end{problemblock}

\begin{solutionblock}
\analysis{这是经典振荡函数题，分别检查连续性、可导性和导函数连续性。}
连续性：
\[
|x^2\sin(1/x)|\le x^2\to0,
\]
故 \(f(x)\to f(0)=0\)，函数在 0 连续。

可导性：
\[
f'(0)=\lim_{x\to0}\frac{f(x)-f(0)}x
=\lim_{x\to0}x\sin\frac1x=0.
\]
故 \(f\) 在 0 可导。

当 \(x\ne0\) 时，
\[
f'(x)=2x\sin\frac1x-\cos\frac1x.
\]
其中 \(-\cos\frac1x\) 在 \(x\to0\) 时振荡不收敛，所以
\[
\lim_{x\to0}f'(x)
\]
不存在。故导数在 0 不连续。

\answer{C}
\examnote{\(x^2\sin(1/x)\) 是“可导但导数不连续”的标准模型。}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 设函数 \(y=f(x)\) 在点 \(x=0\) 处连续，且
\[
\lim_{x\to0}\frac{f(x)-2x}{1-\cos x}=1,
\]
则 \(f(x)\) 在点 \(x=0\) 处（\quad）

A. 不可导 \qquad B. 可导且 \(f'(0)=0\)

C. 可导且 \(f'(0)=-2\) \qquad D. 可微且 \(\left.dy\right|_{x=0}=2\,dx\)
\end{problemblock}

\begin{solutionblock}
\analysis{由已知极限得到 \(f(x)\) 在 0 附近的主部。}
因为
\[
1-\cos x\sim\frac{x^2}{2},
\]
且
\[
\frac{f(x)-2x}{1-\cos x}\to1,
\]
所以
\[
f(x)-2x\sim1-\cos x\sim\frac{x^2}{2}.
\]
因此
\[
f(x)=2x+O(x^2).
\]
由连续性和上式可得 \(f(0)=0\)。于是
\[
f'(0)=\lim_{x\to0}\frac{f(x)-f(0)}x
=\lim_{x\to0}\frac{2x+O(x^2)}x=2.
\]
一元函数在点处可导即在该点可微，因此
\[
\left.dy\right|_{x=0}=f'(0)\,dx=2\,dx.
\]

\answer{D}
\examnote{已知 \(f(x)-2x\) 是二阶小量，就能立刻读出一阶主部 \(f(x)\sim2x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 若 \(f(x)\) 在点 \(x_0\) 处的左、右导数都存在，则 \(f(x)\) 在点 \(x_0\) 处（\quad）

A. 可导 \qquad B. 连续 \qquad C. 不可导 \qquad D. 不一定连续
\end{problemblock}

\begin{solutionblock}
\analysis{单侧导数存在会推出对应单侧连续，但左右导数未必相等。}
若左导数存在，则
\[
\lim_{x\to x_0^-}\frac{f(x)-f(x_0)}{x-x_0}
\]
存在，从而
\[
f(x)-f(x_0)=(x-x_0)\cdot O(1)\to0\quad(x\to x_0^-).
\]
所以左连续。同理，右导数存在推出右连续。左右都连续，故 \(f\) 在 \(x_0\) 连续。

但左右导数存在不代表相等，例如 \(f(x)=|x|\) 在 0 处左导数为 \(-1\)，右导数为 \(1\)，不可导。因此只能推出连续。

\answer{B}
\examnote{“左右导数都存在”比“连续”强，但比“可导”弱；还差左右导数相等。}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 已知 \(f(x)\) 在 \(x=0\) 处连续，且
\[
\lim_{x\to0}\left[f(x)+e^x\right]^{1/x}=2,
\]
则 \(f'(0)\)（\quad）

A. 不存在 \qquad B. 等于 \(\ln2\) \qquad C. 等于 \(2\) \qquad D. 等于 \(\ln2-1\)
\end{problemblock}

\begin{solutionblock}
\analysis{这是 \(1^\infty\) 型极限反求函数一阶主部。}
设
\[
g(x)=f(x)+e^x.
\]
由
\[
g(x)^{1/x}\to2
\]
可知 \(g(x)\to1\)。又 \(f\) 在 0 连续，故
\[
f(0)+1=1,\qquad f(0)=0.
\]
取对数：
\[
\lim_{x\to0}\frac{\ln g(x)}x=\ln2.
\]
由于 \(g(x)\to1\)，有
\[
\ln g(x)\sim g(x)-1.
\]
所以
\[
\lim_{x\to0}\frac{g(x)-1}{x}=\ln2.
\]
而
\[
g(x)-1=f(x)+e^x-1=f(x)+x+o(x).
\]
于是
\[
\lim_{x\to0}\frac{f(x)}x+1=\ln2,
\]
故
\[
f'(0)=\ln2-1.
\]

\answer{D}
\examnote{先由极限推出底数趋于 1，再取对数，是处理 \(1^\infty\) 的固定动作。}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 设 \(f(x)\) 有连续一阶导数，\(f(0)=0\)，若当 \(x\to0\) 时，
\[
\int_0^{f(x)}f(t)\,dt
\]
与 \(4x^2\) 为等价无穷小，则 \(f'(0)\) 等于（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. \(\frac12\)
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(f'(0)=a\)，把 \(f(x)\) 与 \(f(t)\) 都用一阶主部表示。}
由于 \(f(0)=0\) 且 \(f\) 可导，
\[
f(x)=ax+o(x).
\]
同理
\[
f(t)=at+o(t).
\]
于是
\[
\int_0^{f(x)}f(t)\,dt
\sim\int_0^{ax}at\,dt
=\frac{a}{2}(ax)^2
=\frac{a^3}{2}x^2.
\]
它与 \(4x^2\) 等价，故
\[
\frac{a^3}{2}=4,\qquad a^3=8,\qquad a=2.
\]

\answer{C}
\examnote{变上限也是 \(f(x)\)，所以阶数和系数都会出现 \(a\)，最后是 \(a^3\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 函数
\[
f(x)=|x-x^2|(e^x-1)+\sin|x-2|
\]
不可导点的个数为（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. 3
\end{problemblock}

\begin{solutionblock}
\analysis{不可导主要来自绝对值尖点，但若绝对值因子被零因子抵消，也可能变得可导。}
\(|x-x^2|=|x(1-x)|\) 的尖点候选为 \(x=0,1\)。在 \(x=0\) 附近，
\[
|x-x^2|(e^x-1)\sim |x|\cdot x=x|x|,
\]
其在 0 处导数左右都为 0，故 \(x=0\) 可导。在 \(x=1\) 处，\(e^x-1\ne0\)，绝对值尖点不能被抵消，所以不可导。

\(\sin|x-2|\) 在 \(x=2\) 处不可导，因为
\[
\sin|x-2|\sim |x-2|.
\]
其他点由初等函数复合可导。因此不可导点为 \(x=1,2\)，共 2 个。

\answer{C}
\examnote{绝对值零点是候选点，但要检查外面的乘子是否把尖点阶数抹平。}
\end{solutionblock}

\begin{problemblock}
\textbf{8.}
\[
f(x)=\lim_{n\to\infty}\sqrt[n]{1+|x|^n+e^{nx}},
\]
不可导点的个数为（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. 3
\end{problemblock}

\begin{solutionblock}
\analysis{利用结论 \(\lim_{n\to\infty}(a^n+b^n+c^n)^{1/n}=\max\{a,b,c\}\)。}
这里
\[
f(x)=\max\{1,|x|,e^x\}.
\]
当 \(x<-1\) 时，\(|x|>1\) 且 \(e^x<1\)，故 \(f(x)=|x|=-x\)。
当 \(-1\le x\le0\) 时，\(f(x)=1\)。
当 \(x>0\) 时，\(e^x>1\) 且 \(e^x>x\)，故 \(f(x)=e^x\)。

因此
\[
f(x)=
\begin{cases}
-x,&x<-1,\\
1,&-1\le x\le0,\\
e^x,&x>0.
\end{cases}
\]
在 \(x=-1\) 处左右导数分别为 \(-1,0\)，不可导；在 \(x=0\) 处左右导数分别为 \(0,1\)，不可导。其余各段可导。

\answer{C}
\examnote{\(n\) 次根极限通常转化为“最大值函数”，不可导点出现在最大项切换处。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 已知 \(f(x)\) 在 \(x=0\) 处连续，且
\[
\lim_{x\to0}\frac{x^2}{f(x)}=1,
\]
则下列结论中正确的个数为（\quad）

① \(f'(0)\) 存在，且 \(f'(0)=0\)。

② \(f''(0)\) 存在，且 \(f''(0)=2\)。

③ \(f(x)\) 在 \(x=0\) 处取得极小值。

④ \(f(x)\) 在 \(x=0\) 的某邻域内连续。

A. 1 \qquad B. 2 \qquad C. 3 \qquad D. 4
\end{problemblock}

\begin{solutionblock}
\analysis{已知条件等价于 \(f(x)\sim x^2\)。它能给出函数值和一阶导数信息，但不能保证二阶导数或邻域连续。}
由 \(f(x)\sim x^2\) 且 \(f\) 在 0 连续，得
\[
f(0)=0.
\]
于是
\[
f'(0)=\lim_{x\to0}\frac{f(x)-f(0)}x
=\lim_{x\to0}\frac{f(x)}x
=\lim_{x\to0}x\cdot\frac{f(x)}{x^2}=0,
\]
故①正确。

②不一定正确。例如可令
\[
f(x)=x^2+x^3\sin\frac1{x^2}\quad(x\ne0),\qquad f(0)=0,
\]
仍有 \(f(x)\sim x^2\)，但二阶导数在 0 处不一定存在。

③正确。因为 \(f(x)\sim x^2>0\)，所以存在去心邻域使 \(f(x)>0=f(0)\)，故 0 处取得极小值。

④不一定正确。极限 \(f(x)\sim x^2\) 只保证 \(f\) 在 0 处的趋近行为，不能保证它在 0 的整个某邻域内每一点都连续。

因此正确的是①③，共 2 个。

\answer{B}
\examnote{“等价于 \(x^2\)”能推出极小值和一阶导数，但不能自动推出二阶可导。}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 设函数 \(f(x)\) 在 \((-\infty,+\infty)\) 内连续，其导函数的图形如原题图所示，则 \(f(x)\) 有（\quad）

A. 一个极小值点和两个极大值点。

B. 两个极小值点和一个极大值点。

C. 两个极小值点和两个极大值点。

D. 三个极小值点和一个极大值点。
\end{problemblock}

\begin{solutionblock}
\analysis{函数 \(f\) 的极值由导函数 \(f'(x)\) 的符号变化决定：\(f'\) 由正变负，对应极大值；由负变正，对应极小值。}
从图像读出，导函数在四个横轴交点附近的符号变化依次为：
\[
+\to-,
\qquad
-\to+,
\qquad
+\to-,
\qquad
-\to+.
\]
因此第 1 个与第 3 个变号点对应 \(f(x)\) 的极大值点，第 2 个与第 4 个变号点对应 \(f(x)\) 的极小值点。

所以 \(f(x)\) 有两个极小值点和两个极大值点。

\answer{C}
\examnote{看导函数图像时，只看 \(f'\) 在零点两侧的正负号，不要把导函数自己的高低误认为原函数极值。}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 设函数
\[
f(x)=|x^2(x+1)|
\]
的驻点个数为 \(m\)，极值点的个数为 \(n\)，则（\quad）

A. \(m=1,n=1\) \qquad B. \(m=1,n=2\) \qquad C. \(m=2,n=3\) \qquad D. \(m=3,n=2\)
\end{problemblock}

\begin{solutionblock}
\analysis{先按 \(x=-1\) 分段去绝对值，再找可导点的导数零点与极值点。}
因为 \(x^2\ge0\)，符号由 \(x+1\) 决定：
\[
f(x)=
\begin{cases}
-x^2(x+1),&x<-1,\\
x^2(x+1),&x\ge-1.
\end{cases}
\]
当 \(x<-1\) 时，
\[
f'(x)=-(3x^2+2x)=-x(3x+2),
\]
在该区间没有零点。
当 \(x>-1\) 时，
\[
f'(x)=3x^2+2x=x(3x+2),
\]
零点为
\[
x=0,\qquad x=-\frac23.
\]
二者都是可导点且导数为 0，所以驻点个数
\[
m=2.
\]

极值点方面，\(x=-1\) 处 \(f(x)\ge0\) 且 \(f(-1)=0\)，是极小值点；\(x=-\frac23\) 处导数由正变负，是极大值点；\(x=0\) 处导数由负变正，是极小值点。故极值点共有 3 个：
\[
n=3.
\]

\answer{C}
\examnote{驻点必须是可导且导数为零的点；不可导点也可能是极值点，但不是驻点。}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 函数
\[
f(x)=\int_{-\pi}^{\pi}(t-x\sin t)^2\,dt
\]
的极值点为（\quad）

A. \(x=2\) 为极小值点 \qquad B. \(x=2\) 为极大值点

C. \(x=1\) 为极小值点 \qquad D. \(x=1\) 为极大值点
\end{problemblock}

\begin{solutionblock}
\analysis{本题的积分变量是 \(t\)，\(x\) 是参数。把积分展开后，\(f(x)\) 是关于 \(x\) 的二次函数。}
展开被积函数：
\[
(t-x\sin t)^2=t^2-2xt\sin t+x^2\sin^2t.
\]
因此
\[
f(x)=\int_{-\pi}^{\pi}t^2\,dt
-2x\int_{-\pi}^{\pi}t\sin t\,dt
x^2\int_{-\pi}^{\pi}\sin^2t\,dt.
\]
其中
\[
\int_{-\pi}^{\pi}t\sin t\,dt=2\int_0^\pi t\sin t\,dt=2\pi,
\]
\[
\int_{-\pi}^{\pi}\sin^2t\,dt=\pi.
\]
所以
\[
f(x)=C-4\pi x+\pi x^2
=\pi(x-2)^2+C-4\pi,
\]
其中 \(C=\int_{-\pi}^{\pi}t^2\,dt\) 为常数。故 \(f(x)\) 在
\[
x=2
\]
处取得极小值。

\answer{A}
\examnote{定积分上下限都是常数时，被积函数中的 \(x\) 要看作参数；展开后常常变成普通函数极值题。}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 设函数 \(f(x)\) 有二阶导数，且
\[
\lim_{x\to0}\frac{f(x)-a}{\ln(1+x)}=0,
\qquad
\lim_{x\to0}\frac{f''(x)-1}{e^{x^2}-1}=2025,
\]
则（\quad）

A. \(f(0)\) 是 \(f(x)\) 的极大值。

B. \(f(0)\) 是 \(f(x)\) 的极小值。

C. \((0,f(0))\) 是曲线 \(y=f(x)\) 的拐点。

D. \(f(0)\) 不是 \(f(x)\) 的极值，\((0,f(0))\) 也不是曲线 \(y=f(x)\) 的拐点。
\end{problemblock}

\begin{solutionblock}
\analysis{第一个极限给出 \(f(0)\) 和 \(f'(0)\)，第二个极限给出 \(f''(0)\)。}
因为 \(\ln(1+x)\sim x\)，且
\[
\frac{f(x)-a}{\ln(1+x)}\to0,
\]
所以
\[
f(x)-a=o(x).
\]
于是
\[
f(0)=a,\qquad f'(0)=0.
\]
又
\[
e^{x^2}-1\sim x^2,
\]
第二个极限说明
\[
f''(x)-1=2025x^2+o(x^2),
\]
因此
\[
f''(0)=1>0.
\]
由二阶导数判别法，\(f(0)\) 是极小值。

\answer{B}
\examnote{先从 \(f(x)-a=o(x)\) 读出 \(f(0)=a,f'(0)=0\)，再用二阶导数判极值。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 设函数 \(f(x)\) 有二阶连续导数，且
\[
f(0)=0,\qquad f'(0)>0,\qquad f''(0)<0,
\]
则（\quad）

A. \(x=0\) 是 \(|f(x)|\) 的极值点，但 \((0,f(0))\) 不是曲线 \(y=|f(x)|\) 的拐点。

B. \(x=0\) 不是 \(|f(x)|\) 的极值点，但 \((0,f(0))\) 是曲线 \(y=|f(x)|\) 的拐点。

C. \(x=0\) 是 \(|f(x)|\) 的极值点，且 \((0,f(0))\) 是曲线 \(y=|f(x)|\) 的拐点。

D. \(x=0\) 不是 \(|f(x)|\) 的极值点，且 \((0,f(0))\) 不是曲线 \(y=|f(x)|\) 的拐点。
\end{problemblock}

\begin{solutionblock}
\analysis{由于 \(f(0)=0,f'(0)>0\)，函数 \(f(x)\) 在 0 附近与 \(x\) 同号。}
当 \(x<0\) 且充分接近 0 时，\(f(x)<0\)，故
\[
|f(x)|=-f(x).
\]
当 \(x>0\) 且充分接近 0 时，\(f(x)>0\)，故
\[
|f(x)|=f(x).
\]
因此 \(|f(x)|\ge0=|f(0)|\)，所以 \(x=0\) 是 \(|f(x)|\) 的极小值点。

再看凹凸性：左侧
\[
(|f|)''=(-f)''=-f''.
\]
由于 \(f''(0)<0\)，左侧附近 \(-f''(x)>0\)，曲线凹向上；右侧
\[
(|f|)''=f''(x)<0,
\]
曲线凹向下。凹凸性在 0 两侧发生变化，因此 \((0,f(0))=(0,0)\) 是曲线 \(y=|f(x)|\) 的拐点。

\answer{C}
\examnote{\(|f(x)|\) 在 \(f(x)=0\) 且 \(f'(0)\ne0\) 处形成尖点，同时也可能发生凹凸性改变。}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 设 \(f(x)\) 满足
\[
f'(0)=0,\qquad f'(x)+[f(x)]^3=x^2,
\]
则（\quad）

A. \(f(0)\) 是 \(f(x)\) 的极大值。

B. \(f(0)\) 是 \(f(x)\) 的极小值。

C. \((0,f(0))\) 是曲线 \(y=f(x)\) 的拐点。

D. \(f(0)\) 不是 \(f(x)\) 的极值，\((0,f(0))\) 也不是曲线 \(y=f(x)\) 的拐点。
\end{problemblock}

\begin{solutionblock}
\analysis{由方程逐次代入和求导，求出 \(f\) 在 0 处的低阶导数。}
令 \(x=0\)，得
\[
f'(0)+[f(0)]^3=0.
\]
又 \(f'(0)=0\)，所以
\[
f(0)=0.
\]
对
\[
f'(x)+[f(x)]^3=x^2
\]
求导：
\[
f''(x)+3[f(x)]^2f'(x)=2x.
\]
令 \(x=0\)，得
\[
f''(0)=0.
\]
再求导：
\[
f'''(x)+6f(x)[f'(x)]^2+3[f(x)]^2f''(x)=2.
\]
令 \(x=0\)，得
\[
f'''(0)=2.
\]
因此
\[
f(x)=\frac{f'''(0)}{6}x^3+o(x^3)=\frac{x^3}{3}+o(x^3).
\]
这说明 0 附近函数像三次函数一样穿过原点，不是极值点；且
\[
f''(x)=2x+o(x)
\]
在 0 两侧变号，因此 \((0,0)\) 是拐点。

\answer{C}
\examnote{当一阶、二阶导数都为 0 时，继续看三阶主部；三次主部通常对应拐点而非极值。}
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 曲线
\[
y=\frac{x^2+1}{\sqrt{x^2-1}}
\]
的渐近线条数为（\quad）

A. 1 \qquad B. 2 \qquad C. 3 \qquad D. 4
\end{problemblock}

\begin{solutionblock}
\analysis{定义域为 \(|x|>1\)，先找垂直渐近线，再看无穷远处斜渐近线。}
当 \(x\to1^+\) 或 \(x\to-1^-\) 时，\(\sqrt{x^2-1}\to0^+\)，分子趋于 2，故有两条垂直渐近线：
\[
x=1,\qquad x=-1.
\]
当 \(x\to+\infty\) 时，
\[
\frac{x^2+1}{\sqrt{x^2-1}}-x\to0,
\]
故有斜渐近线
\[
y=x.
\]
当 \(x\to-\infty\) 时，\(\sqrt{x^2-1}\sim |x|=-x\)，
\[
\frac{x^2+1}{\sqrt{x^2-1}}+x\to0,
\]
故有斜渐近线
\[
y=-x.
\]
共有 4 条渐近线。

\answer{D}
\examnote{含 \(\sqrt{x^2}\) 的无穷远判断要分 \(+\infty\) 与 \(-\infty\)，因为 \(\sqrt{x^2}=|x|\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 曲线
\[
y=\frac{x^2+x}{x^2-1}
\]
的渐近线条数为（\quad）

A. 0 \qquad B. 1 \qquad C. 2 \qquad D. 3
\end{problemblock}

\begin{solutionblock}
\analysis{先因式分解，区分可去间断点和垂直渐近线。}
\[
y=\frac{x(x+1)}{(x-1)(x+1)}=\frac{x}{x-1}\quad(x\ne\pm1).
\]
在 \(x=-1\) 处只是可去间断点，不是渐近线。在 \(x=1\) 处分母为 0 且不能约去，所以有垂直渐近线
\[
x=1.
\]
当 \(x\to\pm\infty\) 时，
\[
\frac{x^2+x}{x^2-1}\to1,
\]
故有水平渐近线
\[
y=1.
\]
共有 2 条。

\answer{C}
\examnote{分母为零不一定是垂直渐近线，能约去的点通常是可去间断点。}
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 设曲线 \(y=f(x)\) 与 \(y=x^2-x\) 在点 \((1,0)\) 处有公共切线，则
\[
\lim_{n\to\infty}n f\left(\frac{n}{n+2}\right)=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{公共切线给出 \(f(1)\) 与 \(f'(1)\)。}
曲线 \(y=x^2-x\) 在 \(x=1\) 处函数值为 0，导数为
\[
2x-1\big|_{x=1}=1.
\]
因为两曲线在 \((1,0)\) 处有公共切线，所以
\[
f(1)=0,\qquad f'(1)=1.
\]
令
\[
x_n=\frac{n}{n+2}=1-\frac{2}{n+2}.
\]
则
\[
x_n-1=-\frac{2}{n+2}.
\]
由可导性，
\[
f(x_n)=f(1)+f'(1)(x_n-1)+o(x_n-1)
=-\frac{2}{n+2}+o\left(\frac1n\right).
\]
因此
\[
n f\left(\frac{n}{n+2}\right)\to -2.
\]
\answer{\(-2\)}
\examnote{公共切线题常直接转化为函数值相同、导数相同。}
\end{solutionblock}

\section{填空题与计算题}

\begin{problemblock}
\textbf{19.} 已知
\[
f(x)=\frac{(x-1)(x-2)\cdots(x-n)}{(x+1)(x+2)\cdots(x+n)},
\]
则
\[
f'(1)=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{因为 \(x=1\) 是分子的单根，求导值只需把 \((x-1)\) 提出来。}
写成
\[
f(x)=(x-1)\cdot \frac1{x+1}\prod_{k=2}^n\frac{x-k}{x+k}.
\]
因此
\[
f'(1)=\frac12\prod_{k=2}^n\frac{1-k}{1+k}.
\]
而
\[
\prod_{k=2}^n\frac{1-k}{1+k}
=(-1)^{n-1}\frac{1\cdot2\cdots(n-1)}{3\cdot4\cdots(n+1)}
=(-1)^{n-1}\frac{2}{n(n+1)}.
\]
故
\[
f'(1)=\frac{(-1)^{n-1}}{n(n+1)}.
\]
\answer{\(\displaystyle\frac{(-1)^{n-1}}{n(n+1)}\)}
\examnote{有简单零点时，\(f'(x_0)\) 等于去掉零因子后的剩余部分在 \(x_0\) 的值。}
\end{solutionblock}

\begin{problemblock}
\textbf{20.}（数学三不要求）曲线
\[
\begin{cases}
x=\displaystyle\int_0^{1-t}e^{-u^2}\,du,\\
y=t^2\ln(2-t^2)
\end{cases}
\]
在点 \((0,0)\) 处的切线方程为 \(\underline{\qquad}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先确定对应参数，再用 \(\frac{dy}{dx}=\frac{dy/dt}{dx/dt}\)。}
点 \((0,0)\) 对应
\[
x=0\Rightarrow 1-t=0\Rightarrow t=1,
\]
且此时
\[
y=1^2\ln1=0.
\]
求导：
\[
\frac{dx}{dt}=-e^{-(1-t)^2},
\]
故
\[
\left.\frac{dx}{dt}\right|_{t=1}=-1.
\]
又
\[
\frac{dy}{dt}=2t\ln(2-t^2)+t^2\frac{-2t}{2-t^2},
\]
所以
\[
\left.\frac{dy}{dt}\right|_{t=1}=-2.
\]
因此
\[
\left.\frac{dy}{dx}\right|_{t=1}=2.
\]
切线过 \((0,0)\)，方程为
\[
y=2x.
\]
\answer{\(y=2x\)}
\examnote{参数方程切线先找参数值，不要直接消参。}
\end{solutionblock}

\begin{problemblock}
\textbf{21.}（数学三不要求）对数螺线
\[
r=e^\theta
\]
在点
\[
(r,\theta)=\left(e^{\pi/2},\frac\pi2\right)
\]
处的切线的直角坐标方程为 \(\underline{\qquad}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{极坐标曲线用 \(x=r\cos\theta,\ y=r\sin\theta\) 求斜率。}
对 \(r=e^\theta\)，有 \(r'=r\)。切线斜率公式为
\[
\frac{dy}{dx}
=\frac{r'\sin\theta+r\cos\theta}{r'\cos\theta-r\sin\theta}.
\]
在 \(\theta=\frac\pi2\) 处，
\[
\frac{dy}{dx}
=\frac{r}{-r}=-1.
\]
该点直角坐标为
\[
x=0,\qquad y=e^{\pi/2}.
\]
故切线方程为
\[
y-e^{\pi/2}=-x,
\]
即
\[
x+y=e^{\pi/2}.
\]
\answer{\(x+y=e^{\pi/2}\)}
\examnote{极坐标点要先转成直角坐标点，再写切线方程。}
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 设函数
\[
f(x)=
\begin{cases}
\ln\sqrt{x},&x\ge1,\\
2x-1,&x<1,
\end{cases}
\qquad y=f(f(x)),
\]
则
\[
\left.\frac{dy}{dx}\right|_{x=e}
=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{复合函数求导时要先判断内层函数值落在哪个分段。}
因为 \(e>1\)，
\[
f(e)=\ln\sqrt e=\frac12<1.
\]
所以外层函数在输入 \(\frac12\) 时使用分段
\[
f(u)=2u-1,\qquad f'(u)=2.
\]
内层在 \(x=e\) 处使用
\[
f(x)=\ln\sqrt{x}=\frac12\ln x,
\]
故
\[
f'(e)=\frac1{2e}.
\]
由链式法则
\[
\left.\frac{dy}{dx}\right|_{x=e}
=f'(f(e))f'(e)=2\cdot\frac1{2e}=\frac1e.
\]
\answer{\(\frac1e\)}
\examnote{分段复合函数一定要先算内层值，再决定外层用哪一段。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 设 \(y=f(x)\) 的反函数是 \(x=\varphi(y)\)，且
\[
f(x)=\int_1^{2x}e^{t^2}\,dt+1,
\]
则
\[
\varphi''(1)=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{反函数二阶导公式为 \(\varphi''(y)=-\frac{f''(x)}{[f'(x)]^3}\)，其中 \(x=\varphi(y)\)。}
先求 \(\varphi(1)\)。由
\[
f(x)=1
\]
得积分为 0，所以
\[
2x=1,\qquad x=\frac12.
\]
即
\[
\varphi(1)=\frac12.
\]
由变上限积分求导，
\[
f'(x)=2e^{(2x)^2}=2e^{4x^2},
\]
\[
f''(x)=16xe^{4x^2}.
\]
在 \(x=\frac12\) 处，
\[
f'\left(\frac12\right)=2e,\qquad
f''\left(\frac12\right)=8e.
\]
因此
\[
\varphi''(1)=
-\frac{8e}{(2e)^3}
=-\frac1{e^2}.
\]
\answer{\(-e^{-2}\)}
\examnote{反函数求导题先找对应的 \(x\)，再套公式。}
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 函数
\[
y=x\ln(1-2x)
\]
在 \(x=0\) 处的 \(n(n\ge2)\) 阶导数
\[
y^{(n)}(0)=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{用幂级数读出 \(x^n\) 的系数。}
当 \(|x|<\frac12\) 时，
\[
\ln(1-2x)=-\sum_{k=1}^{\infty}\frac{(2x)^k}{k}.
\]
因此
\[
y=x\ln(1-2x)
=-\sum_{k=1}^{\infty}\frac{2^k}{k}x^{k+1}.
\]
要取 \(x^n\) 项，令 \(k+1=n\)，即 \(k=n-1\)。故 \(x^n\) 的系数为
\[
-\frac{2^{n-1}}{n-1}.
\]
所以
\[
y^{(n)}(0)=n!\left(-\frac{2^{n-1}}{n-1}\right)
=-\frac{n!\,2^{n-1}}{n-1}.
\]
\answer{\(\displaystyle-\frac{n!\,2^{n-1}}{n-1}\)}
\examnote{高阶导数在 0 处等于 \(n!\) 乘 Taylor 展开中 \(x^n\) 的系数。}
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 设
\[
f(x)=\frac{x^2+x-1}{x^2+x-2},
\]
则
\[
f^{(n)}(x)=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先把有理函数拆成简单分式。}
因为
\[
x^2+x-1=(x^2+x-2)+1,
\]
所以
\[
f(x)=1+\frac1{x^2+x-2}
=1+\frac1{(x-1)(x+2)}.
\]
部分分式分解：
\[
\frac1{(x-1)(x+2)}
=\frac13\left(\frac1{x-1}-\frac1{x+2}\right).
\]
当 \(n\ge1\) 时，常数项导数为 0，且
\[
\frac{d^n}{dx^n}\frac1{x-a}
=(-1)^n n!(x-a)^{-n-1}.
\]
故
\[
f^{(n)}(x)=\frac{(-1)^n n!}{3}
\left[
\frac1{(x-1)^{n+1}}-\frac1{(x+2)^{n+1}}
\right].
\]
\answer{\(\displaystyle \frac{(-1)^n n!}{3}\left[\frac1{(x-1)^{n+1}}-\frac1{(x+2)^{n+1}}\right]\)}
\examnote{有理函数高阶导优先拆成 \((x-a)^{-1}\) 的线性组合。}
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 函数
\[
f(x)=\ln\bigl[(x-1)(x-2)\cdots(x-n)\bigr]
\]
的驻点个数为 \(\underline{\qquad}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{驻点满足 \(f'(x)=0\)，并且只能在函数有定义的区间内讨论。}
求导得
\[
f'(x)=\sum_{k=1}^n\frac1{x-k}.
\]
再求导：
\[
f''(x)=-\sum_{k=1}^n\frac1{(x-k)^2}<0.
\]
所以 \(f'(x)\) 在每个定义区间上严格递减。

在区间 \((k,k+1)\ (k=1,2,\cdots,n-1)\) 上，
\[
\lim_{x\to k^+}f'(x)=+\infty,\qquad
\lim_{x\to(k+1)^-}f'(x)=-\infty.
\]
由连续性和严格递减性，每个这样的区间内恰有一个零点。

在 \((-\infty,1)\) 上，各项均为负，无零点；在 \((n,+\infty)\) 上，各项均为正，也无零点。因此驻点个数为
\[
n-1.
\]
\answer{\(n-1\)}
\examnote{对数乘积求导变成倒数和；再用单调性判断零点个数。}
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 已知方程
\[
x^4+2x^3-3x^2-4x+a=0
\]
有两个重根，则
\[
a=\underline{\qquad}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{重根必为多项式与导函数的公共根。}
设
\[
P(x)=x^4+2x^3-3x^2-4x+a.
\]
则
\[
P'(x)=4x^3+6x^2-6x-4
=2(x-1)(2x+1)(x+2).
\]
因此重根只能在
\[
x=1,\quad x=-\frac12,\quad x=-2
\]
中产生。分别计算不含 \(a\) 的部分
\[
Q(x)=x^4+2x^3-3x^2-4x.
\]
有
\[
Q(1)=-4,\qquad Q(-2)=-4,
\]
所以若 \(a=4\)，则 \(x=1\) 与 \(x=-2\) 都是重根。事实上
\[
x^4+2x^3-3x^2-4x+4=(x-1)^2(x+2)^2.
\]
故
\[
a=4.
\]
\answer{4}
\examnote{“两个重根”对四次方程通常意味着可以分解成两个平方因子。}
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 已知方程
\[
3x^4-8x^3-6x^2+24x+a=0
\]
有四个不同的实根，则 \(a\) 的取值范围为 \(\underline{\qquad}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{把参数 \(a\) 看作竖直平移，先研究不含 \(a\) 的四次函数极值。}
令
\[
g(x)=3x^4-8x^3-6x^2+24x.
\]
则
\[
g'(x)=12x^3-24x^2-12x+24
=12(x+1)(x-1)(x-2).
\]
三个驻点为
\[
x=-1,\quad x=1,\quad x=2.
\]
计算函数值：
\[
g(-1)=-19,\qquad g(1)=13,\qquad g(2)=8.
\]
因为最高次系数为正，曲线从左到右依次为：下降到 \(-19\)，上升到 \(13\)，下降到 \(8\)，再上升到 \(+\infty\)。

方程
\[
g(x)+a=0
\]
有四个不同实根，等价于水平线 \(y=-a\) 同时穿过四个单调区间，必须满足
\[
8<-a<13.
\]
因此
\[
-13<a<-8.
\]
\answer{\((-13,-8)\)}
\examnote{四次方程实根个数常转化为函数图像与水平线交点个数。}
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 设 \(f(x)\) 为连续函数，
\[
\lim_{x\to0}\frac{xf(x)-\ln(1+x)}{x^2}=2,
\]
\[
F(x)=\int_0^x t f(x-t)\,dt.
\]
当 \(x\to0\) 时，\(F(x)-\frac12x^2\) 与 \(bx^k\) 为等价无穷小，其中常数 \(b\ne0\)，\(k\) 为某正整数。求 \(k,b\) 及 \(f(0),f'(0)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先由已知极限反求 \(f(x)\) 的一阶展开，再代入积分。}
由
\[
\ln(1+x)=x-\frac{x^2}{2}+o(x^2),
\]
可得
\[
xf(x)=\ln(1+x)+2x^2+o(x^2)
=x+\frac32x^2+o(x^2).
\]
因此
\[
f(x)=1+\frac32x+o(x),
\]
所以
\[
f(0)=1,\qquad f'(0)=\frac32.
\]
再看
\[
F(x)=\int_0^x t f(x-t)\,dt.
\]
当 \(x\to0\) 时，
\[
f(x-t)=1+\frac32(x-t)+o(x)
\]
在积分区间内成立。于是
\[
F(x)=\int_0^x t\,dt
+\frac32\int_0^x t(x-t)\,dt
+o(x^3).
\]
计算
\[
\int_0^x t\,dt=\frac{x^2}{2},
\]
\[
\int_0^x t(x-t)\,dt
=x\cdot\frac{x^2}{2}-\frac{x^3}{3}
=\frac{x^3}{6}.
\]
因此
\[
F(x)=\frac{x^2}{2}+\frac32\cdot\frac{x^3}{6}+o(x^3)
=\frac{x^2}{2}+\frac{x^3}{4}+o(x^3).
\]
故
\[
F(x)-\frac12x^2\sim\frac14x^3.
\]
\answer{\(k=3,\ b=\frac14,\ f(0)=1,\ f'(0)=\frac32\)}
\examnote{积分里 \(f(x-t)\) 的一阶项会贡献三阶小量，这是本题的主部来源。}
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 已知函数 \(f(u)\) 具有二阶导数，且 \(f'(0)=1\)，函数 \(y=y(x)\) 由方程
\[
y-xe^{y-1}=1
\]
所确定。设
\[
z=f(\ln y-\sin x),
\]
求
\[
\left.\frac{dz}{dx}\right|_{x=0},\qquad
\left.\frac{d^2z}{dx^2}\right|_{x=0}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先求隐函数 \(y\) 在 0 处的一、二阶导数，再处理复合函数。}
由方程在 \(x=0\) 处得
\[
y(0)=1.
\]
设
\[
y=1+ax+bx^2+o(x^2).
\]
则
\[
y-1=ax+bx^2+o(x^2),
\]
\[
e^{y-1}=1+ax+\left(b+\frac{a^2}{2}\right)x^2+o(x^2).
\]
代入
\[
y-xe^{y-1}=1
\]
得
\[
1+ax+bx^2-x(1+ax+o(x))=1.
\]
比较系数：
\[
a=1,\qquad b=a=1.
\]
所以
\[
y'(0)=1,\qquad y''(0)=2.
\]
令
\[
u(x)=\ln y-\sin x.
\]
则
\[
u(0)=0,
\]
\[
u'(0)=\frac{y'(0)}{y(0)}-\cos0=1-1=0.
\]
又
\[
u''(0)=\left.\left(\frac{y''y-(y')^2}{y^2}+\sin x\right)\right|_{x=0}
=2-1=1.
\]
因为
\[
z=f(u),
\]
所以
\[
z'(0)=f'(0)u'(0)=0,
\]
\[
z''(0)=f''(0)[u'(0)]^2+f'(0)u''(0)=1.
\]
\answer{\(\left.z'\right|_{0}=0,\quad \left.z''\right|_{0}=1\)}
\examnote{若内层函数 \(u'(0)=0\)，二阶复合求导中的 \(f''(0)[u'(0)]^2\) 项会消失。}
\end{solutionblock}

\begin{problemblock}
\textbf{31.}（数学三不要求）设 \(f(t)\) 二阶可导，且 \(f''(t)\ne0\)，
\[
\begin{cases}
y=tf'(t)-f(t),\\
x=f'(t),
\end{cases}
\]
求
\[
\frac{d^2y}{dx^2}\quad\text{及}\quad \frac{d^2x}{dy^2}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{参数方程求二阶导，先求 \(\frac{dy}{dx}\)，再对参数继续求导。}
由
\[
\frac{dx}{dt}=f''(t),
\]
\[
\frac{dy}{dt}=f'(t)+tf''(t)-f'(t)=tf''(t),
\]
得
\[
\frac{dy}{dx}=\frac{dy/dt}{dx/dt}=t.
\]
因此
\[
\frac{d^2y}{dx^2}
=\frac{d}{dx}\left(\frac{dy}{dx}\right)
=\frac{dt}{dx}
=\frac1{f''(t)}.
\]
又
\[
\frac{dx}{dy}=\frac1{dy/dx}=\frac1t.
\]
于是
\[
\frac{d^2x}{dy^2}
=\frac{d}{dy}\left(\frac1t\right)
=\frac{\frac{d}{dt}(1/t)}{dy/dt}
=\frac{-1/t^2}{tf''(t)}
=-\frac1{t^3f''(t)}.
\]
\answer{\(\displaystyle \frac{d^2y}{dx^2}=\frac1{f''(t)},\quad \frac{d^2x}{dy^2}=-\frac1{t^3f''(t)}\)}
\examnote{二阶参数导数本质是“先对 \(t\) 求导，再除以对应的一阶导”。}
\end{solutionblock}

\begin{problemblock}
\textbf{32.}（数学三不要求）设 \(y=y(x)\) 由
\[
\begin{cases}
x=t^3+2t+1,\\
t-\displaystyle\int_1^{y+t^2}e^{-u^2}\,du=0
\end{cases}
\]
确定，求
\[
\left.\frac{dy}{dx}\right|_{t=0},\qquad
\left.\frac{d^2y}{dx^2}\right|_{t=0}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先把 \(y\) 看成 \(t\) 的函数，再用参数方程求导。}
当 \(t=0\) 时，第二个方程给出
\[
\int_1^y e^{-u^2}\,du=0,
\]
故
\[
y(0)=1.
\]
对
\[
t-\int_1^{y+t^2}e^{-u^2}\,du=0
\]
求导：
\[
1-e^{-(y+t^2)^2}(y'+2t)=0,
\]
即
\[
y'+2t=e^{(y+t^2)^2}.
\]
在 \(t=0\) 处，
\[
y'(0)=e.
\]
又
\[
x'=3t^2+2,\qquad x'(0)=2.
\]
所以
\[
\left.\frac{dy}{dx}\right|_{t=0}=\frac{y'(0)}{x'(0)}=\frac e2.
\]
继续对
\[
y'+2t=e^{(y+t^2)^2}
\]
求导。令 \(s=y+t^2\)，则右侧导数为
\[
e^{s^2}\cdot2s(y'+2t).
\]
在 \(t=0\) 处，\(s=1,\ y'+2t=e\)，故
\[
y''(0)+2=2e^2,
\]
\[
y''(0)=2e^2-2.
\]
而 \(x''(0)=0\)，故
\[
\left.\frac{d^2y}{dx^2}\right|_{t=0}
=\left.\frac{y''x'-y'x''}{(x')^3}\right|_{t=0}
=\frac{(2e^2-2)\cdot2}{8}
=\frac{e^2-1}{2}.
\]
\answer{\(\displaystyle \left.\frac{dy}{dx}\right|_{t=0}=\frac e2,\quad \left.\frac{d^2y}{dx^2}\right|_{t=0}=\frac{e^2-1}{2}\)}
\examnote{隐式参数题要分清：先求 \(dy/dt\)、\(d^2y/dt^2\)，再换成对 \(x\) 的导数。}
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 设函数
\[
\varphi(x)=\int_0^{\sin x}f(tx^2)\,dt,
\]
其中 \(f(x)\) 是连续函数，且 \(f(0)=2\)。

(1) 求 \(\varphi'(x)\)；

(2) 讨论 \(\varphi'(x)\) 的连续性。
\end{problemblock}

\begin{solutionblock}
\analysis{由于只假设 \(f\) 连续，不宜直接对 \(f(tx^2)\) 求偏导。可先作变量代换。}
当 \(x\ne0\) 时，令 \(u=tx^2\)，得
\[
\varphi(x)=\frac1{x^2}\int_0^{x^2\sin x}f(u)\,du.
\]
记
\[
H(u)=\int_0^u f(s)\,ds,\qquad u=x^2\sin x.
\]
则
\[
\varphi(x)=x^{-2}H(x^2\sin x).
\]
所以当 \(x\ne0\) 时，
\[
\varphi'(x)
=-\frac2{x^3}H(x^2\sin x)
+\frac1{x^2}f(x^2\sin x)(2x\sin x+x^2\cos x).
\]
即
\[
\varphi'(x)=
-\frac{2}{x^3}\int_0^{x^2\sin x}f(u)\,du
+f(x^2\sin x)\left(\frac{2\sin x}{x}+\cos x\right).
\]
当 \(x=0\) 时，
\[
\varphi(x)=\int_0^{\sin x}f(tx^2)\,dt
\sim\int_0^{x}2\,dt=2x,
\]
故
\[
\varphi'(0)=2.
\]

连续性方面，当 \(x\to0\) 时，由 \(f\) 在 0 连续，\(H(u)\sim2u\)，且 \(x^2\sin x\sim x^3\)。代入上式可得
\[
\varphi'(x)\to -\frac2{x^3}\cdot 2x^3+2(2+1)=2.
\]
因此 \(\varphi'(x)\) 在 \(x=0\) 处连续；在 \(x\ne0\) 处由连续函数复合可知 \(\varphi'(x)\) 连续。故 \(\varphi'(x)\) 在其定义域内连续。
\answer{见上式，且 \(\varphi'(x)\) 连续。}
\examnote{只有连续性时，优先用变上限积分函数 \(H\) 规避对 \(f\) 求导。}
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 设 \(f(x)\) 连续，
\[
\varphi(x)=\int_0^1 f(xt)\,dt,
\]
且
\[
\lim_{x\to0}\frac{f(x)}x=A\quad(A\text{ 为常数}).
\]
求 \(\varphi'(x)\)，并讨论 \(\varphi'(x)\) 在 \(x=0\) 处的连续性。
\end{problemblock}

\begin{solutionblock}
\analysis{同样用变量代换，把含参积分化为变上限积分。}
由已知极限可知 \(f(0)=0\)。当 \(x\ne0\) 时，令 \(u=xt\)，
\[
\varphi(x)=\frac1x\int_0^x f(u)\,du.
\]
因此
\[
\varphi'(x)=\frac{x f(x)-\int_0^x f(u)\,du}{x^2}\qquad(x\ne0).
\]
当 \(x=0\) 时，
\[
\varphi'(0)=\lim_{x\to0}\frac{\varphi(x)-\varphi(0)}x
=\lim_{x\to0}\frac1{x^2}\int_0^x f(u)\,du.
\]
因为
\[
f(u)\sim Au,
\]
所以
\[
\int_0^x f(u)\,du\sim\frac A2x^2.
\]
故
\[
\varphi'(0)=\frac A2.
\]
再看连续性：
\[
x f(x)\sim Ax^2,\qquad
\int_0^x f(u)\,du\sim\frac A2x^2.
\]
于是
\[
\lim_{x\to0}\varphi'(x)
=\frac A2
=\varphi'(0).
\]
所以 \(\varphi'(x)\) 在 \(x=0\) 处连续。
\answer{\(\displaystyle \varphi'(x)=\frac{x f(x)-\int_0^x f(u)\,du}{x^2}(x\ne0),\ \varphi'(0)=\frac A2\)，且在 0 处连续。}
\examnote{\(\int_0^1f(xt)dt\) 是常见模型，换元后就是平均值函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{35.} 设函数由方程
\[
2y^3-2y^2+2xy-x^2=1
\]
所确定，试求 \(y=y(x)\) 的驻点，并判别它是否为极值点。
\end{problemblock}

\begin{solutionblock}
\analysis{隐函数驻点满足 \(y'=0\)。}
令
\[
F(x,y)=2y^3-2y^2+2xy-x^2-1=0.
\]
则
\[
F_x=2y-2x,\qquad
F_y=6y^2-4y+2x.
\]
由隐函数求导，
\[
y'=-\frac{F_x}{F_y}
=\frac{2x-2y}{6y^2-4y+2x}.
\]
驻点要求 \(y'=0\)，即
\[
x=y.
\]
代入原方程：
\[
2y^3-2y^2+2y^2-y^2=1,
\]
即
\[
2y^3-y^2=1.
\]
整理得
\[
2y^3-y^2-1=(y-1)(2y^2+y+1)=0.
\]
二次因子无实根，所以
\[
y=1,\qquad x=1.
\]
驻点为 \((1,1)\)。

判别极值：在 \((1,1)\) 处，
\[
F_y=4\ne0,\qquad y'=0.
\]
二阶求导公式在驻点处化为
\[
F_{xx}+F_y y''=0.
\]
由于 \(F_{xx}=-2\)，故
\[
-2+4y''=0,\qquad y''=\frac12>0.
\]
因此 \((1,1)\) 是极小值点。
\answer{驻点为 \((1,1)\)，且为极小值点。}
\examnote{隐函数驻点先令 \(F_x=0\)，再代回原方程；判别时用二阶导。}
\end{solutionblock}

\begin{problemblock}
\textbf{36.}（数学三不要求）已知曲线 \(L\) 的方程为
\[
\begin{cases}
x=t^2+1,\\
y=4t-t^2
\end{cases}
\quad(t\ge0).
\]
(1) 讨论 \(L\) 的凹凸性；

(2) 过点 \((-1,0)\) 引 \(L\) 的切线，求切点 \((x_0,y_0)\)，并写出切线方程；

(3) 求此切线与 \(L\)（对应于 \(x\le x_0\) 的部分）及 \(x\) 轴所围成的平面图形的面积。
\end{problemblock}

\begin{solutionblock}
\analysis{先用参数方程求斜率和凹凸，再由“切线过定点”确定参数。}
(1) 有
\[
\frac{dx}{dt}=2t,\qquad \frac{dy}{dt}=4-2t.
\]
当 \(t>0\) 时，
\[
\frac{dy}{dx}=\frac{4-2t}{2t}=\frac2t-1.
\]
所以
\[
\frac{d^2y}{dx^2}
=\frac{d}{dt}\left(\frac2t-1\right)\bigg/\frac{dx}{dt}
=\frac{-2/t^2}{2t}
=-\frac1{t^3}<0.
\]
故曲线凹向下。

(2) 参数为 \(t\) 的点为
\[
(x,y)=(t^2+1,\,4t-t^2),
\]
切线斜率为
\[
m=\frac2t-1.
\]
若切线过 \((-1,0)\)，则
\[
\frac{4t-t^2}{t^2+1-(-1)}
=\frac{4t-t^2}{t^2+2}
=\frac2t-1.
\]
解得
\[
t=1\quad(t\ge0).
\]
故切点
\[
(x_0,y_0)=(2,3),
\]
斜率
\[
m=1.
\]
切线方程为
\[
y=x+1.
\]

(3) 所求面积等于直线 \(y=x+1\) 在 \([-1,2]\) 上方与 \(x\) 轴围成的三角形面积，减去曲线 \(L\) 在 \(t\in[0,1]\) 下方的面积：
\[
S=\int_{-1}^{2}(x+1)\,dx-\int_{0}^{1}y(t)x'(t)\,dt.
\]
第一项
\[
\int_{-1}^{2}(x+1)\,dx=\frac92.
\]
第二项
\[
\int_0^1(4t-t^2)\cdot2t\,dt
=\int_0^1(8t^2-2t^3)\,dt
=\frac83-\frac12=\frac{13}{6}.
\]
因此
\[
S=\frac92-\frac{13}{6}
=\frac{7}{3}.
\]
\answer{(1) 凹向下；(2) 切点 \((2,3)\)，切线 \(y=x+1\)；(3) 面积 \(\frac73\)。}
\examnote{参数曲线面积常用 \(\int y\,dx=\int y(t)x'(t)\,dt\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 试确定方程
\[
x^3-x=\sin x
\]
的实根个数。
\end{problemblock}

\begin{solutionblock}
\analysis{方程两边移项，利用奇偶性和导数研究正半轴。}
令
\[
F(x)=x^3-x-\sin x.
\]
则 \(F(x)\) 是奇函数，且
\[
F(0)=0.
\]
只需研究 \(x>0\)。有
\[
F'(x)=3x^2-1-\cos x,
\]
\[
F''(x)=6x+\sin x>0\qquad(x>0).
\]
所以 \(F'(x)\) 在 \((0,+\infty)\) 上严格递增。又
\[
F'(0)=-2,\qquad F'(x)\to+\infty,
\]
故 \(F'\) 在正半轴只有一个零点，\(F\) 先减后增。

当 \(x\to0^+\) 时，\(F(x)<0\)；当 \(x\to+\infty\) 时，\(F(x)\to+\infty\)。因此 \(F(x)=0\) 在 \((0,+\infty)\) 上恰有一个根。由奇函数对称性，在 \((-\infty,0)\) 上也恰有一个根，再加上 \(x=0\)，共有 3 个实根。
\answer{3 个}
\examnote{奇函数方程常先找 \(0\) 根，再研究正半轴。}
\end{solutionblock}

\begin{problemblock}
\textbf{38.} 试确定方程
\[
\int_0^x e^{-t^2}\,dt=x^3-x
\]
的实根个数。
\end{problemblock}

\begin{solutionblock}
\analysis{移项后仍是奇函数，研究正半轴即可。}
令
\[
F(x)=\int_0^x e^{-t^2}\,dt-x^3+x.
\]
则 \(F\) 为奇函数，且 \(F(0)=0\)。对 \(x>0\)，
\[
F'(x)=e^{-x^2}-3x^2+1,
\]
\[
F''(x)=-2xe^{-x^2}-6x<0.
\]
所以 \(F'(x)\) 在 \((0,+\infty)\) 上严格递减。又
\[
F'(0)=2,\qquad F'(x)\to-\infty,
\]
故 \(F'\) 在正半轴仅有一个零点，\(F\) 先增后减。

当 \(x\to0^+\) 时，\(F(x)>0\)；当 \(x\to+\infty\) 时，\(F(x)\to-\infty\)。所以正半轴上恰有一个零点。由奇函数对称性，负半轴上也恰有一个零点，再加 \(x=0\)，共有 3 个实根。
\answer{3 个}
\examnote{“导数单调”能控制函数最多穿过几次横轴。}
\end{solutionblock}

\begin{problemblock}
\textbf{39.} 试确定方程
\[
e^x=ax^2\quad(a>0)
\]
的实根个数。
\end{problemblock}

\begin{solutionblock}
\analysis{把参数写成函数值：\(a=\frac{e^x}{x^2}\)，注意 \(x=0\) 不可能是根。}
令
\[
\phi(x)=\frac{e^x}{x^2}\qquad(x\ne0).
\]
则方程等价于
\[
a=\phi(x).
\]
在 \(x<0\) 上，
\[
\frac{\phi'(x)}{\phi(x)}=1-\frac2x>0,
\]
所以 \(\phi\) 严格递增，且
\[
\phi(x)\to0\ (x\to-\infty),\qquad \phi(x)\to+\infty\ (x\to0^-).
\]
故负半轴上对任意 \(a>0\) 都有一个根。

在 \(x>0\) 上，\(\phi\) 在 \(x=2\) 处取得最小值
\[
\phi(2)=\frac{e^2}{4}.
\]
因此正半轴上：
若 \(0<a<\frac{e^2}{4}\)，无根；若 \(a=\frac{e^2}{4}\)，有一个根；若 \(a>\frac{e^2}{4}\)，有两个根。

综上：
\[
\begin{cases}
0<a<\frac{e^2}{4},&1\text{ 个实根},\\
a=\frac{e^2}{4},&2\text{ 个实根},\\
a>\frac{e^2}{4},&3\text{ 个实根}.
\end{cases}
\]
\answer{见上分段结论}
\examnote{含参数根个数题，常转化为参数等于某函数值，再研究该函数值域。}
\end{solutionblock}

\begin{problemblock}
\textbf{40.} 试确定方程
\[
\ln x=kx
\]
的实根个数。
\end{problemblock}

\begin{solutionblock}
\analysis{定义域为 \(x>0\)，化为 \(\frac{\ln x}{x}=k\)。}
令
\[
\phi(x)=\frac{\ln x}{x}\quad(x>0).
\]
则
\[
\phi'(x)=\frac{1-\ln x}{x^2}.
\]
所以 \(\phi\) 在 \((0,e)\) 上递增，在 \((e,+\infty)\) 上递减，最大值为
\[
\phi(e)=\frac1e.
\]
并且
\[
\phi(x)\to-\infty\quad(x\to0^+),\qquad
\phi(x)\to0^+\quad(x\to+\infty).
\]
因此：
\[
\begin{cases}
k>\frac1e,&0\text{ 个实根},\\
k=\frac1e,&1\text{ 个实根},\\
0<k<\frac1e,&2\text{ 个实根},\\
k=0,&1\text{ 个实根},\\
k<0,&1\text{ 个实根}.
\end{cases}
\]
\answer{见上分段结论}
\examnote{\(\ln x=kx\) 是经典模型，关键函数是 \(\ln x/x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{41.} 试证：当 \(x\ge0\) 时，
\[
x\le e^x\ln(1+x).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{构造差函数并证明单调递增。}
令
\[
F(x)=e^x\ln(1+x)-x.
\]
则
\[
F(0)=0.
\]
求导：
\[
F'(x)=e^x\ln(1+x)+\frac{e^x}{1+x}-1.
\]
当 \(x\ge0\) 时，
\[
e^x\ge1+x,
\]
故
\[
\frac{e^x}{1+x}\ge1.
\]
又 \(e^x\ln(1+x)\ge0\)，所以
\[
F'(x)\ge0.
\]
因此 \(F(x)\ge F(0)=0\)，即
\[
x\le e^x\ln(1+x).
\]
\examnote{证明不等式时，若右边含指数与对数，构造差函数后常用基本不等式 \(e^x\ge1+x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 设 \(x>0\)，证明：
\[
2\sin x+e^x-e^{-x}>4x.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把不等式化为函数正性，用二阶导控制单调性。}
令
\[
F(x)=\sin x+\sinh x-2x.
\]
原不等式等价于
\[
2F(x)>0.
\]
有
\[
F(0)=0,\qquad F'(0)=\cos0+\cosh0-2=0.
\]
再求二阶导：
\[
F''(x)=-\sin x+\sinh x.
\]
当 \(x>0\) 时，\(\sinh x>x\)，且 \(\sin x\le x\)，所以
\[
F''(x)>0.
\]
于是 \(F'(x)>F'(0)=0\)，进而
\[
F(x)>F(0)=0.
\]
故
\[
2\sin x+e^x-e^{-x}>4x.
\]
\examnote{若一阶导在 0 处也为 0，可继续看二阶导的符号。}
\end{solutionblock}

\begin{problemblock}
\textbf{43.} 设 \(x>0\)，常数 \(a>e\)。证明：
\[
(a+x)^a<a^{a+x}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{两边取对数，将幂不等式化为对数不等式。}
原不等式等价于
\[
a\ln(a+x)<(a+x)\ln a.
\]
两边除以 \(a>0\)，令 \(t=\frac{x}{a}>0\)，得
\[
\ln a+\ln(1+t)<(1+t)\ln a,
\]
即
\[
\ln(1+t)<t\ln a.
\]
由于
\[
\ln(1+t)<t\qquad(t>0),
\]
且 \(a>e\Rightarrow \ln a>1\)，所以
\[
\ln(1+t)<t<t\ln a.
\]
结论成立。
\examnote{幂不等式优先取对数；出现 \(a+x\) 时，令 \(t=x/a\) 可简化结构。}
\end{solutionblock}

\begin{problemblock}
\textbf{44.} 设 \(e<a<b\)，证明：
\[
a^2<ab\frac{\ln a}{\ln b}<b^2.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{拆成左右两个不等式，分别转化为单调函数。}
左边不等式
\[
a^2<ab\frac{\ln a}{\ln b}
\]
等价于
\[
a\ln b<b\ln a,
\]
即
\[
\frac{\ln b}{b}<\frac{\ln a}{a}.
\]
函数
\[
\phi(x)=\frac{\ln x}{x}
\]
在 \(x>e\) 上单调递减。由于 \(e<a<b\)，故
\[
\frac{\ln a}{a}>\frac{\ln b}{b},
\]
左边不等式成立。

右边不等式
\[
ab\frac{\ln a}{\ln b}<b^2
\]
等价于
\[
a\ln a<b\ln b.
\]
函数
\[
\psi(x)=x\ln x
\]
在 \(x>e\) 上单调递增，因此
\[
a\ln a<b\ln b.
\]
右边不等式成立。故原不等式成立。
\examnote{同一个双边不等式两侧可能对应不同的单调函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{45.} 设 \(f(x)\) 和 \(g(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内可导，
\[
f(0)=f(1)=-1,\qquad \int_0^1 f(x)\,dx>\frac12.
\]
试证至少存在一点 \(\xi\in(0,1)\)，使
\[
f'(\xi)+g'(\xi)[f(\xi)-\xi]=1.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{目标式可看成某个辅助函数导数为 0。注意
\[
\frac{d}{dx}\left(e^{g(x)}(f(x)-x)\right)
=e^{g(x)}\{f'(x)-1+g'(x)[f(x)-x]\}.
\]
}
令
\[
H(x)=e^{g(x)}(f(x)-x).
\]
若能证明 \(H\) 在 \((0,1)\) 内有极值点，则由费马定理 \(H'(\xi)=0\)，即
\[
f'(\xi)+g'(\xi)[f(\xi)-\xi]=1.
\]
下面证明内点极值存在。由
\[
\int_0^1 f(x)\,dx>\frac12
\]
得
\[
\int_0^1 [f(x)-x]\,dx>0.
\]
因此存在 \(c\in(0,1)\)，使
\[
f(c)-c>0.
\]
于是
\[
H(c)>0.
\]
而
\[
H(0)=e^{g(0)}(f(0)-0)=-e^{g(0)}<0,
\]
\[
H(1)=e^{g(1)}(f(1)-1)=-2e^{g(1)}<0.
\]
所以连续函数 \(H\) 在 \([0,1]\) 上的最大值必在某个内点 \(\xi\in(0,1)\) 取得。由费马定理，
\[
H'(\xi)=0.
\]
即
\[
e^{g(\xi)}\{f'(\xi)-1+g'(\xi)[f(\xi)-\xi]\}=0.
\]
由于 \(e^{g(\xi)}>0\)，故
\[
f'(\xi)+g'(\xi)[f(\xi)-\xi]=1.
\]
\examnote{看到 \(f'+g'(f-x)\) 时，尝试构造 \(e^g(f-x)\)；这是“配导数”的典型技巧。}
\end{solutionblock}

\begin{problemblock}
\textbf{46.} 设 \(f(x),g(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内可导，且
\[
\int_0^1 f(x)\,dx=3\int_{2/3}^1 f(x)\,dx.
\]
试证存在 \(\xi,\eta\in(0,1)\)，使
\[
f'(\xi)=g'(\xi)[f(\eta)-f(\xi)].
\]
\end{problemblock}

\begin{solutionblock}
\analysis{题干中 \(g\) 没有额外条件，因此关键不是研究 \(g\)，而是先由积分条件推出存在一点 \(f'(\xi)=0\)。原题没有要求 \(\xi,\eta\) 不同，于是可取 \(\eta=\xi\)。}
由题设
\[
\int_0^1 f(x)\,dx
=\int_0^{2/3}f(x)\,dx+\int_{2/3}^1f(x)\,dx
=3\int_{2/3}^1f(x)\,dx,
\]
得
\[
\int_0^{2/3}f(x)\,dx=2\int_{2/3}^1f(x)\,dx.
\]
于是
\[
\frac{1}{2/3}\int_0^{2/3}f(x)\,dx
=3\int_{2/3}^1f(x)\,dx
=\frac{1}{1/3}\int_{2/3}^1f(x)\,dx.
\]
由积分中值定理，存在
\[
u\in\left(0,\frac23\right),\qquad v\in\left(\frac23,1\right),
\]
使
\[
f(u)=\frac{1}{2/3}\int_0^{2/3}f(x)\,dx,\qquad
f(v)=\frac{1}{1/3}\int_{2/3}^1f(x)\,dx.
\]
因此
\[
f(u)=f(v).
\]
函数 \(f\) 在 \([u,v]\) 上连续、在 \((u,v)\) 内可导，由罗尔定理，存在
\[
\xi\in(u,v)\subset(0,1)
\]
使
\[
f'(\xi)=0.
\]
取
\[
\eta=\xi.
\]
则
\[
g'(\xi)[f(\eta)-f(\xi)]
=g'(\xi)[f(\xi)-f(\xi)]
=0=f'(\xi).
\]
故结论成立。
\examnote{遇到“只有 \(f\) 的条件却含 \(g'\)”时，要检查题目是否允许取 \(\eta=\xi\)。若允许，先造出 \(f'=0\) 往往即可。}
\end{solutionblock}

\begin{problemblock}
\textbf{47.} 设 \(f(x)\) 在 \([-2,2]\) 上二阶可导，且 \(|f(x)|\le 1\)，又
\[
[f(0)]^2+[f'(0)]^2=4.
\]
证明在 \((-2,2)\) 内至少存在一点 \(\xi\)，使
\[
f''(\xi)+f(\xi)=0.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{反证法。把 \(f''+f\) 看成“受迫项”，构造
\[
F(x)=f'(x)\cos x+f(x)\sin x,
\]
则 \(F'(x)=[f''(x)+f(x)]\cos x\)。在 \((-\pi/2,\pi/2)\) 内 \(\cos x>0\)，可得到单调性。}
由于 \(|f(0)|\le 1\)，而
\[
[f(0)]^2+[f'(0)]^2=4,
\]
故
\[
|f'(0)|=\sqrt{4-[f(0)]^2}\ge \sqrt3>1.
\]
反设对任意 \(x\in(-2,2)\)，均有
\[
f''(x)+f(x)\ne 0.
\]
导函数具有介值性，所以 \(f''+f\) 在区间内不能由正跳到负，否则中间会取零。因此 \(f''+f\) 在 \((-2,2)\) 内同号。

令
\[
F(x)=f'(x)\cos x+f(x)\sin x.
\]
则
\[
F'(x)=[f''(x)+f(x)]\cos x.
\]
注意
\[
\left[-\frac{\pi}{2},\frac{\pi}{2}\right]\subset(-2,2),\qquad \cos x>0\quad\left(|x|<\frac{\pi}{2}\right).
\]
若 \(f''+f>0\)，则 \(F\) 在 \((-\pi/2,\pi/2)\) 上严格递增。
当 \(f'(0)>1\) 时，
\[
F\left(\frac{\pi}{2}\right)>F(0)=f'(0)>1,
\]
但
\[
F\left(\frac{\pi}{2}\right)=f\left(\frac{\pi}{2}\right),
\]
与 \(|f|\le1\) 矛盾。
当 \(f'(0)<-1\) 时，
\[
F\left(-\frac{\pi}{2}\right)<F(0)=f'(0)<-1,
\]
而
\[
F\left(-\frac{\pi}{2}\right)=-f\left(-\frac{\pi}{2}\right),
\]
也与 \(|f|\le1\) 矛盾。

若 \(f''+f<0\)，则 \(F\) 在 \((-\pi/2,\pi/2)\) 上严格递减。类似地：
当 \(f'(0)>1\) 时，
\[
F\left(-\frac{\pi}{2}\right)>F(0)=f'(0)>1,
\]
与 \(|f|\le1\) 矛盾；当 \(f'(0)<-1\) 时，
\[
F\left(\frac{\pi}{2}\right)<F(0)=f'(0)<-1,
\]
也与 \(|f|\le1\) 矛盾。

所有情形均矛盾，故必存在 \(\xi\in(-2,2)\)，使
\[
f''(\xi)+f(\xi)=0.
\]
\examnote{本题核心是把二阶表达式 \(f''+f\) 配成一阶函数的导数；\(\sin,\cos\) 辅助函数是处理 \(f''+f\) 的常用模板。}
\end{solutionblock}

\begin{problemblock}
\textbf{48.} 设函数 \(f(x)\) 在闭区间 \([a,b]\) 上连续，在开区间 \((a,b)\) 内可导，且 \(f'(x)>0\)。若极限
\[
\lim_{x\to a^+}\frac{f(2x-a)}{x-a}
\]
存在，证明：
\begin{enumerate}
\item 在 \((a,b)\) 内 \(f(x)>0\)；
\item 在 \((a,b)\) 内存在点 \(\xi\)，使
\[
\frac{b^2-a^2}{\int_a^b f(x)\,dx}=\frac{2\xi}{f(\xi)};
\]
\item 在 \((a,b)\) 内存在与 \((2)\) 中 \(\xi\) 相异的点 \(\eta\)，使
\[
f'(\eta)(b^2-a^2)=\frac{2\xi}{\xi-a}\int_a^b f(x)\,dx.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{先由极限存在推出 \(f(a)=0\)，再用 \(f'>0\) 得正性。后两问分别是柯西中值定理和拉格朗日中值定理。}
\textbf{(1)} 因为 \(f\) 在 \(a\) 处右连续，故
\[
\lim_{x\to a^+}f(2x-a)=f(a).
\]
若 \(f(a)\ne0\)，则
\[
\frac{f(2x-a)}{x-a}
\]
在 \(x\to a^+\) 时分母趋于 \(0^+\)，分子趋于非零常数，极限不可能为有限值。题设说极限存在，故
\[
f(a)=0.
\]
又 \(f'(x)>0\)，所以 \(f\) 在 \([a,b]\) 上严格递增，从而对任意 \(x\in(a,b)\)，有
\[
f(x)>f(a)=0.
\]

\textbf{(2)} 令
\[
F(x)=x^2,\qquad G(x)=\int_a^x f(t)\,dt.
\]
则 \(F,G\) 在 \([a,b]\) 上连续、在 \((a,b)\) 内可导，且
\[
G'(x)=f(x)>0\quad(a<x<b).
\]
由柯西中值定理，存在 \(\xi\in(a,b)\)，使
\[
\frac{F(b)-F(a)}{G(b)-G(a)}=\frac{F'(\xi)}{G'(\xi)}.
\]
即
\[
\frac{b^2-a^2}{\int_a^b f(x)\,dx}
=\frac{2\xi}{f(\xi)}.
\]

\textbf{(3)} 由 \(f(a)=0\)，对区间 \([a,\xi]\) 应用拉格朗日中值定理，存在
\[
\eta\in(a,\xi)
\]
使
\[
f'(\eta)=\frac{f(\xi)-f(a)}{\xi-a}=\frac{f(\xi)}{\xi-a}.
\]
由第 (2) 问
\[
\frac{b^2-a^2}{\int_a^b f(x)\,dx}=\frac{2\xi}{f(\xi)}
\]
可得
\[
\frac{f(\xi)}{\xi-a}(b^2-a^2)
=\frac{2\xi}{\xi-a}\int_a^b f(x)\,dx.
\]
因此
\[
f'(\eta)(b^2-a^2)=\frac{2\xi}{\xi-a}\int_a^b f(x)\,dx.
\]
且 \(\eta\in(a,\xi)\)，所以 \(\eta\ne\xi\)。
\examnote{“极限存在 + 分母趋零”常用于推出端点函数值为零；含两个增量比的结论优先考虑柯西中值定理。}
\end{solutionblock}

\begin{problemblock}
\textbf{49.} 设 \(f(x),g(x)\) 在 \([a,b]\) 上连续，在 \((a,b)\) 内可导，且
\[
g(a)=g(b)=1,\qquad f'(x)\ne0.
\]
试证存在 \(\xi,\eta\in(a,b)\)，使得
\[
\frac{f'(\xi)}{f'(\eta)}
=e^{\xi-\eta}\bigl[g(\xi)+g'(\xi)\bigr].
\]
\end{problemblock}

\begin{solutionblock}
\analysis{目标式中出现 \(e^\xi[g(\xi)+g'(\xi)]\)，这是 \((e^xg(x))'\)。再用一次 \(e^x\) 与 \(f(x)\) 的柯西中值定理，把端点差相同的两个比值连接起来。}
由于 \(f'(x)\ne0\)，由导函数介值性可知 \(f'(x)\) 在 \((a,b)\) 内同号，因此 \(f\) 严格单调，
\[
f(b)-f(a)\ne0.
\]
令
\[
H(x)=e^xg(x).
\]
由 \(g(a)=g(b)=1\)，得
\[
H(b)-H(a)=e^bg(b)-e^ag(a)=e^b-e^a.
\]
对 \(H(x)\) 与 \(f(x)\) 在 \([a,b]\) 上应用柯西中值定理，存在 \(\xi\in(a,b)\)，使
\[
\frac{H(b)-H(a)}{f(b)-f(a)}
=\frac{H'(\xi)}{f'(\xi)}
=\frac{e^\xi[g(\xi)+g'(\xi)]}{f'(\xi)}.
\]
对 \(e^x\) 与 \(f(x)\) 在 \([a,b]\) 上应用柯西中值定理，存在 \(\eta\in(a,b)\)，使
\[
\frac{e^b-e^a}{f(b)-f(a)}
=\frac{e^\eta}{f'(\eta)}.
\]
由于 \(H(b)-H(a)=e^b-e^a\)，两式左端相等，所以
\[
\frac{e^\xi[g(\xi)+g'(\xi)]}{f'(\xi)}
=\frac{e^\eta}{f'(\eta)}.
\]
整理得
\[
\frac{f'(\xi)}{f'(\eta)}
=e^{\xi-\eta}[g(\xi)+g'(\xi)].
\]
\examnote{含 \(g+g'\) 且旁边有指数 \(e^x\) 时，第一反应应是 \((e^xg)'\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{50.} 设函数 \(f(x)\) 在闭区间 \([0,1]\) 上连续，在开区间 \((0,1)\) 内可导，且
\[
f(0)=0,\qquad f(1)=\frac13.
\]
证明：存在
\[
\xi\in\left(0,\frac12\right),\qquad
\eta\in\left(\frac12,1\right),
\]
使得
\[
f'(\xi)+f'(\eta)=\xi^2+\eta^2.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把右边的 \(\xi^2+\eta^2\) 移到左边，构造 \(F(x)=f(x)-x^3/3\)，使目标变为 \(F'(\xi)+F'(\eta)=0\)。}
令
\[
F(x)=f(x)-\frac{x^3}{3}.
\]
则
\[
F(0)=0,\qquad F(1)=f(1)-\frac13=0.
\]
在区间 \([0,1/2]\) 上应用拉格朗日中值定理，存在
\[
\xi\in\left(0,\frac12\right)
\]
使
\[
F'(\xi)=\frac{F(1/2)-F(0)}{1/2-0}=2F\left(\frac12\right).
\]
在区间 \([1/2,1]\) 上应用拉格朗日中值定理，存在
\[
\eta\in\left(\frac12,1\right)
\]
使
\[
F'(\eta)=\frac{F(1)-F(1/2)}{1-1/2}=-2F\left(\frac12\right).
\]
两式相加得
\[
F'(\xi)+F'(\eta)=0.
\]
而
\[
F'(x)=f'(x)-x^2,
\]
故
\[
f'(\xi)-\xi^2+f'(\eta)-\eta^2=0.
\]
即
\[
f'(\xi)+f'(\eta)=\xi^2+\eta^2.
\]
\examnote{出现 \(x^2\) 作为导数项时，常逆向构造 \(x^3/3\)。左右两个半区间分别用中值定理，是制造“两点导数和”的常用手法。}
\end{solutionblock}

\begin{problemblock}
\textbf{51.} 设 \(f(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内可导，且
\[
f(0)=f(1).
\]
试证存在 \(\xi,\eta\)，满足
\[
0<\xi<\eta<1,
\]
使
\[
f'(\xi)+f'(\eta)=0.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把区间从中点拆开，两段分别使用拉格朗日中值定理，两个平均斜率正好互为相反数。}
在 \([0,1/2]\) 上应用拉格朗日中值定理，存在
\[
\xi\in\left(0,\frac12\right)
\]
使
\[
f'(\xi)=\frac{f(1/2)-f(0)}{1/2-0}=2\left[f\left(\frac12\right)-f(0)\right].
\]
在 \([1/2,1]\) 上应用拉格朗日中值定理，存在
\[
\eta\in\left(\frac12,1\right)
\]
使
\[
f'(\eta)=\frac{f(1)-f(1/2)}{1-1/2}
=2\left[f(1)-f\left(\frac12\right)\right].
\]
由 \(f(1)=f(0)\)，得
\[
f'(\eta)=2\left[f(0)-f\left(\frac12\right)\right]
=-2\left[f\left(\frac12\right)-f(0)\right].
\]
因此
\[
f'(\xi)+f'(\eta)=0.
\]
又
\[
0<\xi<\frac12<\eta<1,
\]
所以 \(0<\xi<\eta<1\)。
\examnote{两点结论常通过“分段中值定理”获得；中点不是唯一选择，但中点让系数最整齐。}
\end{solutionblock}

\begin{problemblock}
\textbf{52.} 设 \(f(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内可导，且
\[
f(0)=0,\qquad f(1)=0.
\]
若 \(f(x)\) 在 \([0,1]\) 上的最大值为 \(M>0\)，证明存在两个不同的点 \(x_1,x_2\in(0,1)\)，使得
\[
\frac{1}{f'(x_1)}-\frac{1}{f'(x_2)}=\frac{n}{M},
\]
其中 \(n\) 是大于 \(1\) 的整数。
\end{problemblock}

\begin{solutionblock}
\analysis{最大值点左右两侧分别存在正斜率和负斜率。再利用导数的介值性，选出一正一负且大小恰为 \(2M/n\) 的导数值。}
设 \(c\in(0,1)\) 使
\[
f(c)=M.
\]
因为端点值为 \(0\)，且最大值 \(M>0\)，最大值点必在开区间内。由费马定理，
\[
f'(c)=0.
\]
对 \([0,c]\) 应用拉格朗日中值定理，存在 \(u\in(0,c)\)，使
\[
f'(u)=\frac{f(c)-f(0)}{c-0}=\frac{M}{c}\ge M.
\]
因为 \(n>1\) 是整数，所以 \(n\ge2\)，从而
\[
0<\frac{2M}{n}\le M\le f'(u).
\]
导函数具有介值性，且 \(f'(c)=0\)，故在 \((u,c)\) 内存在 \(x_1\)，使
\[
f'(x_1)=\frac{2M}{n}.
\]

同理，对 \([c,1]\) 应用拉格朗日中值定理，存在 \(v\in(c,1)\)，使
\[
f'(v)=\frac{f(1)-f(c)}{1-c}=-\frac{M}{1-c}\le -M.
\]
由于
\[
-M\le-\frac{2M}{n}<0,
\]
并且 \(f'(c)=0,\ f'(v)\le -M\)，由导数介值性，存在 \(x_2\in(c,v)\)，使
\[
f'(x_2)=-\frac{2M}{n}.
\]
于是 \(x_1\ne x_2\)，且
\[
\frac{1}{f'(x_1)}-\frac{1}{f'(x_2)}
=\frac{1}{2M/n}-\frac{1}{-2M/n}
=\frac{n}{2M}+\frac{n}{2M}
=\frac{n}{M}.
\]
\examnote{本题不能只用一次中值定理，还要用导数介值性。导数即使不连续，也一定有介值性，这是考研证明题的高频工具。}
\end{solutionblock}

\begin{problemblock}
\textbf{53.} 设 \(f(x)\) 在 \([0,1]\) 上二阶可导，
\[
f(0)=f(1)=0,\qquad \max_{0\le x\le1}f(x)=2.
\]
试证存在 \(\xi\in(0,1)\)，使得
\[
f''(\xi)\le -16.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{取最大值点 \(c\)，由 \(f(c)=2\) 和 \(f'(c)=0\)，向距离较近的端点作二阶泰勒展开。距离不超过 \(1/2\)，于是二阶导数至少要小到 \(-16\)。}
设 \(c\in(0,1)\) 使
\[
f(c)=2.
\]
由于端点 \(f(0)=f(1)=0\)，最大值点 \(c\) 在开区间内，故
\[
f'(c)=0.
\]
若 \(c\le 1/2\)，对 \(f(x)\) 在点 \(c\) 到点 \(0\) 之间使用泰勒公式的拉格朗日余项，存在
\[
\xi\in(0,c)
\]
使
\[
f(0)=f(c)+f'(c)(0-c)+\frac12 f''(\xi)(0-c)^2.
\]
代入 \(f(0)=0,\ f(c)=2,\ f'(c)=0\)，得
\[
0=2+\frac12 f''(\xi)c^2,
\]
所以
\[
f''(\xi)=-\frac{4}{c^2}.
\]
又 \(c\le1/2\)，故
\[
f''(\xi)=-\frac{4}{c^2}\le -16.
\]

若 \(c>1/2\)，对 \(f(x)\) 在点 \(c\) 到点 \(1\) 之间使用泰勒公式，存在
\[
\xi\in(c,1)
\]
使
\[
f(1)=f(c)+f'(c)(1-c)+\frac12 f''(\xi)(1-c)^2.
\]
同理
\[
0=2+\frac12 f''(\xi)(1-c)^2,
\]
即
\[
f''(\xi)=-\frac{4}{(1-c)^2}.
\]
因为 \(c>1/2\)，所以 \(1-c<1/2\)，从而
\[
f''(\xi)<-16.
\]
综上，必存在 \(\xi\in(0,1)\)，使
\[
f''(\xi)\le -16.
\]
\examnote{最大值为 2 而端点为 0，函数必须“弯下来”。常数 16 来自最近端点距离不超过 \(1/2\)：\(4/(1/2)^2=16\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{54.} 设 \(f(x)\) 在 \([0,2]\) 上二阶可导，且
\[
|f(x)|\le1,\qquad |f''(x)|\le1.
\]
证明：
\[
|f'(x)|\le2\qquad(0\le x\le2).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{反证。若某点导数大于 2，则由于二阶导数绝对值不超过 1，整个区间上的导数都保持较大的同向趋势，积分后会迫使函数值振幅超过 2，与 \(|f|\le1\) 矛盾。}
任取 \(x_0\in[0,2]\)，记
\[
p=f'(x_0).
\]
先证 \(p\le2\)。若 \(p>2\)，由 \(|f''(x)|\le1\)，对任意 \(t\in[0,2]\)，有
\[
f'(t)\ge p-|t-x_0|.
\]
于是
\[
f(2)-f(0)=\int_0^2 f'(t)\,dt
\ge \int_0^2 \bigl(p-|t-x_0|\bigr)\,dt.
\]
计算右端：
\[
\int_0^2 |t-x_0|\,dt
=\frac{x_0^2}{2}+\frac{(2-x_0)^2}{2}\le2.
\]
故
\[
f(2)-f(0)\ge 2p-2>2.
\]
但由 \(|f(x)|\le1\)，有
\[
f(2)-f(0)\le |f(2)|+|f(0)|\le2,
\]
矛盾。因此
\[
f'(x_0)\le2.
\]

再证 \(p\ge-2\)。若 \(p<-2\)，同理对任意 \(t\in[0,2]\)，
\[
f'(t)\le p+|t-x_0|.
\]
于是
\[
f(2)-f(0)=\int_0^2 f'(t)\,dt
\le \int_0^2 \bigl(p+|t-x_0|\bigr)\,dt
\le 2p+2<-2.
\]
但
\[
f(2)-f(0)\ge -|f(2)|-|f(0)|\ge-2,
\]
矛盾。因此
\[
f'(x_0)\ge-2.
\]
由于 \(x_0\in[0,2]\) 任意，故
\[
|f'(x)|\le2\qquad(0\le x\le2).
\]
\examnote{这类题不要只用单点泰勒估计；把导数在全区间积分，能同时利用 \(|f|\le1\) 与 \(|f''|\le1\)。}
\end{solutionblock}

\section{第二章完成说明}
第二章第 \(1\)--\(54\) 题已按“题目解析、完整推导、答案、考研提示”的格式整理完毕。下一步从第三章一元函数积分学继续补充。
"""


CH03_TEX = r"""\chapter{一元函数积分学}

\section{原题页索引}
本章原题对应做题本第 \(39\)--\(62\) 页。本节完成第 \(1\)--\(61\) 题详细解析。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_039.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 若 \(f(x)\) 的导函数是 \(\sin x\)，则 \(f(x)\) 有一个原函数为
\[
\text{A. }1+\sin x\quad
\text{B. }1-\sin x\quad
\text{C. }1+\cos x\quad
\text{D. }1-\cos x.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{已知的是 \(f'(x)=\sin x\)，先还原 \(f(x)\)，再判断谁的导数可以等于 \(f(x)\)。}
由 \(f'(x)=\sin x\)，得
\[
f(x)=-\cos x+C.
\]
选项 B 的导数为
\[
(1-\sin x)'=-\cos x.
\]
这对应 \(C=0\) 时的 \(f(x)\)，因此 \(1-\sin x\) 是 \(f(x)\) 的一个原函数。
\[
\boxed{\text{B}}
\]
\examnote{“\(f\) 的导函数”和“\(f\) 的原函数”不要混淆。本题要先由 \(f'\) 求 \(f\)，再由 \(f\) 找原函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 设
\[
f(x)=
\begin{cases}
\cos x,&x\ge0,\\
\sin x,&x<0,
\end{cases}
\qquad
g(x)=
\begin{cases}
x\sin\dfrac1x,&x\ne0,\\
0,&x=0.
\end{cases}
\]
则在 \((-\infty,+\infty)\) 上
\[
\text{A. }f,g\text{ 都存在原函数}\quad
\text{B. }f,g\text{ 都不存在原函数}
\]
\[
\text{C. }f\text{ 存在原函数},g\text{ 不存在原函数}\quad
\text{D. }f\text{ 不存在原函数},g\text{ 存在原函数}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{原函数的导数必须具有介值性。连续函数一定存在原函数。}
函数 \(f\) 在 \(x=0\) 处左极限为
\[
\lim_{x\to0^-}\sin x=0,
\]
右侧函数值趋于
\[
\lim_{x\to0^+}\cos x=1.
\]
若 \(f\) 是某函数的导数，则 \(f\) 必须满足达布性质，即不能在 \(0\) 附近从接近 \(0\) 跳到接近 \(1\) 而漏掉中间值。因此 \(f\) 不存在原函数。

而 \(g(x)=x\sin(1/x)\) 在 \(x=0\) 处连续，因为
\[
|x\sin(1/x)|\le |x|\to0.
\]
连续函数在任意区间上都有原函数，所以 \(g\) 存在原函数。
\[
\boxed{\text{D}}
\]
\examnote{判断“是否存在原函数”时，连续性是充分条件；不连续函数还要看是否违反导数的介值性。}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 已知
\[
f(x)=
\begin{cases}
x^2,&0\le x<1,\\
1,&1\le x\le2,
\end{cases}
\qquad
F(x)=\int_1^x f(t)\,dt\quad(0\le x\le2).
\]
求 \(F(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{积分下限为 \(1\)，当 \(x<1\) 时要反向积分。}
当 \(0\le x<1\) 时，
\[
F(x)=\int_1^x t^2\,dt=-\int_x^1t^2\,dt
=\frac{x^3-1}{3}.
\]
当 \(1\le x\le2\) 时，
\[
F(x)=\int_1^x1\,dt=x-1.
\]
因此
\[
F(x)=
\begin{cases}
\dfrac13x^3-\dfrac13,&0\le x<1,\\
x-1,&1\le x\le2.
\end{cases}
\]
\[
\boxed{\text{D}}
\]
\examnote{变下限积分要注意方向，不能把 \(\int_1^x\) 误看成 \(\int_0^x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 设
\[
f(x)=
\begin{cases}
e^x,&x\le0,\\
x^2+a,&x>0,
\end{cases}
\qquad
F(x)=\int_{-1}^x f(t)\,dt.
\]
判断 \(F(x)\) 在 \(x=0\) 处的可导性。
\end{problemblock}

\begin{solutionblock}
\analysis{积分函数 \(F\) 一定连续；在分段点可导要看被积函数左右极限是否一致。}
由于 \(f\) 在 \([-1,x]\) 上分段连续，\(F\) 在 \(0\) 处连续。
左导数为
\[
F'_-(0)=\lim_{x\to0^-}f(x)=1.
\]
右导数为
\[
F'_+(0)=\lim_{x\to0^+}f(x)=a.
\]
故 \(F\) 在 \(0\) 处可导当且仅当
\[
a=1.
\]
\[
\boxed{\text{D}}
\]
\examnote{变上限定积分在连续点处导数等于被积函数；在间断点处要分别算左右导数。}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 设在区间 \([a,b]\) 上 \(f(x)>0,\ f'(x)<0,\ f''(x)>0\)。令
\[
S_1=\int_a^b f(x)\,dx,\quad
S_2=f(b)(b-a),\quad
S_3=\frac12[f(a)+f(b)](b-a).
\]
比较 \(S_1,S_2,S_3\) 的大小。
\end{problemblock}

\begin{solutionblock}
\analysis{\(f'<0\) 表明函数递减，右端矩形低估面积；\(f''>0\) 表明函数凸，梯形面积高估曲边梯形面积。}
因为 \(f\) 单调递减，故对 \(x\in(a,b)\)，
\[
f(x)>f(b),
\]
所以
\[
S_1>\int_a^b f(b)\,dx=f(b)(b-a)=S_2.
\]
又因为 \(f''(x)>0\)，函数图像是凸的，曲线位于端点弦线下方，因此梯形面积大于曲边梯形面积：
\[
S_1<S_3.
\]
故
\[
S_2<S_1<S_3.
\]
\[
\boxed{\text{B}}
\]
\examnote{单调性比较矩形面积，凸凹性比较梯形面积，这是积分几何估值的固定套路。}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 设 \(f(x)\) 连续，求
\[
\frac{d}{dx}\int_0^x t f(x^2-t^2)\,dt.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先换元把 \(x\) 同时出现在上限和被积函数中的复杂形式化成普通变上限积分。}
令
\[
u=x^2-t^2,\qquad du=-2t\,dt.
\]
当 \(t=0\) 时 \(u=x^2\)，当 \(t=x\) 时 \(u=0\)。于是
\[
\int_0^x t f(x^2-t^2)\,dt
=\frac12\int_0^{x^2}f(u)\,du.
\]
所以
\[
\frac{d}{dx}\int_0^x t f(x^2-t^2)\,dt
=\frac12 f(x^2)\cdot 2x
=xf(x^2).
\]
\[
\boxed{\text{A}}
\]
\examnote{含 \(x^2-t^2\) 且前面有 \(t\,dt\)，优先令 \(u=x^2-t^2\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 设 \(f(x)\) 连续，且存在常数 \(a\)，满足
\[
5x^3+40=\int_a^x f(t)\,dt.
\]
当 \(x\to0\) 时，\(axf(x)\) 与 \(c(\tan x-x)^k\) 是等价无穷小，求 \(k,c\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先由积分等式确定 \(a\)，再求 \(f(x)\)，最后与 \(\tan x-x\sim x^3/3\) 比较。}
令 \(x=a\)，右端为 \(0\)，所以
\[
5a^3+40=0,\qquad a=-2.
\]
对原式两边求导，得
\[
f(x)=15x^2.
\]
于是
\[
axf(x)=-2x\cdot15x^2=-30x^3.
\]
又
\[
\tan x-x\sim \frac{x^3}{3}\quad(x\to0).
\]
要使 \(c(\tan x-x)^k\) 与 \(-30x^3\) 等价，必须
\[
k=1,\qquad c\cdot\frac13=-30,
\]
即
\[
c=-90.
\]
\[
\boxed{\text{D}}
\]
\examnote{等价无穷小比较幂次先定 \(k\)，再定系数。}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 设
\[
a_n=\frac32\int_0^{(n+1)/n}x^{n-1}\sqrt{1+x^n}\,dx,
\]
求
\[
\lim_{n\to\infty}na_n.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{被积函数含 \(x^{n-1}\) 与 \(1+x^n\)，直接令 \(u=1+x^n\)。}
令
\[
u=1+x^n,\qquad du=nx^{n-1}\,dx.
\]
则
\[
a_n=\frac{3}{2n}\int_1^{1+\left(1+\frac1n\right)^n}u^{1/2}\,du
=\frac1n\left[u^{3/2}\right]_1^{1+\left(1+\frac1n\right)^n}.
\]
所以
\[
na_n=\left[1+\left(1+\frac1n\right)^n\right]^{3/2}-1.
\]
令 \(n\to\infty\)，得
\[
\lim_{n\to\infty}na_n=(1+e)^{3/2}-1.
\]
\[
\boxed{\text{D}}
\]
\examnote{\((1+1/n)^n\to e\) 与含参积分换元经常一起出现。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 求
\[
\lim_{n\to\infty}\ln\sqrt[n]{\left(1+\frac1n\right)^2
\left(1+\frac2n\right)^2\cdots
\left(1+\frac nn\right)^2}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先取对数并把乘积化为和，再识别黎曼和。}
原式等于
\[
\lim_{n\to\infty}\frac1n\sum_{k=1}^n
2\ln\left(1+\frac{k}{n}\right).
\]
这是区间 \([0,1]\) 上函数 \(2\ln(1+x)\) 的黎曼和，故极限为
\[
2\int_0^1\ln(1+x)\,dx.
\]
令 \(u=1+x\)，得
\[
2\int_0^1\ln(1+x)\,dx=2\int_1^2\ln u\,du.
\]
\[
\boxed{\text{B}}
\]
\examnote{乘积极限常先取对数；\(\frac1n\sum \varphi(k/n)\) 是黎曼和标准形。}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 设
\[
I_1=\int_0^{\pi/2}\sin(\sin x)\,dx,\qquad
I_2=\int_0^{\pi/2}\cos(\sin x)\,dx.
\]
比较 \(I_1,I_2,1\) 的大小。
\end{problemblock}

\begin{solutionblock}
\analysis{用基本不等式与单调性比较：\(\sin u<u\)，且 \(\sin x<x\) 推出 \(\cos(\sin x)>\cos x\)。}
当 \(0<x<\pi/2\) 时，
\[
0<\sin x<x,\qquad \sin(\sin x)<\sin x.
\]
因此
\[
I_1<\int_0^{\pi/2}\sin x\,dx=1.
\]
又因 \(\cos u\) 在 \([0,\pi/2]\) 上单调递减，且 \(\sin x<x\)，故
\[
\cos(\sin x)>\cos x.
\]
于是
\[
I_2>\int_0^{\pi/2}\cos x\,dx=1.
\]
所以
\[
I_1<1<I_2.
\]
\[
\boxed{\text{A}}
\]
\examnote{比较积分大小时，先比较被积函数；不必强行求积分值。}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 设
\[
I=\int_0^{\pi/4}\ln\sin x\,dx,\quad
J=\int_0^{\pi/4}\ln\cot x\,dx,\quad
K=\int_0^{\pi/4}\ln\cos x\,dx.
\]
比较 \(I,J,K\) 的大小。
\end{problemblock}

\begin{solutionblock}
\analysis{在 \((0,\pi/4)\) 上 \(\cos x>\sin x\)，所以 \(\ln\cos x>\ln\sin x\)。同时 \(\cot x>1\)，所以 \(J>0\)。}
因为
\[
\ln\cot x=\ln\cos x-\ln\sin x,
\]
所以
\[
J=K-I.
\]
在 \(0<x<\pi/4\) 上，
\[
0<\sin x<\cos x<1.
\]
因此
\[
\ln\sin x<\ln\cos x<0,
\]
即
\[
I<K<0.
\]
又 \(\cot x>1\)，故
\[
J=\int_0^{\pi/4}\ln\cot x\,dx>0.
\]
于是
\[
I<K<J.
\]
\[
\boxed{\text{B}}
\]
\examnote{含 \(\ln\cot x\) 时先拆成 \(\ln\cos x-\ln\sin x\)，符号关系会很清楚。}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 设
\[
I_k=\int_0^{k\pi}e^{x^2}\sin x\,dx\qquad(k=1,2,3).
\]
比较 \(I_1,I_2,I_3\) 的大小。
\end{problemblock}

\begin{solutionblock}
\analysis{\(\sin x\) 正负交替，而 \(e^{x^2}\) 递增。后面的半波权重更大，这是比较的关键。}
显然
\[
I_1=\int_0^\pi e^{x^2}\sin x\,dx>0.
\]
又
\[
I_2-I_1=\int_\pi^{2\pi}e^{x^2}\sin x\,dx<0,
\]
所以
\[
I_2<I_1.
\]
比较 \(I_3\) 与 \(I_1\)：
\[
I_3-I_1=\int_\pi^{3\pi}e^{x^2}\sin x\,dx.
\]
将 \([2\pi,3\pi]\) 上的积分令 \(x=u+\pi\)，得
\[
I_3-I_1
=\int_\pi^{2\pi}\left[e^{x^2}-e^{(x+\pi)^2}\right]\sin x\,dx.
\]
在 \((\pi,2\pi)\) 上，
\[
\sin x<0,\qquad e^{x^2}-e^{(x+\pi)^2}<0,
\]
故乘积为正，因而
\[
I_3>I_1.
\]
综上
\[
I_2<I_1<I_3.
\]
\[
\boxed{\text{D}}
\]
\examnote{含 \(\sin x\) 的多周期积分，常按相邻半波配对比较权重。}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 曲线
\[
y=\sin^{3/2}x\quad(0\le x\le\pi)
\]
与 \(x\) 轴围成的图形绕 \(x\) 轴旋转所得旋转体体积为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{绕 \(x\) 轴旋转，用圆盘法 \(V=\pi\int y^2\,dx\)。}
有
\[
y^2=\sin^3x.
\]
所以
\[
V=\pi\int_0^\pi \sin^3x\,dx.
\]
而
\[
\int_0^\pi\sin^3x\,dx
=\int_0^\pi(1-\cos^2x)\sin x\,dx
=\frac43.
\]
故
\[
V=\frac43\pi.
\]
\[
\boxed{\text{B}}
\]
\examnote{旋转体体积要平方半径；本题 \(y=\sin^{3/2}x\)，平方后才是 \(\sin^3x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 计算
\[
\int\frac{x+5}{x^2-6x+13}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{分母配方，并把分子拆成分母导数的一部分加常数。}
因为
\[
x^2-6x+13=(x-3)^2+4,
\]
且
\[
x+5=\frac12(2x-6)+8.
\]
所以
\[
\int\frac{x+5}{x^2-6x+13}\,dx
=\frac12\ln(x^2-6x+13)
8\int\frac{dx}{(x-3)^2+4}.
\]
后一个积分为
\[
8\cdot\frac12\arctan\frac{x-3}{2}
=4\arctan\frac{x-3}{2}.
\]
故
\[
\boxed{\frac12\ln(x^2-6x+13)+4\arctan\frac{x-3}{2}+C}.
\]
\examnote{有不可约二次式时，通常会同时出现 \(\ln\) 与 \(\arctan\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 计算
\[
\int\frac{\arcsin x}{x^2}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{含反三角函数乘 \(x^{-2}\)，优先分部积分。}
取
\[
u=\arcsin x,\qquad dv=\frac{dx}{x^2}.
\]
则
\[
du=\frac{dx}{\sqrt{1-x^2}},\qquad v=-\frac1x.
\]
于是
\[
\int\frac{\arcsin x}{x^2}\,dx
=-\frac{\arcsin x}{x}
\int\frac{dx}{x\sqrt{1-x^2}}.
\]
令 \(x=\sin\theta\)，则
\[
\int\frac{dx}{x\sqrt{1-x^2}}
=\int \csc\theta\,d\theta
=\ln\left|\tan\frac{\theta}{2}\right|.
\]
由
\[
\tan\frac{\theta}{2}=\frac{\sin\theta}{1+\cos\theta}
=\frac{x}{1+\sqrt{1-x^2}},
\]
得
\[
\boxed{
\int\frac{\arcsin x}{x^2}\,dx
=-\frac{\arcsin x}{x}
\ln\left|\frac{x}{1+\sqrt{1-x^2}}\right|+C }.
\]
\examnote{反三角函数积分常用分部积分；\(\int\csc\theta\,d\theta\) 的结果要熟。}
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 计算
\[
\int\frac{x^2e^x}{(x+2)^2}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{寻找形如 \((e^xR(x))'\) 的结构，即解 \(R+R'=x^2/(x+2)^2\)。}
注意到
\[
\frac{x^2}{(x+2)^2}
=\left(1-\frac4{x+2}\right)
\left(1-\frac4{x+2}\right)'.
\]
因此
\[
\left[e^x\left(1-\frac4{x+2}\right)\right]'
=e^x\frac{x^2}{(x+2)^2}.
\]
所以
\[
\boxed{
\int\frac{x^2e^x}{(x+2)^2}\,dx
=e^x\left(1-\frac4{x+2}\right)+C
=\frac{(x-2)e^x}{x+2}+C }.
\]
\examnote{有 \(e^x\) 乘有理式时，可尝试把原式配成 \((e^xR)'=e^x(R+R')\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 设 \(f(x)\) 是连续函数，且
\[
\int_0^{x^3-1}f(t)\,dt=x-1.
\]
求 \(f(7)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{对变上限积分求导，再令上限 \(x^3-1=7\)。}
两边对 \(x\) 求导：
\[
f(x^3-1)\cdot 3x^2=1.
\]
要计算 \(f(7)\)，令
\[
x^3-1=7,\qquad x=2.
\]
于是
\[
f(7)\cdot 3\cdot 2^2=1,
\]
故
\[
\boxed{f(7)=\frac1{12}}.
\]
\examnote{变上限是复合函数时，求导必须乘上限的导数。}
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 设 \(f(x)\) 是连续函数，且
\[
f(x)=x+2\int_0^1f(t)\,dt.
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{把定积分看作常数，反代求常数。}
令
\[
A=\int_0^1f(t)\,dt.
\]
则
\[
f(x)=x+2A.
\]
两边在 \([0,1]\) 上积分：
\[
A=\int_0^1(x+2A)\,dx=\frac12+2A.
\]
所以
\[
A=-\frac12.
\]
代回得
\[
\boxed{f(x)=x-1}.
\]
\examnote{含 \(\int_0^1f(t)\,dt\) 的方程，一般先设常数 \(A\)，再积分求 \(A\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{19.} 计算
\[
\int_0^1\frac{x\,dx}{(2-x^2)\sqrt{1-x^2}}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{根号中是 \(1-x^2\)，且有 \(x\,dx\)，令 \(u=\sqrt{1-x^2}\)。}
令
\[
u=\sqrt{1-x^2},\qquad x\,dx=-u\,du.
\]
又
\[
2-x^2=1+u^2.
\]
当 \(x=0\) 时 \(u=1\)，当 \(x=1\) 时 \(u=0\)。故
\[
\int_0^1\frac{x\,dx}{(2-x^2)\sqrt{1-x^2}}
=\int_1^0\frac{-du}{1+u^2}
=\int_0^1\frac{du}{1+u^2}
=\frac{\pi}{4}.
\]
\[
\boxed{\frac{\pi}{4}}
\]
\examnote{根号换元后要同步改上下限，避免符号出错。}
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 计算
\[
\int_0^{\pi^2}\sqrt{x}\cos\sqrt{x}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(t=\sqrt{x}\)，把根号变量变为普通三角积分。}
令
\[
t=\sqrt{x},\qquad x=t^2,\qquad dx=2t\,dt.
\]
则
\[
\int_0^{\pi^2}\sqrt{x}\cos\sqrt{x}\,dx
=2\int_0^\pi t^2\cos t\,dt.
\]
分部积分可得
\[
\int t^2\cos t\,dt=t^2\sin t+2t\cos t-2\sin t.
\]
于是
\[
2\int_0^\pi t^2\cos t\,dt
=2[-2\pi]
=-4\pi.
\]
\[
\boxed{-4\pi}
\]
\examnote{出现 \(\sqrt{x}\) 同时在代数项和三角函数中，令 \(t=\sqrt{x}\) 通常最直接。}
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 计算
\[
\int_{-\pi/2}^{\pi/2}
\left[\cos^2x+\int_0^x e^{-t^2}\,dt\right]\sin^2x\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{利用奇偶性。\(\int_0^x e^{-t^2}dt\) 是奇函数，\(\sin^2x\) 是偶函数。}
记
\[
E(x)=\int_0^x e^{-t^2}\,dt.
\]
因为 \(e^{-t^2}\) 是偶函数，所以 \(E(x)\) 是奇函数。于是
\[
E(x)\sin^2x
\]
是奇函数，在对称区间上的积分为 \(0\)。
因此原积分等于
\[
\int_{-\pi/2}^{\pi/2}\cos^2x\sin^2x\,dx.
\]
由
\[
\sin^2x\cos^2x=\frac18(1-\cos4x),
\]
得
\[
\int_{-\pi/2}^{\pi/2}\cos^2x\sin^2x\,dx
=\frac18\int_{-\pi/2}^{\pi/2}(1-\cos4x)\,dx
=\frac{\pi}{8}.
\]
\[
\boxed{\frac{\pi}{8}}
\]
\examnote{对称区间积分先看奇偶性，经常可以直接消去复杂项。}
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 计算
\[
\int_0^\pi x\sqrt{\cos^2x-\cos^4x}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{根号化简为 \(|\sin x\cos x|\)，再用关于 \(\pi/2\) 的对称性。}
因为
\[
\sqrt{\cos^2x-\cos^4x}
=\sqrt{\cos^2x(1-\cos^2x)}
=|\sin x\cos x|.
\]
设
\[
q(x)=|\sin x\cos x|.
\]
则
\[
q(\pi-x)=q(x).
\]
因此
\[
\int_0^\pi xq(x)\,dx
=\frac{\pi}{2}\int_0^\pi q(x)\,dx.
\]
而
\[
\int_0^\pi|\sin x\cos x|\,dx
=2\int_0^{\pi/2}\sin x\cos x\,dx=1.
\]
所以
\[
\boxed{\frac{\pi}{2}}.
\]
\examnote{若 \(q(\pi-x)=q(x)\)，则 \(\int_0^\pi xq(x)dx=\frac{\pi}{2}\int_0^\pi q(x)dx\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 设 \(a>0\)，计算
\[
\int_0^{2a}x\sqrt{2ax-x^2}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把二次式配成圆：\(2ax-x^2=a^2-(x-a)^2\)。}
令
\[
u=x-a.
\]
则
\[
2ax-x^2=a^2-u^2,\qquad x=u+a.
\]
积分化为
\[
\int_{-a}^{a}(u+a)\sqrt{a^2-u^2}\,du.
\]
其中
\[
\int_{-a}^{a}u\sqrt{a^2-u^2}\,du=0
\]
因为被积函数为奇函数。因此
\[
\int_0^{2a}x\sqrt{2ax-x^2}\,dx
=a\int_{-a}^{a}\sqrt{a^2-u^2}\,du.
\]
后一个积分是半径为 \(a\) 的上半圆面积：
\[
\int_{-a}^{a}\sqrt{a^2-u^2}\,du=\frac{\pi a^2}{2}.
\]
故
\[
\boxed{\frac{\pi a^3}{2}}.
\]
\examnote{含 \(\sqrt{2ax-x^2}\) 时，配方后常转化为半圆面积。}
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 设
\[
f(x)=x-\int_0^\pi f(x)\cos x\,dx.
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{积分号中的变量与外面的 \(x\) 同名，实质上该定积分是一个常数。设它为 \(A\)，再反代。}
令
\[
A=\int_0^\pi f(x)\cos x\,dx.
\]
则
\[
f(x)=x-A.
\]
代入 \(A\)：
\[
A=\int_0^\pi (x-A)\cos x\,dx
=\int_0^\pi x\cos x\,dx-A\int_0^\pi\cos x\,dx.
\]
由于
\[
\int_0^\pi\cos x\,dx=0,
\]
且
\[
\int_0^\pi x\cos x\,dx
=\left[x\sin x+\cos x\right]_0^\pi=-2,
\]
所以
\[
A=-2.
\]
故
\[
\boxed{f(x)=x+2}.
\]
\examnote{定积分变量只是哑变量；遇到这种题先把整个积分设为常数。}
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 设 \(f(x)\) 为连续函数，且
\[
\int_0^x f(t)\,dt=3x^3-x\int_{-1}^{1}f(t)\,dt.
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{把 \(\int_{-1}^{1}f(t)dt\) 设为常数，再由求导和反代确定。}
令
\[
A=\int_{-1}^{1}f(t)\,dt.
\]
则
\[
\int_0^x f(t)\,dt=3x^3-Ax.
\]
两边求导得
\[
f(x)=9x^2-A.
\]
于是
\[
A=\int_{-1}^{1}(9x^2-A)\,dx=6-2A.
\]
故
\[
A=2.
\]
所以
\[
\boxed{f(x)=9x^2-2}.
\]
\examnote{含未知函数的定积分常数，依然是“设常数、求导、反代”。}
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 求
\[
\lim_{n\to\infty}\frac1{n^2}\left[
\sqrt{n^2-1}+\sqrt{n^2-2^2}+\cdots+\sqrt{n^2-(n-1)^2}
\right].
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把每项提出一个 \(n\)，化成黎曼和。}
原式等于
\[
\lim_{n\to\infty}\frac1n\sum_{k=1}^{n-1}
\sqrt{1-\left(\frac{k}{n}\right)^2}.
\]
这是函数 \(\sqrt{1-x^2}\) 在 \([0,1]\) 上的黎曼和，因此极限为
\[
\int_0^1\sqrt{1-x^2}\,dx.
\]
该积分表示单位圆第一象限面积，故
\[
\boxed{\frac{\pi}{4}}.
\]
\examnote{根式和式极限常对应几何面积；这里就是四分之一单位圆。}
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 求
\[
\lim_{n\to\infty}\frac1n\left(
\sqrt{1+\cos\frac{\pi}{n}}
+\sqrt{1+\cos\frac{2\pi}{n}}
+\cdots
+\sqrt{1+\cos\frac{n\pi}{n}}
\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先识别黎曼和，再用半角公式化简被积函数。}
原式为
\[
\int_0^1\sqrt{1+\cos\pi x}\,dx.
\]
由
\[
1+\cos\pi x=2\cos^2\frac{\pi x}{2},
\]
且 \(0\le x\le1\) 时 \(\cos(\pi x/2)\ge0\)，所以
\[
\sqrt{1+\cos\pi x}=\sqrt2\cos\frac{\pi x}{2}.
\]
因此
\[
\int_0^1\sqrt{1+\cos\pi x}\,dx
=\sqrt2\int_0^1\cos\frac{\pi x}{2}\,dx
=\sqrt2\cdot\frac{2}{\pi}.
\]
故
\[
\boxed{\frac{2\sqrt2}{\pi}}.
\]
\examnote{黎曼和中的 \(\cos(k\pi/n)\) 对应 \(\cos\pi x\)，不要漏掉 \(\pi\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 求
\[
\lim_{n\to\infty}\int_0^1 e^{-x}\sin nx\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是典型的振荡积分，连续函数乘 \(\sin nx\) 在有限区间上的积分趋于 \(0\)。}
由黎曼-勒贝格型结论，
\[
\lim_{n\to\infty}\int_0^1 e^{-x}\sin nx\,dx=0.
\]
也可分部积分：
\[
\int_0^1 e^{-x}\sin nx\,dx
=\left[-\frac{e^{-x}\cos nx}{n}\right]_0^1
-\frac1n\int_0^1 e^{-x}\cos nx\,dx,
\]
右端绝对值被 \(O(1/n)\) 控制，故极限为
\[
\boxed{0}.
\]
\examnote{固定区间上，光滑函数乘高频 \(\sin nx\) 或 \(\cos nx\) 的积分通常趋于 \(0\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 设函数 \(f(x)\) 连续，且
\[
\int_0^x f(t-x)\,dt=(1+x^2)^x-1.
\]
求
\[
\int_{-1}^{1}f(x)\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先把左边换元成 \(\int_{-x}^0f(u)du\)，再求导得到 \(f(-x)\)。}
令 \(u=t-x\)，则
\[
\int_0^x f(t-x)\,dt=\int_{-x}^0 f(u)\,du.
\]
记
\[
\varphi(x)=(1+x^2)^x-1.
\]
于是
\[
\int_{-x}^0 f(u)\,du=\varphi(x).
\]
两边对 \(x\) 求导：
\[
-f(-x)=\varphi'(x),
\]
即
\[
f(-x)=-\varphi'(x).
\]
因此
\[
\int_{-1}^{1}f(u)\,du
=\int_{-1}^{1}f(-x)\,dx
=-\int_{-1}^{1}\varphi'(x)\,dx.
\]
所以
\[
\int_{-1}^{1}f(u)\,du
=-[\varphi(1)-\varphi(-1)].
\]
计算
\[
\varphi(1)=2^1-1=1,\qquad
\varphi(-1)=2^{-1}-1=-\frac12.
\]
故
\[
\boxed{\int_{-1}^{1}f(x)\,dx=-\frac32}.
\]
\examnote{变下限含 \(-x\) 时，求导符号最容易错；本题关键是 \(\frac{d}{dx}\int_{-x}^{0}f(u)du=-f(-x)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 若
\[
\int_0^x f(t)\,dt=xe^{-x},
\]
求
\[
\int_1^{+\infty}\frac{f(\ln x)}{x}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先用 \(u=\ln x\) 把反常积分化回 \(f(u)\) 的积分。}
令
\[
u=\ln x,\qquad \frac{dx}{x}=du.
\]
当 \(x=1\) 时 \(u=0\)，当 \(x\to+\infty\) 时 \(u\to+\infty\)。所以
\[
\int_1^{+\infty}\frac{f(\ln x)}{x}\,dx
=\int_0^{+\infty}f(u)\,du.
\]
由题设
\[
\int_0^x f(t)\,dt=xe^{-x}.
\]
令 \(x\to+\infty\)，得
\[
\int_0^{+\infty}f(t)\,dt
=\lim_{x\to+\infty}xe^{-x}=0.
\]
故
\[
\boxed{0}.
\]
\examnote{出现 \(f(\ln x)/x\)，几乎必令 \(u=\ln x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 计算
\[
\int_2^{+\infty}\frac{dx}{(x+7)\sqrt{x-2}}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(u=\sqrt{x-2}\)，根号和无穷上限都会简化。}
令
\[
u=\sqrt{x-2},\qquad x=u^2+2,\qquad dx=2u\,du.
\]
则
\[
x+7=u^2+9.
\]
原积分为
\[
\int_0^{+\infty}\frac{2u\,du}{(u^2+9)u}
=\int_0^{+\infty}\frac{2\,du}{u^2+9}.
\]
所以
\[
\int_0^{+\infty}\frac{2\,du}{u^2+9}
=2\cdot \frac{\pi}{2\cdot3}
=\frac{\pi}{3}.
\]
\[
\boxed{\frac{\pi}{3}}
\]
\examnote{反常积分换元后要同时检查新上限；本题 \(x\to+\infty\) 对应 \(u\to+\infty\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{32.} 函数
\[
y=\frac{x^2}{\sqrt{1-x^2}}
\]
在区间
\[
\left[\frac12,\frac{\sqrt3}{2}\right]
\]
上的平均值为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{函数平均值为区间积分除以区间长度。令 \(x=\sin t\)。}
平均值为
\[
\frac{1}{\frac{\sqrt3}{2}-\frac12}
\int_{1/2}^{\sqrt3/2}\frac{x^2}{\sqrt{1-x^2}}\,dx.
\]
令
\[
x=\sin t.
\]
则 \(t\) 从 \(\pi/6\) 到 \(\pi/3\)，且
\[
\frac{x^2}{\sqrt{1-x^2}}dx=\sin^2t\,dt.
\]
因此
\[
\int_{1/2}^{\sqrt3/2}\frac{x^2}{\sqrt{1-x^2}}\,dx
=\int_{\pi/6}^{\pi/3}\sin^2t\,dt
=\frac{\pi}{12}.
\]
区间长度为
\[
\frac{\sqrt3-1}{2}.
\]
所以平均值为
\[
\frac{\pi/12}{(\sqrt3-1)/2}
=\frac{\pi}{6(\sqrt3-1)}
=\boxed{\frac{\pi(\sqrt3+1)}{12}}.
\]
\examnote{平均值不是积分值，最后一定要除以区间长度。}
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 由曲线
\[
y=x+\frac1x,\qquad x=2,\qquad y=2
\]
所围图形的面积 \(S\) 为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{先求交点。\(x+1/x=2\) 给出 \(x=1\)。}
由
\[
x+\frac1x=2
\]
得
\[
(x-1)^2=0,\qquad x=1.
\]
在 \(1\le x\le2\) 上，
\[
x+\frac1x\ge2.
\]
所以面积
\[
S=\int_1^2\left(x+\frac1x-2\right)\,dx.
\]
计算得
\[
S=\left[\frac{x^2}{2}+\ln x-2x\right]_1^2
=\ln2-\frac12.
\]
故
\[
\boxed{\ln2-\frac12}.
\]
\examnote{面积题先画上下关系；本题曲线在直线 \(y=2\) 上方。}
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 设曲线的极坐标方程为
\[
r=e^{a\theta}\quad(a>0),
\]
求该曲线上 \(\theta\) 从 \(0\) 变到 \(2\pi\) 的一段弧与极轴所围成图形的面积。
\end{problemblock}

\begin{solutionblock}
\analysis{极坐标面积公式为 \(S=\frac12\int r^2\,d\theta\)。}
所求面积为
\[
S=\frac12\int_0^{2\pi}e^{2a\theta}\,d\theta.
\]
计算得
\[
S=\frac12\cdot \frac{e^{2a\theta}}{2a}\bigg|_0^{2\pi}
=\frac{e^{4\pi a}-1}{4a}.
\]
故
\[
\boxed{\frac{e^{4\pi a}-1}{4a}}.
\]
\examnote{极坐标面积不要漏掉系数 \(1/2\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{35.}（数学三不要求）曲线
\[
y=\int_0^x\tan t\,dt\qquad\left(0\le x\le\frac{\pi}{4}\right)
\]
的弧长 \(s\) 为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{先求导 \(y'=\tan x\)，再用弧长公式。}
弧长
\[
s=\int_0^{\pi/4}\sqrt{1+(y')^2}\,dx
=\int_0^{\pi/4}\sqrt{1+\tan^2x}\,dx.
\]
因为在该区间 \(\sec x>0\)，所以
\[
s=\int_0^{\pi/4}\sec x\,dx
=\left[\ln|\sec x+\tan x|\right]_0^{\pi/4}.
\]
故
\[
\boxed{s=\ln(1+\sqrt2)}.
\]
\examnote{变上限定积分给出的曲线，先由牛顿-莱布尼茨公式求 \(y'\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{36.}（数学三不要求）一根长为 \(1\) 的细棒位于 \(x\) 轴的区间 \([0,1]\) 上，若其线密度
\[
\rho=-x^2+2x+1,
\]
求该细棒的质心坐标 \(\bar x\)。
\end{problemblock}

\begin{solutionblock}
\analysis{质心坐标等于一阶矩除以质量。}
质量为
\[
m=\int_0^1(-x^2+2x+1)\,dx
=-\frac13+1+1=\frac53.
\]
关于原点的一阶矩为
\[
M=\int_0^1x(-x^2+2x+1)\,dx
=-\frac14+\frac23+\frac12
=\frac{11}{12}.
\]
故
\[
\bar x=\frac{M}{m}
=\frac{11/12}{5/3}
=\boxed{\frac{11}{20}}.
\]
\examnote{质心题记住 \(\bar x=\dfrac{\int x\rho(x)\,dx}{\int\rho(x)\,dx}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 计算
\[
\int_0^1\frac{f(x)}{\sqrt{x}}\,dx,\qquad
f(x)=\int_1^x\frac{\ln(1+t)}{t}\,dt.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{外层积分含 \(f(x)x^{-1/2}\)，用分部积分把 \(f\) 转成 \(f'\)。}
取
\[
u=f(x),\qquad dv=x^{-1/2}\,dx,
\]
则
\[
du=\frac{\ln(1+x)}{x}\,dx,\qquad v=2\sqrt{x}.
\]
由于 \(f(1)=0\)，且 \(\sqrt{x}f(x)\to0\ (x\to0^+)\)，所以
\[
\int_0^1\frac{f(x)}{\sqrt{x}}\,dx
=-2\int_0^1\frac{\ln(1+x)}{\sqrt{x}}\,dx.
\]
令 \(x=t^2\)，得
\[
-2\int_0^1\frac{\ln(1+x)}{\sqrt{x}}\,dx
=-4\int_0^1\ln(1+t^2)\,dt.
\]
而
\[
\int_0^1\ln(1+t^2)\,dt
=\left[t\ln(1+t^2)-2t+2\arctan t\right]_0^1
=\ln2-2+\frac{\pi}{2}.
\]
故
\[
\boxed{8-4\ln2-2\pi}.
\]
\examnote{含“积分定义的函数”时，分部积分常能把未知函数降为已知导数。}
\end{solutionblock}

\begin{problemblock}
\textbf{38.} 计算积分
\[
\int_{1/2}^{3/2}\frac{dx}{\sqrt{|x-x^2|}}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{绝对值在 \(x=1\) 处分段：左边是 \(x-x^2\)，右边是 \(x^2-x\)。}
\[
\int_{1/2}^{3/2}\frac{dx}{\sqrt{|x-x^2|}}
=\int_{1/2}^{1}\frac{dx}{\sqrt{x(1-x)}}
+\int_1^{3/2}\frac{dx}{\sqrt{x(x-1)}}.
\]
第一段令 \(2x-1=\sin u\)，得
\[
\int_{1/2}^{1}\frac{dx}{\sqrt{x(1-x)}}=\frac{\pi}{2}.
\]
第二段令 \(u=2x-1\)，则
\[
\int_1^{3/2}\frac{dx}{\sqrt{x(x-1)}}
=\int_1^2\frac{du}{\sqrt{u^2-1}}
=\ln(2+\sqrt3).
\]
所以
\[
\boxed{\frac{\pi}{2}+\ln(2+\sqrt3)}.
\]
\examnote{有绝对值的根式积分必须先找符号变化点。}
\end{solutionblock}

\begin{problemblock}
\textbf{39.} 求极限
\[
\lim_{x\to0}
\frac{\displaystyle\int_0^x\left[\int_0^{u^2}\arctan(1+t)\,dt\right]du}
{x(1-\cos x)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{只需抓主部。内层积分上限为 \(u^2\)，被积函数在 \(0\) 处为 \(\arctan1=\pi/4\)。}
当 \(u\to0\) 时，
\[
\int_0^{u^2}\arctan(1+t)\,dt
\sim \frac{\pi}{4}u^2.
\]
于是
\[
\int_0^x\left[\int_0^{u^2}\arctan(1+t)\,dt\right]du
\sim \int_0^x\frac{\pi}{4}u^2\,du
=\frac{\pi}{12}x^3.
\]
又
\[
x(1-\cos x)\sim x\cdot\frac{x^2}{2}=\frac{x^3}{2}.
\]
故极限为
\[
\boxed{\frac{\pi}{6}}.
\]
\examnote{多重变限积分求极限，先从最内层提取等价主部。}
\end{solutionblock}

\begin{problemblock}
\textbf{40.} 设 \(f(x)\) 为非负连续函数，且
\[
f(x)\int_0^x f(x-t)\,dt=\sin^4x.
\]
求 \(f(x)\) 在 \([0,\pi/2]\) 上的平均值。
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(F(x)=\int_0^x f(t)dt\)，则 \(\int_0^x f(x-t)dt=F(x)\)，并且 \(F'=f\)。}
令
\[
F(x)=\int_0^x f(t)\,dt.
\]
则题设化为
\[
F'(x)F(x)=\sin^4x.
\]
因此
\[
\frac12(F^2(x))'=\sin^4x.
\]
由 \(F(0)=0\)，得
\[
F^2(x)=2\int_0^x\sin^4t\,dt.
\]
因为 \(f\ge0\)，所以 \(F(x)\ge0\)。于是
\[
F\left(\frac{\pi}{2}\right)
=\sqrt{2\int_0^{\pi/2}\sin^4t\,dt}
=\sqrt{2\cdot\frac{3\pi}{16}}
=\sqrt{\frac{3\pi}{8}}.
\]
所求平均值为
\[
\frac{1}{\pi/2}\int_0^{\pi/2}f(x)\,dx
=\frac{2}{\pi}F\left(\frac{\pi}{2}\right)
=\boxed{\sqrt{\frac{3}{2\pi}}}.
\]
\examnote{卷积型 \(\int_0^x f(x-t)dt\) 换元后就是 \(\int_0^x f(t)dt\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{41.} 设 \(f(x)\) 在 \(x=a\) 的某邻域内可导，且 \(f(a)\ne0\)，求
\[
\lim_{x\to a}\left(
\frac{1}{(x-a)f(a)}
-\frac{1}{\displaystyle\int_a^x f(t)\,dt}
\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{两项都含一阶无穷小，直接通分后用积分的局部展开。}
记 \(h=x-a\)。因为 \(f\) 在 \(a\) 处可导，
\[
\int_a^x f(t)\,dt
=f(a)h+\frac12f'(a)h^2+o(h^2).
\]
于是
\[
\frac{1}{hf(a)}
-\frac{1}{\int_a^x f(t)\,dt}
=
\frac{\int_a^x f(t)\,dt-hf(a)}
{hf(a)\int_a^x f(t)\,dt}.
\]
分子为
\[
\frac12f'(a)h^2+o(h^2),
\]
分母为
\[
h f(a)\,[f(a)h+o(h)]=f^2(a)h^2+o(h^2).
\]
故极限为
\[
\boxed{\frac{f'(a)}{2f^2(a)}}.
\]
\examnote{两个无穷大相减，先通分；积分主部要展开到二阶。}
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 函数 \(f(x)\) 在 \([0,+\infty)\) 上可导，\(f(0)=0\)，且其反函数为 \(g(x)\)。若
\[
\int_x^{x+f(x)}g(t-x)\,dt=x^2\ln(1+x),
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先令 \(u=t-x\)，再使用反函数面积公式
\(\int_0^{f(x)}g(u)du=xf(x)-\int_0^x f(s)ds\)。}
令 \(u=t-x\)，则
\[
\int_x^{x+f(x)}g(t-x)\,dt
=\int_0^{f(x)}g(u)\,du.
\]
由反函数积分公式，
\[
\int_0^{f(x)}g(u)\,du+\int_0^x f(s)\,ds=xf(x).
\]
所以题设等价于
\[
xf(x)-\int_0^x f(s)\,ds=x^2\ln(1+x).
\]
两边求导：
\[
f(x)+xf'(x)-f(x)=2x\ln(1+x)+\frac{x^2}{1+x}.
\]
即
\[
f'(x)=2\ln(1+x)+\frac{x}{1+x}.
\]
由 \(f(0)=0\)，积分得
\[
f(x)=2\int_0^x\ln(1+t)\,dt+\int_0^x\frac{t}{1+t}\,dt.
\]
计算：
\[
2\int_0^x\ln(1+t)\,dt
=2[(1+x)\ln(1+x)-x],
\]
\[
\int_0^x\frac{t}{1+t}\,dt=x-\ln(1+x).
\]
故
\[
\boxed{f(x)=(2x+1)\ln(1+x)-x}.
\]
\examnote{反函数题常用面积公式：\(\int_0^a f+\int_0^{f(a)}f^{-1}=af(a)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{43.} 设函数
\[
S(x)=\int_0^x|\cos t|\,dt.
\]
\begin{enumerate}
\item 当 \(n\) 为正整数，且 \(n\pi\le x<(n+1)\pi\) 时，证明
\[
2n\le S(x)<2(n+1).
\]
\item 求
\[
\lim_{x\to+\infty}\frac{S(x)}{x}.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{\(|\cos t|\) 的周期为 \(\pi\)，每个周期面积为 \(2\)。}
\textbf{(1)} 因为
\[
\int_0^\pi|\cos t|\,dt=2,
\]
且 \(|\cos t|\) 以 \(\pi\) 为周期，所以
\[
S(n\pi)=2n.
\]
当 \(n\pi\le x<(n+1)\pi\) 时，
\[
S(x)=S(n\pi)+\int_{n\pi}^x|\cos t|\,dt.
\]
其中
\[
0\le\int_{n\pi}^x|\cos t|\,dt<2.
\]
故
\[
2n\le S(x)<2(n+1).
\]

\textbf{(2)} 若 \(n\pi\le x<(n+1)\pi\)，则
\[
\frac{2n}{(n+1)\pi}<\frac{S(x)}{x}\le\frac{2(n+1)}{n\pi}
\]
可作夹逼。令 \(x\to+\infty\) 时 \(n\to+\infty\)，两边都趋于
\[
\frac{2}{\pi}.
\]
因此
\[
\boxed{\lim_{x\to+\infty}\frac{S(x)}{x}=\frac{2}{\pi}}.
\]
\examnote{周期函数积分的长期平均值等于一个周期积分除以周期长度。}
\end{solutionblock}

\begin{problemblock}
\textbf{44.} 
\begin{enumerate}
\item 比较
\[
\int_0^1|\ln t|[\ln(1+t)]^n\,dt
\quad\text{与}\quad
\int_0^1t^n|\ln t|\,dt
\]
的大小，其中 \(n=1,2,\cdots\)；
\item 记
\[
u_n=\int_0^1|\ln t|[\ln(1+t)]^n\,dt,
\]
求
\[
\lim_{n\to\infty}u_n.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{在 \(0<t\le1\) 上有 \(0<\ln(1+t)<t\)，乘以正函数 \(|\ln t|\) 后积分比较。}
\textbf{(1)} 对 \(0<t\le1\)，
\[
0<\ln(1+t)<t.
\]
因此
\[
0<[\ln(1+t)]^n<t^n.
\]
又 \(|\ln t|>0\)，所以
\[
\int_0^1|\ln t|[\ln(1+t)]^n\,dt
<
\int_0^1t^n|\ln t|\,dt.
\]

\textbf{(2)} 由第 (1) 问，
\[
0\le u_n<\int_0^1t^n|\ln t|\,dt.
\]
而
\[
\int_0^1t^n|\ln t|\,dt
=\frac{1}{(n+1)^2}.
\]
由夹逼定理，
\[
\boxed{\lim_{n\to\infty}u_n=0}.
\]
\examnote{\(\int_0^1x^a(-\ln x)dx=1/(a+1)^2\) 是常用结论。}
\end{solutionblock}

\begin{problemblock}
\textbf{45.} 设 \(f(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内可导，且满足
\[
f(1)=k\int_0^{1/k}xe^{1-x}f(x)\,dx\qquad(k>1).
\]
证明至少存在一点 \(\xi\in(0,1)\)，使得
\[
f'(\xi)=\left(1-\frac1{\xi}\right)f(\xi).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{目标式等价于 \((xe^{-x}f(x))'=0\)，因此要证明辅助函数 \(xe^{-x}f(x)\) 在两点取同值。}
令
\[
H(x)=xe^{-x}f(x).
\]
则
\[
H'(x)=xe^{-x}\left[f'(x)+\left(\frac1x-1\right)f(x)\right].
\]
题设可写为
\[
f(1)=ke\int_0^{1/k}xe^{-x}f(x)\,dx,
\]
即
\[
H(1)=k\int_0^{1/k}H(x)\,dx.
\]
右端是 \(H\) 在 \([0,1/k]\) 上的平均值。由积分中值定理，存在
\[
\eta\in\left(0,\frac1k\right)
\]
使
\[
H(\eta)=k\int_0^{1/k}H(x)\,dx=H(1).
\]
于是 \(H\) 在 \([\eta,1]\) 上满足罗尔定理条件，存在
\[
\xi\in(\eta,1)\subset(0,1)
\]
使
\[
H'(\xi)=0.
\]
因为 \(\xi e^{-\xi}\ne0\)，得
\[
f'(\xi)+\left(\frac1\xi-1\right)f(\xi)=0,
\]
即
\[
f'(\xi)=\left(1-\frac1{\xi}\right)f(\xi).
\]
\examnote{看到 \(1-1/x\) 与 \(f\) 配合，要想到积分因子 \(xe^{-x}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{46.} 设函数 \(f(x)\) 在 \([0,3]\) 上连续，在 \((0,3)\) 内存在二阶导数，且
\[
2f(0)=\int_0^2f(x)\,dx=f(2)+f(3).
\]
\begin{enumerate}
\item 证明存在 \(\eta\in(0,2)\)，使得 \(f(\eta)=f(0)\)；
\item 证明存在 \(\xi\in(0,3)\)，使得 \(f''(\xi)=0\)。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{第一问由积分平均值推出；第二问先造出两个不同点使 \(f'\) 为零，再对 \(f'\) 用罗尔定理。}
\textbf{(1)} 由
\[
\int_0^2f(x)\,dx=2f(0),
\]
可知 \(f\) 在 \([0,2]\) 上的平均值为 \(f(0)\)。若在 \((0,2)\) 内恒有 \(f(x)>f(0)\)，则积分大于 \(2f(0)\)；若恒有 \(f(x)<f(0)\)，则积分小于 \(2f(0)\)。故必存在
\[
\eta\in(0,2)
\]
使
\[
f(\eta)=f(0).
\]

\textbf{(2)} 由 \(f(0)=f(\eta)\)，罗尔定理给出一点
\[
u\in(0,\eta)
\]
使
\[
f'(u)=0.
\]
又由
\[
f(2)+f(3)=2f(0)=2f(\eta),
\]
可知 \(f(2),f(3)\) 的平均值为 \(f(\eta)\)。因此在 \([\eta,3]\) 中可找到一点 \(v>\eta\)，使
\[
f(v)=f(\eta).
\]
对 \([\eta,v]\) 应用罗尔定理，存在
\[
w\in(\eta,v)
\]
使
\[
f'(w)=0.
\]
现在 \(u<w\)，且 \(f'(u)=f'(w)=0\)。对 \(f'\) 在 \([u,w]\) 上应用罗尔定理，存在
\[
\xi\in(u,w)\subset(0,3)
\]
使
\[
f''(\xi)=0.
\]
\examnote{证明二阶导数为零，常用“先两次罗尔得到两个 \(f'=0\) 点，再对 \(f'\) 用罗尔”。}
\end{solutionblock}

\begin{problemblock}
\textbf{47.} 设 \(f(x)\) 在 \([0,a]\ (a>0)\) 上连续，且
\[
\int_0^a f(x)\,dx=0.
\]
试证存在 \(\xi\in(0,a)\)，使得
\[
f(a-\xi)=-f(\xi).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把目标写成 \(f(\xi)+f(a-\xi)=0\)，再对这个连续函数积分。}
令
\[
F(x)=f(x)+f(a-x).
\]
则 \(F\) 在 \([0,a]\) 上连续，且
\[
\int_0^aF(x)\,dx
=\int_0^af(x)\,dx+\int_0^af(a-x)\,dx
=2\int_0^af(x)\,dx=0.
\]
若 \(F(x)\) 在 \((0,a)\) 内恒正或恒负，则其积分不可能为 \(0\)。故存在
\[
\xi\in(0,a)
\]
使
\[
F(\xi)=0.
\]
即
\[
f(\xi)+f(a-\xi)=0,
\]
所以
\[
f(a-\xi)=-f(\xi).
\]
\examnote{证明两点函数值相反，常构造和函数 \(f(x)+f(a-x)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{48.} 设 \(f(x)\) 在 \([0,1]\) 上连续，证明存在 \(\xi\in(0,1)\)，使
\[
\int_0^\xi f(t)\,dt=(1-\xi)f(\xi).
\]
若又设 \(f(x)>0\) 且单调减，则这种 \(\xi\) 是唯一的。
\end{problemblock}

\begin{solutionblock}
\analysis{存在性用罗尔定理：构造 \(H(x)=(1-x)\int_0^xf(t)dt\)，其两端值都为零。唯一性用单调性比较两个正量的商。}
令
\[
H(x)=(1-x)\int_0^xf(t)\,dt.
\]
则
\[
H(0)=H(1)=0.
\]
由罗尔定理，存在 \(\xi\in(0,1)\)，使
\[
H'(\xi)=0.
\]
而
\[
H'(x)=-(\int_0^xf(t)\,dt)+(1-x)f(x).
\]
因此
\[
\int_0^\xi f(t)\,dt=(1-\xi)f(\xi).
\]

若 \(f(x)>0\) 且单调减，令
\[
R(x)=\frac{\int_0^x f(t)\,dt}{(1-x)f(x)}\qquad(0<x<1).
\]
分子随 \(x\) 严格增加，分母 \((1-x)f(x)\) 随 \(x\) 严格减少且为正，所以 \(R(x)\) 严格增加。并且
\[
\lim_{x\to0^+}R(x)=0,\qquad \lim_{x\to1^-}R(x)=+\infty.
\]
方程 \(R(x)=1\) 因而只有一个解，故 \(\xi\) 唯一。
\examnote{存在性看端点同值的辅助函数；唯一性看单调商。}
\end{solutionblock}

\begin{problemblock}
\textbf{49.} 设 \(y=f(x)\) 是区间 \([0,1]\) 上的任一非负连续函数。
\begin{enumerate}
\item 证明存在 \(x_0\in(0,1)\)，使得
\[
x_0f(x_0)=\int_{x_0}^1f(x)\,dx;
\]
\item 设 \(f(x)\) 在 \((0,1)\) 内可导，且
\[
f'(x)>-\frac{2f(x)}{x},
\]
证明 (1) 中的 \(x_0\) 是唯一的。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{令两块面积之差为 \(H(x)=xf(x)-\int_x^1f\)。存在性由介值定理，唯一性由 \(H'(x)>0\)。}
\textbf{(1)} 令
\[
H(x)=xf(x)-\int_x^1f(t)\,dt.
\]
则 \(H\) 连续。若 \(f\equiv0\)，任取 \(x_0\in(0,1)\) 即可。下设 \(f\not\equiv0\)。由于 \(f\ge0\)，
\[
H(0)=-\int_0^1f(t)\,dt<0.
\]
又
\[
H(1)=f(1)\ge0.
\]
由介值定理，存在 \(x_0\in(0,1]\) 使 \(H(x_0)=0\)。若首次取到零在 \(1\)，由于 \(H(0)<0\) 且 \(H\) 连续，也可在靠近 \(1\) 的区间中取得所需平衡点；因此存在 \(x_0\in(0,1)\)，满足
\[
x_0f(x_0)=\int_{x_0}^1f(x)\,dx.
\]

\textbf{(2)} 对 \(H\) 求导：
\[
H'(x)=f(x)+xf'(x)+f(x)=2f(x)+xf'(x).
\]
由题设
\[
xf'(x)>-2f(x),
\]
故
\[
H'(x)>0.
\]
所以 \(H\) 在 \((0,1)\) 上严格递增，方程 \(H(x)=0\) 至多一个解。结合存在性，\(x_0\) 唯一。
\examnote{面积平衡题通常把“左面积-右面积”作为辅助函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{50.} 设函数 \(f(x)\) 在 \([0,1]\) 上有连续一阶导数，且 \(f(0)=0\)。试证至少存在一点 \(\xi\in(0,1)\)，使
\[
f'(\xi)=2\int_0^1f(x)\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把 \(\int_0^1 f\) 用 \(f'\) 表示，再用积分中值定理。}
由
\[
f(x)=\int_0^x f'(t)\,dt
\]
得
\[
\int_0^1f(x)\,dx
=\int_0^1\int_0^x f'(t)\,dt\,dx.
\]
交换积分次序：
\[
\int_0^1f(x)\,dx
=\int_0^1(1-t)f'(t)\,dt.
\]
于是
\[
2\int_0^1f(x)\,dx
=\int_0^1 2(1-t)f'(t)\,dt.
\]
权函数 \(2(1-t)\ge0\)，且
\[
\int_0^12(1-t)\,dt=1.
\]
由积分中值定理，存在 \(\xi\in(0,1)\)，使
\[
\int_0^1 2(1-t)f'(t)\,dt=f'(\xi).
\]
故
\[
f'(\xi)=2\int_0^1f(x)\,dx.
\]
\examnote{证明导数等于某个积分平均值时，把原积分改写成 \(f'\) 的加权平均。}
\end{solutionblock}

\begin{problemblock}
\textbf{51.} 设函数 \(f(x)\) 在 \([-l,l]\) 上连续，在 \(x=0\) 处可导，且 \(f'(0)\ne0\)。
\begin{enumerate}
\item 证明：对任意 \(x\in(0,l)\)，至少存在 \(\theta\in(0,1)\)，使
\[
\int_0^x f(t)\,dt+\int_0^{-x} f(t)\,dt
=x[f(\theta x)-f(-\theta x)];
\]
\item 求极限
\[
\lim_{x\to0^+}\theta.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{把左边化为 \(\int_0^x[f(t)-f(-t)]dt\)，再用积分中值定理。极限由 \(f(t)-f(-t)\sim2f'(0)t\) 得到。}
\textbf{(1)} 有
\[
\int_0^{-x}f(t)\,dt=-\int_0^x f(-s)\,ds.
\]
因此
\[
\int_0^x f(t)\,dt+\int_0^{-x} f(t)\,dt
=\int_0^x [f(t)-f(-t)]\,dt.
\]
令
\[
\varphi(t)=f(t)-f(-t).
\]
\(\varphi\) 连续。由积分中值定理，存在 \(c\in(0,x)\)，使
\[
\int_0^x\varphi(t)\,dt=x\varphi(c).
\]
令
\[
c=\theta x,\qquad 0<\theta<1,
\]
即得
\[
\int_0^x f(t)\,dt+\int_0^{-x} f(t)\,dt
=x[f(\theta x)-f(-\theta x)].
\]

\textbf{(2)} 由于 \(f\) 在 \(0\) 处可导，
\[
f(t)-f(-t)=2f'(0)t+o(t)\qquad(t\to0).
\]
于是左边
\[
\int_0^x[f(t)-f(-t)]\,dt
=f'(0)x^2+o(x^2).
\]
右边为
\[
x[f(\theta x)-f(-\theta x)]
=x[2f'(0)\theta x+o(x)]
=2f'(0)\theta x^2+o(x^2).
\]
比较主部，并利用 \(f'(0)\ne0\)，得
\[
1=2\lim_{x\to0^+}\theta.
\]
因此
\[
\boxed{\lim_{x\to0^+}\theta=\frac12}.
\]
\examnote{这种题的 \(\theta\) 极限通常来自“平均点趋向区间中点”。}
\end{solutionblock}

\begin{problemblock}
\textbf{52.} 设 \(f(x)\) 在 \([0,2\pi]\) 上具有二阶连续导数，且 \(f''(x)\ge0\)。证明：
\[
\int_0^{2\pi}f(x)\cos x\,dx\ge0.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把凸函数写成线性函数加二阶导数的积分余项。常数项和一次项与 \(\cos x\) 在整周期上积分为零，剩下核函数 \(1-\cos t\ge0\)。}
由积分型泰勒公式，
\[
f(x)=f(0)+f'(0)x+\int_0^x(x-t)f''(t)\,dt.
\]
因此
\[
\int_0^{2\pi}f(x)\cos x\,dx
=\int_0^{2\pi}\left[\int_0^x(x-t)f''(t)\,dt\right]\cos x\,dx,
\]
因为
\[
\int_0^{2\pi}\cos x\,dx=0,\qquad
\int_0^{2\pi}x\cos x\,dx=0.
\]
交换积分次序：
\[
\int_0^{2\pi}f(x)\cos x\,dx
=\int_0^{2\pi}f''(t)
\left[\int_t^{2\pi}(x-t)\cos x\,dx\right]dt.
\]
计算内层积分：
\[
\int_t^{2\pi}(x-t)\cos x\,dx
=1-\cos t.
\]
于是
\[
\int_0^{2\pi}f(x)\cos x\,dx
=\int_0^{2\pi}f''(t)(1-\cos t)\,dt.
\]
由于
\[
f''(t)\ge0,\qquad 1-\cos t\ge0,
\]
故
\[
\int_0^{2\pi}f(x)\cos x\,dx\ge0.
\]
\examnote{凸函数与三角积分结合时，可把函数分解为线性部分加非负二阶导贡献。}
\end{solutionblock}

\begin{problemblock}
\textbf{53.} 设函数 \(f(x)\) 在区间 \([0,1]\) 上可导，且 \(|f'(x)|<M\)，证明：
\[
\left|\int_0^1f(x)\,dx-\frac1n\sum_{k=1}^nf\left(\frac{k}{n}\right)\right|
\le\frac{M}{2n}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{右端和是右端点矩形和。逐小区间估计积分与右端点函数值的误差。}
将区间分成
\[
I_k=\left[\frac{k-1}{n},\frac{k}{n}\right]\qquad(k=1,\dots,n).
\]
则
\[
\int_0^1f(x)\,dx-\frac1n\sum_{k=1}^nf\left(\frac{k}{n}\right)
=\sum_{k=1}^n\int_{(k-1)/n}^{k/n}
\left[f(x)-f\left(\frac{k}{n}\right)\right]dx.
\]
对 \(x\in I_k\)，由拉格朗日中值定理，
\[
\left|f(x)-f\left(\frac{k}{n}\right)\right|
\le M\left(\frac{k}{n}-x\right).
\]
因此
\[
\left|\int_{(k-1)/n}^{k/n}
\left[f(x)-f\left(\frac{k}{n}\right)\right]dx\right|
\le M\int_{(k-1)/n}^{k/n}\left(\frac{k}{n}-x\right)dx
=\frac{M}{2n^2}.
\]
求和得
\[
\left|\int_0^1f(x)\,dx-\frac1n\sum_{k=1}^nf\left(\frac{k}{n}\right)\right|
\le n\cdot\frac{M}{2n^2}
=\frac{M}{2n}.
\]
\examnote{黎曼和误差估计常在每个小区间上用导数界控制振幅。}
\end{solutionblock}

\begin{problemblock}
\textbf{54.} 设 \(f(x)\) 满足
\[
f(1)=1,\qquad f'(x)=\frac1{x^2+f^2(x)}\quad(x\ge1).
\]
试证
\[
\lim_{x\to+\infty}f(x)
\]
存在且不超过
\[
1+\frac{\pi}{4}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{由 \(f'>0\) 知 \(f\) 单调递增；又 \(f(x)\ge1\)，所以用 \(1/(x^2+1)\) 控制导数。}
因为
\[
f'(x)=\frac1{x^2+f^2(x)}>0,
\]
所以 \(f(x)\) 在 \([1,+\infty)\) 上单调递增。又 \(f(1)=1\)，故
\[
f(x)\ge1\qquad(x\ge1).
\]
于是
\[
f'(x)=\frac1{x^2+f^2(x)}
\le \frac1{x^2+1}.
\]
对 \([1,x]\) 积分：
\[
f(x)-1
\le \int_1^x\frac{dt}{t^2+1}
\le \int_1^{+\infty}\frac{dt}{t^2+1}
=\frac{\pi}{4}.
\]
因此
\[
1\le f(x)\le1+\frac{\pi}{4}.
\]
单调有界函数极限存在，且
\[
\boxed{\lim_{x\to+\infty}f(x)\le1+\frac{\pi}{4}}.
\]
\examnote{微分方程不一定要求显式解；单调有界加导数估计即可证明极限存在。}
\end{solutionblock}

\begin{problemblock}
\textbf{55.}（数学三不要求）一容器的内侧是由图中曲线绕 \(y\) 轴旋转一周而成的曲面，该曲线由
\[
x^2+y^2=2y\quad\left(y\ge\frac12\right)
\]
与
\[
x^2+y^2=1\quad\left(y\le\frac12\right)
\]
连接而成。
\begin{enumerate}
\item 求容器的容积；
\item 若将容器内盛满的水从容器顶部全部抽出，至少需要做多少功？
\end{enumerate}
长度单位为 m，重力加速度为 \(g\,\mathrm{m/s^2}\)，水的密度为 \(10^3\,\mathrm{kg/m^3}\)。
\end{problemblock}

\begin{solutionblock}
\analysis{绕 \(y\) 轴旋转，用水平薄片。半径平方下半段为 \(1-y^2\)，上半段为 \(2y-y^2\)。}
\textbf{(1)} 容器容积
\[
V=\pi\int_{-1}^{1/2}(1-y^2)\,dy
+\pi\int_{1/2}^{2}(2y-y^2)\,dy.
\]
计算得
\[
\int_{-1}^{1/2}(1-y^2)\,dy=\frac98,\qquad
\int_{1/2}^{2}(2y-y^2)\,dy=\frac98.
\]
因此
\[
\boxed{V=\frac{9\pi}{4}\ \mathrm{m^3}}.
\]

\textbf{(2)} 顶部高度为 \(y=2\)。高度 \(y\) 处的水片体积为 \(\pi r^2dy\)，需提升距离为 \(2-y\)。故功为
\[
W=10^3g\pi\left[
\int_{-1}^{1/2}(1-y^2)(2-y)\,dy
+\int_{1/2}^{2}(2y-y^2)(2-y)\,dy
\right].
\]
两段积分分别为
\[
\int_{-1}^{1/2}(1-y^2)(2-y)\,dy=\frac{153}{64},
\]
\[
\int_{1/2}^{2}(2y-y^2)(2-y)\,dy=\frac{63}{64}.
\]
所以括号内为
\[
\frac{216}{64}=\frac{27}{8}.
\]
故
\[
\boxed{W=3375\pi g\ \mathrm{J}}.
\]
\examnote{抽水做功题固定模板：水片重量 \(\rho g A(y)dy\)，乘提升距离。}
\end{solutionblock}

\begin{problemblock}
\textbf{56.}（数学三不要求）设曲线 \(L\) 的方程为
\[
y=\frac14x^2-\frac12\ln x\qquad(1\le x\le e).
\]
\begin{enumerate}
\item 求 \(L\) 的弧长；
\item 设 \(D\) 是由曲线 \(L\)，直线 \(x=1,x=e\) 及 \(x\) 轴所围成的平面图形，求 \(D\) 的形心的横坐标。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{先求 \(y'\)，弧长根式会化成完全平方。形心横坐标为 \(\bar x=\frac{\int x y\,dx}{\int y\,dx}\)。}
\textbf{(1)} 有
\[
y'=\frac{x}{2}-\frac{1}{2x}.
\]
所以
\[
\sqrt{1+(y')^2}
=\sqrt{1+\frac{(x^2-1)^2}{4x^2}}
=\frac{x^2+1}{2x}.
\]
弧长
\[
s=\int_1^e\frac{x^2+1}{2x}\,dx
=\int_1^e\left(\frac{x}{2}+\frac{1}{2x}\right)dx
=\left[\frac{x^2}{4}+\frac12\ln x\right]_1^e.
\]
故
\[
\boxed{s=\frac{e^2+1}{4}}.
\]

\textbf{(2)} 面积
\[
A=\int_1^e\left(\frac14x^2-\frac12\ln x\right)dx
=\frac{e^3-7}{12}.
\]
关于 \(y\) 轴的矩为
\[
M_y=\int_1^e x\left(\frac14x^2-\frac12\ln x\right)dx
=\frac{e^4-2e^2-3}{16}.
\]
因此形心横坐标为
\[
\bar x=\frac{M_y}{A}
=\boxed{\frac{3(e^4-2e^2-3)}{4(e^3-7)}}.
\]
\examnote{平面图形在 \(x\) 轴上方且由 \(y=f(x)\) 围成时，\(\bar x=\frac{\int x f(x)dx}{\int f(x)dx}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{57.} 求曲线
\[
y=3-|x^2-1|
\]
与 \(x\) 轴围成的封闭图形绕直线 \(y=3\) 旋转所得的旋转体体积。
\end{problemblock}

\begin{solutionblock}
\analysis{旋转轴 \(y=3\) 在图形上方。用垂直于 \(x\) 轴的薄片，外半径为 \(3\)，内半径为 \(3-y=|x^2-1|\)。}
曲线与 \(x\) 轴交于
\[
3-|x^2-1|=0
\quad\Longrightarrow\quad
x=\pm2.
\]
在 \([-2,2]\) 上，旋转截面为圆环，外半径
\[
R=3,
\]
内半径
\[
r=3-y=|x^2-1|.
\]
体积为
\[
V=\pi\int_{-2}^{2}\left[9-(x^2-1)^2\right]dx.
\]
被积函数为偶函数，故
\[
V=2\pi\int_0^2(8+2x^2-x^4)\,dx.
\]
计算得
\[
V=2\pi\left[8x+\frac{2x^3}{3}-\frac{x^5}{5}\right]_0^2
=2\pi\left(16+\frac{16}{3}-\frac{32}{5}\right)
=\boxed{\frac{448\pi}{15}}.
\]
\examnote{绕水平直线旋转时，先判断外半径和内半径；本题外半径是到 \(x\) 轴的距离 \(3\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{58.} 设有抛物线
\[
\Gamma:\ y=a-bx^2\qquad(a>0,\ b>0).
\]
试确定常数 \(a,b\) 的值，使得：
\begin{enumerate}
\item \(\Gamma\) 与直线 \(y=x+1\) 相切；
\item \(\Gamma\) 与 \(x\) 轴所围图形绕 \(y\) 轴旋转所得旋转体体积最大。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{相切给出 \(a,b\) 的约束；体积用水平截面表示为 \(V=\pi\int_0^a x^2(y)dy\)。}
由
\[
a-bx^2=x+1
\]
得
\[
bx^2+x+1-a=0.
\]
相切要求判别式为零：
\[
1-4b(1-a)=0.
\]
因此
\[
b=\frac{1}{4(1-a)},\qquad 0<a<1.
\]
抛物线与 \(x\) 轴围成的图形绕 \(y\) 轴旋转。对固定高度 \(y\in[0,a]\)，有
\[
x^2=\frac{a-y}{b}.
\]
故体积
\[
V=\pi\int_0^a\frac{a-y}{b}\,dy
=\frac{\pi a^2}{2b}.
\]
代入 \(b=\frac{1}{4(1-a)}\)，得
\[
V=2\pi a^2(1-a).
\]
令
\[
\phi(a)=a^2(1-a),\qquad 0<a<1.
\]
则
\[
\phi'(a)=2a-3a^2=a(2-3a).
\]
最大值在
\[
a=\frac23
\]
处取得。此时
\[
b=\frac{1}{4(1-2/3)}=\frac34.
\]
故
\[
\boxed{a=\frac23,\qquad b=\frac34}.
\]
\examnote{带参数最值题先用几何条件消去一个参数，再对剩余参数求最值。}
\end{solutionblock}

\begin{problemblock}
\textbf{59.} 设曲线 \(y=1/x\) 与直线 \(y=x\) 及 \(y=2\) 所围区域为 \(D\)。
\begin{enumerate}
\item 求区域 \(D\) 分别绕 \(x\) 轴和 \(y\) 轴旋转所得旋转体的体积；
\item 求区域 \(D\) 分别绕 \(x=2\) 和 \(y=2\) 旋转所得旋转体的体积。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{用水平切片最统一。区域可写成 \(1\le y\le2,\ 1/y\le x\le y\)。}
区域 \(D\) 为
\[
1\le y\le2,\qquad \frac1y\le x\le y.
\]
\textbf{(1)} 绕 \(x\) 轴旋转，用壳层法：
\[
V_x=2\pi\int_1^2 y\left(y-\frac1y\right)dy
=2\pi\int_1^2(y^2-1)dy
=\boxed{\frac{8\pi}{3}}.
\]
绕 \(y\) 轴旋转，用圆环法：
\[
V_y=\pi\int_1^2\left[y^2-\left(\frac1y\right)^2\right]dy
=\boxed{\frac{11\pi}{6}}.
\]

\textbf{(2)} 绕 \(x=2\) 旋转。外半径为 \(2-\frac1y\)，内半径为 \(2-y\)，故
\[
V_{x=2}
=\pi\int_1^2\left[\left(2-\frac1y\right)^2-(2-y)^2\right]dy.
\]
计算得
\[
V_{x=2}
=\boxed{\pi\left(\frac{25}{6}-4\ln2\right)}.
\]
绕 \(y=2\) 旋转，用竖直切片：
\[
V_{y=2}
=\pi\int_{1/2}^{1}\left(2-\frac1x\right)^2dx
+\pi\int_1^2(2-x)^2dx.
\]
因此
\[
V_{y=2}
=\boxed{\pi\left(\frac{10}{3}-4\ln2\right)}.
\]
\examnote{旋转轴换成 \(x=2\)、\(y=2\) 后，半径必须改成到新轴的距离，不能沿用到坐标轴的半径。}
\end{solutionblock}

\begin{problemblock}
\textbf{60.} 求曲线 \(y=x^2\) 与直线 \(y=x\) 所围区域 \(D\) 绕直线 \(y=x\) 旋转一周所得旋转体的体积。
\end{problemblock}

\begin{solutionblock}
\analysis{旋转轴是区域边界 \(y=x\)。用帕普斯定理或“面积元到轴距离”积分：\(dV=2\pi d\,dA\)。}
区域为
\[
0\le x\le1,\qquad x^2\le y\le x.
\]
点 \((x,y)\) 到直线 \(y=x\) 的距离为
\[
d=\frac{x-y}{\sqrt2}.
\]
旋转体体积为
\[
V=2\pi\iint_D d\,dA
=\sqrt2\pi\int_0^1\int_{x^2}^{x}(x-y)\,dy\,dx.
\]
内层积分为
\[
\int_{x^2}^{x}(x-y)\,dy
=\frac{x^2}{2}-x^3+\frac{x^4}{2}.
\]
所以
\[
V=\sqrt2\pi\int_0^1\left(\frac{x^2}{2}-x^3+\frac{x^4}{2}\right)dx
=\sqrt2\pi\left(\frac16-\frac14+\frac1{10}\right).
\]
故
\[
\boxed{V=\frac{\sqrt2\pi}{60}}.
\]
\examnote{绕斜直线旋转时，距离公式比硬换坐标更快。}
\end{solutionblock}

\begin{problemblock}
\textbf{61.} 设平面域 \(D\) 由曲线
\[
r=1+\cos\theta
\]
所围成，试求：
\begin{enumerate}
\item 区域 \(D\) 的面积；
\item 区域 \(D\) 绕极轴旋转一周所得旋转体的体积。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{面积用极坐标面积公式；绕极轴旋转只需取上半部分，用壳层法。}
\textbf{(1)} 面积为
\[
S=\frac12\int_0^{2\pi}(1+\cos\theta)^2\,d\theta.
\]
展开得
\[
S=\frac12\int_0^{2\pi}(1+2\cos\theta+\cos^2\theta)d\theta
=\frac12(2\pi+\pi)
=\boxed{\frac{3\pi}{2}}.
\]

\textbf{(2)} 取上半部分 \(0\le\theta\le\pi\)。极坐标中面积元为 \(\rho\,d\rho\,d\theta\)，到极轴距离为 \(\rho\sin\theta\)。旋转体体积
\[
V=2\pi\int_0^\pi\int_0^{1+\cos\theta}
(\rho\sin\theta)\rho\,d\rho\,d\theta.
\]
故
\[
V=\frac{2\pi}{3}\int_0^\pi(1+\cos\theta)^3\sin\theta\,d\theta.
\]
令 \(u=1+\cos\theta\)，得
\[
\int_0^\pi(1+\cos\theta)^3\sin\theta\,d\theta
=\int_0^2u^3\,du=4.
\]
所以
\[
\boxed{V=\frac{8\pi}{3}}.
\]
\examnote{极坐标绕极轴旋转，常用 \(V=2\pi\iint_{\text{上半域}} y\,dA\)。}
\end{solutionblock}

\section{第三章完成说明}
第三章第 \(1\)--\(61\) 题已按“题目解析、完整推导、答案、考研提示”的格式整理完毕。
"""


CH04_TEX = r"""\chapter{常微分方程}

\section{原题页索引}
本章原题对应做题本第 \(63\)--\(75\) 页。本节先完成第 \(1\)--\(15\) 题详细解析。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_063.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 已知函数 \(y=y(x)\) 在任意点处的增量
\[
\Delta y=\frac{y\Delta x}{1+x^2}+\alpha,
\]
且当 \(\Delta x\to0\) 时，\(\alpha\) 是 \(\Delta x\) 的高阶无穷小，\(y(0)=\pi\)，求 \(y(1)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{由增量式取极限可得到微分方程。}
由题设
\[
\frac{\Delta y}{\Delta x}=\frac{y}{1+x^2}+\frac{\alpha}{\Delta x}.
\]
令 \(\Delta x\to0\)，由于 \(\alpha=o(\Delta x)\)，得
\[
y'=\frac{y}{1+x^2}.
\]
分离变量：
\[
\frac{dy}{y}=\frac{dx}{1+x^2}.
\]
积分得
\[
\ln|y|=\arctan x+C,
\qquad y=Ce^{\arctan x}.
\]
由 \(y(0)=\pi\)，得 \(C=\pi\)。所以
\[
y(1)=\pi e^{\arctan1}=\boxed{\pi e^{\pi/4}}.
\]
\[
\boxed{\text{D}}
\]
\examnote{增量式中“高阶无穷小”就是在提示你两边除以 \(\Delta x\) 后取极限。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 方程
\[
y''+2y'+y=3xe^{-x}
\]
的特解形式为哪一项？
\end{problemblock}

\begin{solutionblock}
\analysis{左端特征方程为 \((r+1)^2=0\)，右端是一次多项式乘 \(e^{-x}\)，且 \(-1\) 是二重根。}
因为
\[
r^2+2r+1=(r+1)^2,
\]
所以 \(-1\) 是二重特征根。右端为
\[
3xe^{-x}.
\]
按待定系数法，若 \(\lambda=-1\) 是二重根，特解应乘 \(x^2\)，且多项式次数为 \(1\)。故可设
\[
y^*=(Ax+B)x^2e^{-x}.
\]
\[
\boxed{\text{D}}
\]
\examnote{右端 \(P_m(x)e^{\lambda x}\)，若 \(\lambda\) 是 \(s\) 重特征根，特解前乘 \(x^s\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 具有特解
\[
y_1=e^{-x},\qquad y_2=2xe^{-x},\qquad y_3=3e^x
\]
的三阶常系数齐次线性微分方程是哪一个？
\end{problemblock}

\begin{solutionblock}
\analysis{\(e^{-x}\) 与 \(xe^{-x}\) 表明 \(-1\) 是二重根，\(e^x\) 表明 \(1\) 是一重根。}
特征根为
\[
r=-1\quad(\text{二重}),\qquad r=1.
\]
特征多项式
\[
(r+1)^2(r-1)=r^3+r^2-r-1.
\]
故微分方程为
\[
y'''+y''-y'-y=0.
\]
\[
\boxed{\text{B}}
\]
\examnote{出现 \(xe^{\lambda x}\) 时，说明 \(\lambda\) 至少是二重根。}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 微分方程
\[
y''-4y'+8y=e^{2x}(1+\cos2x)
\]
的特解可设为何种形式？
\end{problemblock}

\begin{solutionblock}
\analysis{分别处理 \(e^{2x}\) 与 \(e^{2x}\cos2x\)。特征根为 \(2\pm2i\)。}
特征方程
\[
r^2-4r+8=0
\]
的根为
\[
r=2\pm2i.
\]
右端第一项 \(e^{2x}\) 中 \(\lambda=2\) 不是特征根，故对应特解可设 \(Ae^{2x}\)。

右端第二项 \(e^{2x}\cos2x\) 对应复指数 \(e^{(2+2i)x}\)，正好与特征根重合一次，故应乘 \(x\)。所以特解可设
\[
y^*=Ae^{2x}+xe^{2x}(B\cos2x+C\sin2x).
\]
\[
\boxed{\text{C}}
\]
\examnote{三角非齐次项要看复根 \(\alpha\pm i\beta\) 是否与特征根重合。}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 函数
\[
y=C_1e^x+C_2e^{-2x}+xe^x
\]
满足的一个微分方程是哪一个？
\end{problemblock}

\begin{solutionblock}
\analysis{齐次部分给出特征根 \(1,-2\)，所以左端算子是 \(D^2+D-2\)。再代入 \(xe^x\) 求右端。}
由齐次部分可知特征多项式为
\[
(r-1)(r+2)=r^2+r-2.
\]
故左端为
\[
y''+y'-2y.
\]
对特解 \(y_p=xe^x\)，有
\[
(D^2+D-2)(xe^x)=3e^x.
\]
因此满足
\[
y''+y'-2y=3e^x.
\]
\[
\boxed{\text{D}}
\]
\examnote{由通解反推方程时，先从齐次通解确定特征多项式。}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 下列微分方程中，以
\[
y=C_1e^x+C_2\cos2x+C_3\sin2x
\]
为通解的是哪一个？
\end{problemblock}

\begin{solutionblock}
\analysis{通解对应特征根 \(1,2i,-2i\)。}
特征多项式为
\[
(r-1)(r^2+4)=r^3-r^2+4r-4.
\]
故方程为
\[
y'''-y''+4y'-4y=0.
\]
\[
\boxed{\text{D}}
\]
\examnote{\(\cos\beta x,\sin\beta x\) 对应特征根 \(\pm i\beta\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 微分方程
\[
y''-\lambda^2y=e^{\lambda x}+e^{-\lambda x}\qquad(\lambda>0)
\]
的特解形式为哪一项？
\end{problemblock}

\begin{solutionblock}
\analysis{齐次特征根为 \(\pm\lambda\)，右端两个指数项均与齐次解重复。}
特征方程为
\[
r^2-\lambda^2=0,
\]
故
\[
r=\lambda,\ -\lambda.
\]
右端 \(e^{\lambda x}\) 和 \(e^{-\lambda x}\) 都对应齐次解中的指数项，所以特解都要乘 \(x\)。因此可设
\[
y^*=x(ae^{\lambda x}+be^{-\lambda x}).
\]
\[
\boxed{\text{C}}
\]
\examnote{若右端每一项都共振，每一项都要按自己的重数乘 \(x\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 方程
\[
x\ln x\,dy+(y-\ln x)\,dx=0
\]
满足初始条件 \(y|_{x=e}=1\) 的特解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{化为一阶线性方程 \(y'+P(x)y=Q(x)\)。}
原方程化为
\[
x\ln x\,y'+y-\ln x=0,
\]
即
\[
y'+\frac{1}{x\ln x}y=\frac1x.
\]
积分因子为
\[
\mu(x)=e^{\int\frac{dx}{x\ln x}}=\ln x.
\]
于是
\[
(y\ln x)'=\frac{\ln x}{x}.
\]
积分得
\[
y\ln x=\frac12(\ln x)^2+C.
\]
由 \(y(e)=1\)，得
\[
1=\frac12+C,\qquad C=\frac12.
\]
故
\[
\boxed{y=\frac{(\ln x)^2+1}{2\ln x}}.
\]
\examnote{一阶线性方程的积分因子是 \(e^{\int P(x)dx}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 微分方程
\[
(y+x^3)\,dx-2x\,dy=0
\]
满足 \(y|_{x=1}=6/5\) 的特解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{整理为一阶线性方程。}
由题设
\[
2x y'=y+x^3,
\]
即
\[
y'-\frac{1}{2x}y=\frac{x^2}{2}.
\]
积分因子
\[
\mu(x)=e^{\int-\frac{1}{2x}dx}=x^{-1/2}.
\]
于是
\[
(yx^{-1/2})'=\frac12x^{3/2}.
\]
积分得
\[
yx^{-1/2}=\frac15x^{5/2}+C.
\]
所以
\[
y=\frac{x^3}{5}+C\sqrt{x}.
\]
由 \(y(1)=6/5\)，得 \(C=1\)。故
\[
\boxed{y=\frac{x^3}{5}+\sqrt{x}}.
\]
\examnote{含 \(dy\) 的微分方程先化为 \(dy/dx\) 形式，再判断类型。}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 方程
\[
\left(1+e^{-x/y}\right)y\,dx+(y-x)\,dy=0
\]
的通解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{这是齐次型方程，令 \(x=vy\)，把 \(x/y\) 化为 \(v\)。}
令
\[
x=vy,\qquad dx=v\,dy+y\,dv.
\]
代入原方程：
\[
y(1+e^{-v})(v\,dy+y\,dv)+y(1-v)\,dy=0.
\]
整理得
\[
y(1+e^{-v})\,dv+(1+ve^{-v})\,dy=0.
\]
因此
\[
\frac{dy}{y}=-\frac{1+e^{-v}}{1+ve^{-v}}\,dv
=-\frac{e^v+1}{e^v+v}\,dv.
\]
积分得
\[
\ln y+\ln(e^v+v)=C.
\]
即
\[
y(e^{x/y}+x/y)=C.
\]
故通解可写为
\[
\boxed{x+ye^{x/y}=C}.
\]
\examnote{出现 \(x/y\) 的微分方程，优先尝试齐次换元 \(x=vy\) 或 \(y=vx\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 已知方程
\[
y''+ay'+by=0
\]
的通解为
\[
y=C_1e^x+C_2e^{-x}.
\]
求方程
\[
y''+ay'+by=e^2
\]
满足初始条件
\[
y(0)=0,\qquad y'(0)=\frac32
\]
的特解。
\end{problemblock}

\begin{solutionblock}
\analysis{齐次根为 \(\pm1\)，所以 \(a=0,b=-1\)。右端是常数。}
由通解得特征根为 \(1,-1\)，故齐次方程为
\[
y''-y=0.
\]
非齐次方程为
\[
y''-y=e^2.
\]
取常数特解 \(y_p=-e^2\)。故
\[
y=C_1e^x+C_2e^{-x}-e^2.
\]
由 \(y(0)=0\)，得
\[
C_1+C_2=e^2.
\]
由 \(y'(0)=3/2\)，得
\[
C_1-C_2=\frac32.
\]
解得
\[
C_1=\frac{e^2}{2}+\frac34,\qquad
C_2=\frac{e^2}{2}-\frac34.
\]
所以
\[
\boxed{
y=\left(\frac{e^2}{2}+\frac34\right)e^x
\left(\frac{e^2}{2}-\frac34\right)e^{-x}
-e^2 }.
\]
\examnote{先由齐次通解还原 \(a,b\)，再求非齐次特解。}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 方程
\[
y''+y=x+\cos x
\]
的通解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{右端分成 \(x\) 和 \(\cos x\)。其中 \(\cos x\) 与齐次解共振。}
齐次方程
\[
y''+y=0
\]
的通解为
\[
y_h=C_1\cos x+C_2\sin x.
\]
对右端 \(x\)，可取特解
\[
y_{p1}=x.
\]
对右端 \(\cos x\)，由于 \(\cos x\) 是齐次解，取
\[
y_{p2}=Ax\sin x.
\]
代入 \(y''+y=\cos x\) 得
\[
2A\cos x=\cos x,
\qquad A=\frac12.
\]
故通解为
\[
\boxed{y=C_1\cos x+C_2\sin x+x+\frac{x}{2}\sin x}.
\]
\examnote{右端与齐次解重复时，特解乘 \(x\) 消重。}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 设函数 \(y(x)\) 满足
\[
y''+(x-1)y'+x^2y=e^x,\qquad y'(0)=1.
\]
若
\[
\lim_{x\to0}\frac{y(x)-x}{x^2}=a,
\]
求 \(a\)。
\end{problemblock}

\begin{solutionblock}
\analysis{极限存在说明 \(y(0)=0\)，且二阶系数就是 \(y''(0)/2\)。}
由
\[
\frac{y(x)-x}{x^2}
\]
极限存在，必须有
\[
y(0)=0.
\]
又题设给出 \(y'(0)=1\)。把 \(x=0\) 代入微分方程：
\[
y''(0)+(0-1)y'(0)+0=e^0.
\]
即
\[
y''(0)-1=1,
\qquad y''(0)=2.
\]
而
\[
y(x)=y(0)+y'(0)x+\frac12y''(0)x^2+o(x^2)
=x+x^2+o(x^2).
\]
因此
\[
a=\boxed{1}.
\]
\examnote{含 \(\lim (y-x)/x^2\) 的题，实质是在问泰勒展开的二阶系数。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 二阶常系数非齐次线性微分方程
\[
y''-4y'+3y=2e^{2x}
\]
的通解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{先求齐次通解，再用待定系数法求指数特解。}
特征方程
\[
r^2-4r+3=0
\]
有根
\[
r=1,\quad r=3.
\]
故
\[
y_h=C_1e^x+C_2e^{3x}.
\]
设特解
\[
y_p=Ae^{2x}.
\]
代入得
\[
(4-8+3)Ae^{2x}=2e^{2x},
\]
即
\[
-A=2,\qquad A=-2.
\]
所以通解为
\[
\boxed{y=C_1e^x+C_2e^{3x}-2e^{2x}}.
\]
\examnote{若 \(2\) 不是特征根，指数特解直接设 \(Ae^{2x}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 三阶常系数线性齐次微分方程
\[
y'''-2y''+y'-2y=0
\]
的通解为多少？
\end{problemblock}

\begin{solutionblock}
\analysis{分解特征多项式。}
特征方程为
\[
r^3-2r^2+r-2=0.
\]
分组分解：
\[
r^3-2r^2+r-2
=r^2(r-2)+(r-2)
=(r^2+1)(r-2).
\]
故特征根为
\[
r=2,\quad r=\pm i.
\]
所以通解为
\[
\boxed{y=C_1e^{2x}+C_2\cos x+C_3\sin x}.
\]
\examnote{三阶常系数齐次方程，核心就是特征多项式分解。}
\end{solutionblock}

\section{编号说明}
原书第四章页图中第 \(15\) 题后直接接第 \(18\) 题，未出现第 \(16,17\) 题。以下按原书编号继续。

\begin{problemblock}
\textbf{18.} 设函数 \(y=y(x)\) 满足微分方程
\[
y''-3y'+2y=2e^x,
\]
且其图形在点 \((0,1)\) 处的切线与曲线
\[
y=x^2-x+1
\]
在该点的切线重合，求函数 \(y=y(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{切线重合给出初值 \(y(0)=1,\ y'(0)=-1\)。再解二阶常系数非齐次方程。}
曲线 \(y=x^2-x+1\) 在 \(x=0\) 处导数为
\[
y'=2x-1,\qquad y'(0)=-1.
\]
故所求函数满足
\[
y(0)=1,\qquad y'(0)=-1.
\]
齐次方程
\[
y''-3y'+2y=0
\]
的特征根为
\[
r=1,\quad r=2.
\]
右端 \(2e^x\) 与根 \(r=1\) 共振，设特解
\[
y_p=Axe^x.
\]
代入得
\[
(D^2-3D+2)(Axe^x)=-Ae^x=2e^x,
\]
所以
\[
A=-2.
\]
通解为
\[
y=C_1e^x+C_2e^{2x}-2xe^x.
\]
由 \(y(0)=1\)，得
\[
C_1+C_2=1.
\]
由
\[
y'=C_1e^x+2C_2e^{2x}-2e^x-2xe^x,
\]
代入 \(x=0\) 得
\[
C_1+2C_2-2=-1,
\]
即
\[
C_1+2C_2=1.
\]
解得
\[
C_2=0,\qquad C_1=1.
\]
故
\[
\boxed{y=(1-2x)e^x}.
\]
\examnote{“切线重合”通常同时给函数值和导数值两个初始条件。}
\end{solutionblock}

\begin{problemblock}
\textbf{19.} 已知
\[
y_1=3,\qquad y_2=3+x^2,\qquad y_3=3+e^x
\]
是某二阶线性非齐次方程的三个特解，求该微分方程及通解。
\end{problemblock}

\begin{solutionblock}
\analysis{非齐次方程任意两个特解之差是对应齐次方程的解。因此 \(x^2,e^x\) 是齐次方程的两个线性无关解。}
设齐次方程为
\[
y''+P(x)y'+Q(x)y=0.
\]
因为
\[
y_2-y_1=x^2,\qquad y_3-y_1=e^x,
\]
所以 \(x^2\) 和 \(e^x\) 是齐次方程的两个解。

代入 \(y=x^2\)：
\[
2+2xP+x^2Q=0.
\]
代入 \(y=e^x\)：
\[
1+P+Q=0.
\]
解得
\[
P(x)=\frac{x^2-2}{x(2-x)},\qquad
Q(x)=\frac{2(1-x)}{x(2-x)}.
\]
由于 \(y=3\) 是非齐次方程的一个特解，右端为
\[
3Q(x)=\frac{6(1-x)}{x(2-x)}.
\]
故一个微分方程可写为
\[
y''+\frac{x^2-2}{x(2-x)}y'
+\frac{2(1-x)}{x(2-x)}y
=\frac{6(1-x)}{x(2-x)}.
\]
等价地，两边乘 \(x(2-x)\)，得
\[
\boxed{x(2-x)y''+(x^2-2)y'+2(1-x)y=6(1-x)}.
\]
其通解为
\[
\boxed{y=3+C_1x^2+C_2e^x}.
\]
\examnote{“多个非齐次特解”题的核心：特解之差属于齐次解空间。}
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 求微分方程
\[
y''+(x+e^{2y})(y')^3=0
\]
的通解。
\end{problemblock}

\begin{solutionblock}
\analysis{方程中 \(x\) 和 \(y\) 的位置提示把 \(x\) 看成 \(y\) 的函数。利用
\[
\frac{d^2x}{dy^2}=-\frac{y''}{(y')^3}.
\]}
设 \(x=x(y)\)。则
\[
\frac{d^2x}{dy^2}=-\frac{y''}{(y')^3}.
\]
由原方程
\[
y''=-(x+e^{2y})(y')^3,
\]
得
\[
\frac{d^2x}{dy^2}=x+e^{2y}.
\]
即
\[
x''-x=e^{2y}.
\]
这是关于 \(x(y)\) 的二阶常系数非齐次方程。齐次解为
\[
x_h=C_1e^y+C_2e^{-y}.
\]
设特解
\[
x_p=Ae^{2y}.
\]
代入得
\[
(4-1)Ae^{2y}=e^{2y},
\]
所以
\[
A=\frac13.
\]
故通解为
\[
\boxed{x=C_1e^y+C_2e^{-y}+\frac13e^{2y}}.
\]
\examnote{含 \((y')^3\) 与 \(y''\) 的方程，常尝试把 \(x\) 反过来看成 \(y\) 的函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 设函数 \(f(x)\) 具有连续的一阶导数，且满足
\[
f(x)=\int_0^x(x^2-t^2)f'(t)\,dt+x^2.
\]
求 \(f(x)\) 的表达式。
\end{problemblock}

\begin{solutionblock}
\analysis{对积分方程求导，利用变上限处 \(x^2-x^2=0\) 消去边界项。}
令 \(x=0\)，得
\[
f(0)=0.
\]
对原式求导：
\[
f'(x)=\int_0^x2x f'(t)\,dt+2x.
\]
由于
\[
\int_0^x f'(t)\,dt=f(x)-f(0)=f(x),
\]
所以
\[
f'(x)=2xf(x)+2x.
\]
即
\[
f'-2xf=2x.
\]
积分因子为
\[
e^{-x^2}.
\]
于是
\[
(fe^{-x^2})'=2xe^{-x^2}.
\]
积分得
\[
fe^{-x^2}=-e^{-x^2}+C.
\]
由 \(f(0)=0\)，得 \(C=1\)。故
\[
\boxed{f(x)=e^{x^2}-1}.
\]
\examnote{变限积分方程通常通过求导化为微分方程。}
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 设 \(f(x)\) 连续，且满足
\[
\int_0^x f(t)\,dt=x+\int_0^x t f(x-t)\,dt.
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{把卷积项换元，设 \(F(x)=\int_0^xf(t)dt\)。}
令
\[
F(x)=\int_0^xf(t)\,dt.
\]
则
\[
\int_0^x t f(x-t)\,dt
=\int_0^x (x-u)f(u)\,du
=xF(x)-\int_0^x u f(u)\,du.
\]
原式为
\[
F(x)=x+xF(x)-\int_0^x u f(u)\,du.
\]
两边求导：
\[
F'(x)=1+F(x)+xF'(x)-xF'(x)=1+F(x).
\]
又 \(F(0)=0\)，故
\[
F'=F+1.
\]
解得
\[
F(x)=e^x-1.
\]
所以
\[
\boxed{f(x)=F'(x)=e^x}.
\]
\examnote{卷积 \(\int_0^x t f(x-t)dt\) 换元后往往能转成 \(F\) 与另一个积分的组合。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 设 \(f(x)\) 为连续函数，且满足
\[
f(x)=e^x+e^x\int_0^x[f(t)]^2\,dt.
\]
试求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{设 \(u=e^{-x}f(x)\)，可把积分方程化为可分离微分方程。}
由题设
\[
e^{-x}f(x)=1+\int_0^x[f(t)]^2\,dt.
\]
令
\[
u(x)=e^{-x}f(x).
\]
则
\[
u(0)=f(0)=1,
\]
且
\[
u'(x)=f^2(x)=e^{2x}u^2(x).
\]
分离变量：
\[
\frac{du}{u^2}=e^{2x}\,dx.
\]
积分得
\[
-\frac1u=\frac12e^{2x}+C.
\]
由 \(u(0)=1\)，得
\[
-1=\frac12+C,\qquad C=-\frac32.
\]
因此
\[
\frac1u=\frac{3-e^{2x}}{2},
\qquad
u=\frac{2}{3-e^{2x}}.
\]
故
\[
\boxed{f(x)=\frac{2e^x}{3-e^{2x}}}.
\]
\examnote{等式两边都有 \(e^x\) 时，先除以 \(e^x\) 通常能简化结构。}
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 函数 \(f(x)\) 在 \([0,+\infty)\) 上可导，\(f(0)=1\)，且满足
\[
f'(x)+f(x)-\frac{1}{x+1}\int_0^x f(t)\,dt=0.
\]
\begin{enumerate}
\item 求导数 \(f'(x)\)；
\item 证明：当 \(x\ge0\) 时，
\[
e^{-x}\le f(x)\le1.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{设 \(F(x)=\int_0^xf(t)dt\)，先把原式写成 \(f'+f=F/(x+1)\)，再求导得到关于 \(f'\) 的一阶方程。}
令
\[
F(x)=\int_0^xf(t)\,dt.
\]
题设为
\[
f'(x)+f(x)=\frac{F(x)}{x+1}.
\]
令 \(x=0\)，得
\[
f'(0)+f(0)=0,\qquad f'(0)=-1.
\]
对
\[
f'+f=\frac{F}{x+1}
\]
两边求导：
\[
f''+f'=\frac{(x+1)f-F}{(x+1)^2}.
\]
又
\[
F=(x+1)(f'+f),
\]
故
\[
f''+f'=-\frac{f'}{x+1}.
\]
令 \(g=f'\)，则
\[
g'+\left(1+\frac{1}{x+1}\right)g=0.
\]
解得
\[
g=\frac{Ce^{-x}}{x+1}.
\]
由 \(g(0)=f'(0)=-1\)，得 \(C=-1\)。所以
\[
\boxed{f'(x)=-\frac{e^{-x}}{x+1}}.
\]

由 \(f'(x)\le0\)，知 \(f\) 单调不增，所以
\[
f(x)\le f(0)=1.
\]
再令
\[
h(x)=f(x)-e^{-x}.
\]
则
\[
h(0)=0,
\]
且
\[
h'(x)=f'(x)+e^{-x}
=-\frac{e^{-x}}{x+1}+e^{-x}
=\frac{x}{x+1}e^{-x}\ge0.
\]
所以 \(h(x)\ge0\)，即
\[
f(x)\ge e^{-x}.
\]
综上
\[
\boxed{e^{-x}\le f(x)\le1\quad(x\ge0)}.
\]
\examnote{含 \(\int_0^x f\) 的方程设 \(F\) 后，常通过再求导降为常微分方程。}
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 设 \(f(x)\) 连续，且
\[
f(t)=\iint_{x^2+y^2\le t} f(x^2+y^2)\,dxdy+t^4\qquad(t\ge0).
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{圆域积分改用极坐标，令 \(u=r^2\)，可转化为一阶线性微分方程。}
用极坐标：
\[
\iint_{x^2+y^2\le t} f(x^2+y^2)\,dxdy
=2\pi\int_0^{\sqrt t}f(r^2)r\,dr.
\]
令 \(u=r^2\)，得
\[
2\pi\int_0^{\sqrt t}f(r^2)r\,dr
=\pi\int_0^t f(u)\,du.
\]
所以
\[
f(t)=\pi\int_0^t f(u)\,du+t^4.
\]
令 \(t=0\)，得 \(f(0)=0\)。两边求导：
\[
f'(t)=\pi f(t)+4t^3.
\]
即
\[
f'-\pi f=4t^3,\qquad f(0)=0.
\]
解得
\[
f(t)=\frac{24}{\pi^4}\left(e^{\pi t}-1-\pi t-\frac{\pi^2t^2}{2}-\frac{\pi^3t^3}{6}\right).
\]
因此
\[
\boxed{
f(x)=\frac{24}{\pi^4}\left(e^{\pi x}-1-\pi x-\frac{\pi^2x^2}{2}-\frac{\pi^3x^3}{6}\right)}.
\]
\examnote{二重积分中被积函数只含 \(x^2+y^2\)，通常立刻转极坐标。}
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 设 \(f(x)\) 在 \((-\infty,+\infty)\) 上有定义，\(f'(0)=2\)，对任意 \(x,y\) 有
\[
f(x+y)=e^x f(y)+e^y f(x).
\]
求 \(f(x)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{先令 \(y=0\) 得 \(f(0)=0\)，再对 \(y\) 在 \(0\) 处求导。}
令 \(y=0\)，得
\[
f(x)=e^x f(0)+f(x),
\]
故
\[
f(0)=0.
\]
对恒等式关于 \(y\) 在 \(y=0\) 处求导：
\[
f'(x)=e^x f'(0)+e^0 f(x).
\]
由 \(f'(0)=2\)，得
\[
f'=f+2e^x.
\]
即
\[
f'-f=2e^x,\qquad f(0)=0.
\]
乘积分因子 \(e^{-x}\)：
\[
(fe^{-x})'=2.
\]
积分得
\[
fe^{-x}=2x+C.
\]
由 \(f(0)=0\)，得 \(C=0\)。故
\[
\boxed{f(x)=2xe^x}.
\]
\examnote{函数方程含任意 \(x,y\)，常令一个变量为 \(0\)，再对另一个变量在特殊点求导。}
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 设 \(f(x)\) 在 \([1,+\infty)\) 上有连续二阶导数，\(f(1)=0,\ f'(1)=1\)，且
\[
z=(x^2+y^2)f(x^2+y^2)
\]
满足
\[
\frac{\partial^2z}{\partial x^2}+\frac{\partial^2z}{\partial y^2}=0.
\]
求 \(f(x)\) 在 \([1,+\infty)\) 上的最大值。
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(s=x^2+y^2\)，把 \(z\) 看成径向函数 \(\phi(s)=sf(s)\)。二维拉普拉斯算子给出 \(s\phi''+\phi'=0\)。}
令
\[
s=x^2+y^2,\qquad \phi(s)=sf(s).
\]
对径向函数 \(z=\phi(s)\)，有
\[
\frac{\partial^2z}{\partial x^2}+\frac{\partial^2z}{\partial y^2}
=4[s\phi''(s)+\phi'(s)].
\]
题设给出
\[
s\phi''(s)+\phi'(s)=0,
\]
即
\[
(s\phi'(s))'=0.
\]
所以
\[
\phi'(s)=\frac{C}{s},
\qquad
\phi(s)=C\ln s+D.
\]
由
\[
\phi(1)=1\cdot f(1)=0
\]
得 \(D=0\)。又
\[
\phi'(s)=f(s)+sf'(s),
\]
故
\[
\phi'(1)=f(1)+f'(1)=1.
\]
于是 \(C=1\)，
\[
\phi(s)=\ln s.
\]
因此
\[
f(s)=\frac{\ln s}{s}.
\]
令
\[
F(s)=\frac{\ln s}{s}\qquad(s\ge1).
\]
则
\[
F'(s)=\frac{1-\ln s}{s^2}.
\]
最大值在
\[
\ln s=1,\qquad s=e
\]
处取得，最大值为
\[
\boxed{\frac1e}.
\]
\examnote{径向调和函数题，记住 \(u=\phi(r^2)\) 时 \(\Delta u=4(s\phi''+\phi')\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 设函数 \(u(x,y)\) 的全微分
\[
du=\bigl(e^x+f''(x)y\bigr)\,dx+f(x)\,dy,
\]
其中 \(f\) 具有二阶连续导数，且
\[
f(0)=4,\qquad f'(0)=3.
\]
求 \(f(x)\) 及 \(u(x,y)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{全微分存在要求混合偏导相等，即 \(\partial M/\partial y=\partial N/\partial x\)。}
记
\[
M=e^x+f''(x)y,\qquad N=f(x).
\]
因为 \(du=Mdx+Ndy\) 是全微分，所以
\[
\frac{\partial M}{\partial y}=\frac{\partial N}{\partial x}.
\]
即
\[
f''(x)=f'(x).
\]
解得
\[
f'(x)=Ce^x,\qquad f(x)=Ce^x+D.
\]
由
\[
f'(0)=3
\]
得 \(C=3\)。由
\[
f(0)=4
\]
得 \(3+D=4\)，故 \(D=1\)。所以
\[
\boxed{f(x)=3e^x+1}.
\]
此时
\[
du=(e^x+3e^xy)\,dx+(3e^x+1)\,dy.
\]
先对 \(y\) 积分：
\[
u=(3e^x+1)y+\varphi(x).
\]
再对 \(x\) 求偏导：
\[
u_x=3e^xy+\varphi'(x).
\]
与 \(M=e^x+3e^xy\) 比较，得
\[
\varphi'(x)=e^x,\qquad \varphi(x)=e^x+C.
\]
故
\[
\boxed{u(x,y)=(3e^x+1)y+e^x+C}.
\]
\examnote{全微分题先用 \(\partial M/\partial y=\partial N/\partial x\)，再积分还原势函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 求过点 \((0,2)\) 的曲线 \(y=y(x)\)，使曲线上任一点 \(P\) 的法线段 \(PQ\) 的中点位于抛物线
\[
2y^2=x
\]
上，其中 \(Q\) 是过 \(P\) 点作曲线法线与 \(x\) 轴的交点。
\end{problemblock}

\begin{solutionblock}
\analysis{设 \(P(x,y)\)，切线斜率为 \(y'\)。法线与 \(x\) 轴交点可由法线方程求出。}
法线斜率为 \(-1/y'\)。法线方程为
\[
Y-y=-\frac1{y'}(X-x).
\]
令 \(Y=0\)，得
\[
X_Q=x+yy'.
\]
所以 \(Q=(x+yy',0)\)。中点为
\[
\left(x+\frac{yy'}2,\frac y2\right).
\]
该点在 \(2y^2=x\) 上，即
\[
x+\frac{yy'}2=2\left(\frac y2\right)^2=\frac{y^2}{2}.
\]
故
\[
yy'=y^2-2x.
\]
令 \(z=y^2\)，则
\[
z'=2yy'=2z-4x.
\]
即
\[
z'-2z=-4x.
\]
解得
\[
z=Ce^{2x}+2x+1.
\]
由曲线过 \((0,2)\)，得
\[
4=C+1,\qquad C=3.
\]
因此
\[
\boxed{y^2=3e^{2x}+2x+1}.
\]
若取过点 \((0,2)\) 的上支，则
\[
\boxed{y=\sqrt{3e^{2x}+2x+1}}.
\]
\examnote{法线与坐标轴交点题，第一步通常是写出法线方程。}
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 设函数 \(f(x)\) 在 \([0,1]\) 上连续，在 \((0,1)\) 内大于零，且满足微分方程
\[
xf'(x)=f(x)+\frac32ax^2.
\]
曲线 \(y=f(x)\) 与直线 \(x=1,\ y=0\) 所围成区域 \(D\) 的面积为 \(2\)，求：
\begin{enumerate}
\item \(f(x)\)；
\item 使 \(D\) 绕 \(x\) 轴旋转一周而成旋转体体积最小的 \(a\)。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{先解一阶线性方程，再用面积条件确定积分常数，最后把旋转体体积写成 \(a\) 的二次函数。}
由
\[
xf'-f=\frac32ax^2
\]
得
\[
\left(\frac{f}{x}\right)'=\frac{xf'-f}{x^2}=\frac32a.
\]
因此
\[
\frac{f}{x}=\frac32ax+C,
\]
即
\[
f(x)=Cx+\frac32ax^2.
\]
区域面积为
\[
\int_0^1f(x)\,dx=2.
\]
所以
\[
\frac C2+\frac a2=2,\qquad C=4-a.
\]
故
\[
\boxed{f(x)=(4-a)x+\frac32ax^2}.
\]
旋转体体积
\[
V(a)=\pi\int_0^1 f^2(x)\,dx.
\]
代入 \(f(x)=(4-a)x+\frac32ax^2\)，得
\[
\frac{V(a)}{\pi}
=\frac{(4-a)^2}{3}+\frac{3a(4-a)}{4}+\frac{9a^2}{20}
=\frac{a^2+10a+160}{30}.
\]
这是开口向上的二次函数，其最小值在
\[
2a+10=0
\]
处取得，故
\[
\boxed{a=-5}.
\]
此时
\[
f(x)=9x-\frac{15}{2}x^2>0\qquad(0<x<1).
\]
\examnote{面积条件用于确定通解常数；体积最值通常转为参数二次函数最值。}
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 设曲线 \(L\) 位于 \(xOy\) 平面的第一象限内，\(L\) 上任一点 \(M\) 处的切线与 \(y\) 轴总相交，交点记为 \(A\)。已知
\[
|MA|=|OA|,
\]
且 \(L\) 过点 \((3/2,3/2)\)，求 \(L\) 的方程。
\end{problemblock}

\begin{solutionblock}
\analysis{设 \(M(x,y)\)，切线斜率为 \(y'\)。切线在 \(y\) 轴上的截距为 \(y-xy'\)。}
切线方程为
\[
Y-y=y'(X-x).
\]
令 \(X=0\)，得
\[
A=(0,y-xy').
\]
于是
\[
|OA|=y-xy',
\]
而
\[
|MA|=\sqrt{x^2+(xy')^2}=x\sqrt{1+(y')^2}.
\]
题设给出
\[
x\sqrt{1+(y')^2}=y-xy'.
\]
两边平方并化简：
\[
x^2=y^2-2xyy',
\]
所以
\[
y'=\frac{y^2-x^2}{2xy}.
\]
令 \(v=y/x\)，则 \(y=vx,\ y'=v+xv'\)。代入得
\[
v+xv'=\frac{v^2-1}{2v},
\]
即
\[
\frac{2v}{v^2+1}\,dv=-\frac{dx}{x}.
\]
积分：
\[
\ln(v^2+1)=-\ln x+C.
\]
故
\[
x\left(1+\frac{y^2}{x^2}\right)=C,
\]
即
\[
x^2+y^2=Cx.
\]
代入点 \((3/2,3/2)\)，得
\[
\frac94+\frac94=\frac32C,\qquad C=3.
\]
所以
\[
\boxed{x^2+y^2=3x}.
\]
\examnote{切线截距条件常能转成齐次微分方程，令 \(y=vx\) 处理。}
\end{solutionblock}

\begin{problemblock}
\textbf{32.}（数学三不要求）在上半平面一条向下凸的曲线，其上任一点 \(P(x,y)\) 处的曲率等于此曲线在该点的法线段 \(PQ\) 长度的倒数，其中 \(Q\) 是法线与 \(x\) 轴的交点，且曲线在点 \((1,1)\) 处的切线与 \(x\) 轴平行。求该曲线。
\end{problemblock}

\begin{solutionblock}
\analysis{向下凸说明曲率 \(\kappa=-y''/(1+y'^2)^{3/2}\)。法线段长度为 \(y\sqrt{1+y'^2}\)。}
法线段
\[
PQ=y\sqrt{1+(y')^2}.
\]
曲率条件为
\[
\frac{-y''}{[1+(y')^2]^{3/2}}
=\frac{1}{y\sqrt{1+(y')^2}}.
\]
整理得
\[
yy''+1+(y')^2=0.
\]
即
\[
(yy')'+1=0.
\]
积分：
\[
yy'=-x+C.
\]
在点 \((1,1)\) 处切线与 \(x\) 轴平行，所以 \(y'(1)=0\)，代入得
\[
0=-1+C,\qquad C=1.
\]
于是
\[
yy'=1-x.
\]
再积分：
\[
\frac12y^2=x-\frac{x^2}{2}+C_1.
\]
代入 \((1,1)\)，得 \(C_1=0\)。所以
\[
y^2=2x-x^2.
\]
上半平面取正支：
\[
\boxed{y=\sqrt{2x-x^2}}.
\]
\examnote{曲率题先写曲率公式，再把法线长度用 \(y,y'\) 表示。}
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 设 \(L\) 是一条平面曲线，其上任意一点 \(P(x,y)\ (x>0)\) 到坐标原点的距离，恒等于该点处切线在 \(y\) 轴上的截距，且 \(L\) 经过点 \((1/2,0)\)。
\begin{enumerate}
\item 求曲线 \(L\) 的方程；
\item 设 \(L\) 位于第一象限部分的一条切线，使该切线与 \(L\) 以及两坐标轴所围图形的面积最小，求此切线。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{切线在 \(y\) 轴上的截距为 \(y-xy'\)，距离原点为 \(\sqrt{x^2+y^2}\)。}
\textbf{(1)} 由题意
\[
y-xy'=\sqrt{x^2+y^2}.
\]
所以
\[
y'=\frac{y-\sqrt{x^2+y^2}}{x}.
\]
令 \(v=y/x\)，则
\[
v+xv'=v-\sqrt{1+v^2},
\]
即
\[
\frac{dv}{\sqrt{1+v^2}}=-\frac{dx}{x}.
\]
积分：
\[
\operatorname{arsinh}v=-\ln x+C.
\]
由 \(L\) 过 \((1/2,0)\)，得 \(C=\ln(1/2)\)。故
\[
\operatorname{arsinh}\frac{y}{x}=\ln\frac{1}{2x}.
\]
于是
\[
\frac{y}{x}=\sinh\left(\ln\frac1{2x}\right)
=\frac{1}{4x}-x.
\]
故
\[
\boxed{y=\frac14-x^2}.
\]

\textbf{(2)} 第一象限部分为 \(0<x<1/2\)。设切点横坐标为 \(t\)，则
\[
y=\frac14-x^2,\qquad y'=-2x.
\]
切线为
\[
Y=-2t(X-t)+\frac14-t^2=-2tX+t^2+\frac14.
\]
其 \(y\) 轴截距为
\[
B=t^2+\frac14,
\]
\(x\) 轴截距为
\[
A=\frac{B}{2t}.
\]
切线与两坐标轴围成三角形面积为
\[
S_{\triangle}=\frac12AB=\frac{B^2}{4t}
=\frac{(t^2+1/4)^2}{4t}.
\]
与曲线 \(L\) 以及两坐标轴围成的面积只是在此基础上减去固定的曲线下方面积，故最小化等价于最小化 \(S_{\triangle}\)。
令导数为零，得
\[
3t^2=\frac14,\qquad t=\frac{1}{2\sqrt3}.
\]
此时
\[
B=t^2+\frac14=\frac13,
\]
切线为
\[
\boxed{y=-\frac{x}{\sqrt3}+\frac13}.
\]
\examnote{含“切线与坐标轴所围面积最小”，通常先用切点参数表示两个截距。}
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 设 \(y=y(x)\) 是区间 \((-\pi,\pi)\) 内过点 \((-\pi/2,\pi/2)\) 的光滑曲线。当 \(-\pi<x<0\) 时，曲线上任一点处的法线都过原点；当 \(0\le x<\pi\) 时，函数 \(y(x)\) 满足
\[
y''+y+x=0.
\]
求函数 \(y(x)\) 的表达式。
\end{problemblock}

\begin{solutionblock}
\analysis{左半段由“法线过原点”得到 \(yy'=-x\)，再用光滑性给出右半段初值。}
当 \(-\pi<x<0\) 时，法线过原点。切线斜率为 \(y'\)，法线斜率为 \(-1/y'\)。原点与点 \((x,y)\) 连线斜率为 \(y/x\)，故
\[
-\frac1{y'}=\frac{y}{x},
\]
即
\[
yy'=-x.
\]
积分得
\[
x^2+y^2=C.
\]
代入点 \((-\pi/2,\pi/2)\)，得
\[
C=\frac{\pi^2}{2}.
\]
左半段位于上方，故
\[
y=\sqrt{\frac{\pi^2}{2}-x^2}\qquad(-\pi<x<0).
\]
于是
\[
y(0^-)=\frac{\pi}{\sqrt2},\qquad y'(0^-)=0.
\]
光滑性给出右半段初值
\[
y(0)=\frac{\pi}{\sqrt2},\qquad y'(0)=0.
\]
当 \(0\le x<\pi\) 时，
\[
y''+y=-x.
\]
通解为
\[
y=C_1\cos x+C_2\sin x-x.
\]
代入初值：
\[
C_1=\frac{\pi}{\sqrt2},\qquad C_2-1=0.
\]
所以
\[
y=\frac{\pi}{\sqrt2}\cos x+\sin x-x\qquad(0\le x<\pi).
\]
综上
\[
\boxed{
y(x)=
\begin{cases}
\sqrt{\dfrac{\pi^2}{2}-x^2},&-\pi<x<0,\\[6pt]
\dfrac{\pi}{\sqrt2}\cos x+\sin x-x,&0\le x<\pi.
\end{cases}}
\]
\examnote{分段微分方程要用“光滑曲线”在分界点处衔接函数值和导数值。}
\end{solutionblock}

\begin{problemblock}
\textbf{35.}（数学三不要求）已知曲线
\[
L:\quad x=f(t),\quad y=\cos t,\qquad 0\le t<\frac{\pi}{2},
\]
其中 \(f(0)=0,\ f'(t)>0\)。若曲线 \(L\) 的切线与 \(x\) 轴的交点到切点的距离恒为 \(1\)，求 \(f(t)\)，并求以曲线 \(L\) 及 \(x\) 轴和 \(y\) 轴为边界的区域面积。
\end{problemblock}

\begin{solutionblock}
\analysis{参数曲线切线斜率为 \(\frac{dy/dt}{dx/dt}=-\sin t/f'(t)\)。切点到 \(x\) 轴切线交点的距离由直角三角形给出。}
切线斜率
\[
m=\frac{dy/dt}{dx/dt}=-\frac{\sin t}{f'(t)}.
\]
切点纵坐标为 \(\cos t\)。沿切线下降到 \(x\) 轴的距离为
\[
\cos t\frac{\sqrt{1+m^2}}{|m|}.
\]
题设该距离恒为 \(1\)，故
\[
\cos t\frac{\sqrt{f'^2(t)+\sin^2t}}{\sin t}=1.
\]
于是
\[
f'^2(t)+\sin^2t=\tan^2t,
\]
从而
\[
f'(t)=\frac{\sin^2t}{\cos t}\qquad(f'(t)>0).
\]
积分：
\[
f(t)=\int_0^t\frac{\sin^2u}{\cos u}\,du
=\int_0^t(\sec u-\cos u)\,du.
\]
所以
\[
\boxed{f(t)=\ln(\sec t+\tan t)-\sin t}.
\]
区域面积
\[
S=\int y\,dx
=\int_0^{\pi/2}\cos t\,f'(t)\,dt
=\int_0^{\pi/2}\sin^2t\,dt
=\boxed{\frac{\pi}{4}}.
\]
\examnote{参数曲线面积常用 \(S=\int y\,dx=\int y(t)x'(t)dt\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 在 \(xOy\) 坐标平面上，连续曲线 \(L\) 过点 \(M(1,0)\)，其上任意点 \(P(x,y)\ (x\ne0)\) 处的切线斜率与直线 \(OP\) 的斜率之差等于 \(ax\)，其中常数 \(a>0\)。
\begin{enumerate}
\item 求 \(L\) 的方程；
\item 当 \(L\) 与直线 \(y=ax\) 所围成平面图形的面积为 \(8/3\) 时，确定 \(a\) 的值。
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{切线斜率是 \(y'\)，直线 \(OP\) 的斜率是 \(y/x\)。}
\textbf{(1)} 由题意
\[
y'-\frac{y}{x}=ax.
\]
这是线性方程。注意
\[
\left(\frac{y}{x}\right)'=\frac{xy'-y}{x^2}.
\]
两边等价于
\[
\left(\frac{y}{x}\right)'=a.
\]
积分得
\[
\frac{y}{x}=ax+C,
\]
即
\[
y=ax^2+Cx.
\]
由 \(L\) 过 \((1,0)\)，得
\[
0=a+C,\qquad C=-a.
\]
所以
\[
\boxed{y=ax^2-ax}.
\]

\textbf{(2)} 曲线 \(y=ax^2-ax\) 与直线 \(y=ax\) 的交点满足
\[
ax^2-ax=ax,
\]
即
\[
ax(x-2)=0.
\]
故交点横坐标为 \(0,2\)。在 \([0,2]\) 上，直线 \(y=ax\) 位于曲线上方，面积为
\[
S=\int_0^2\left[ax-(ax^2-ax)\right]dx
=a\int_0^2(2x-x^2)\,dx
=\frac{4a}{3}.
\]
由 \(S=8/3\)，得
\[
\boxed{a=2}.
\]
\examnote{“切线斜率与 OP 斜率之差”直接翻译为 \(y'-y/x\)。}
\end{solutionblock}

\section{第四章完成说明}
第四章除原书未出现的第 \(16,17\) 题外，其余第 \(1\)--\(15\)、\(18\)--\(36\) 题已按“题目解析、完整推导、答案、考研提示”的格式整理完毕。
"""


CH05_TEX = r"""\chapter{多元函数微分学}

\section{原题页索引}
本章原题对应做题本第 \(76\)--\(95\) 页。本节先完成第 \(1\)--\(15\) 题详细解析。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_076.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 已知
\[
f(x,y)=e^{-\sqrt{x^2+y^4}},
\]
判断 \(f'_x(0,0),f'_y(0,0)\) 是否存在。
\end{problemblock}

\begin{solutionblock}
\analysis{按偏导定义沿坐标轴分别考察。}
\[
f'_x(0,0)=\lim_{h\to0}\frac{e^{-|h|}-1}{h}.
\]
当 \(h\to0^+\) 时极限为 \(-1\)，当 \(h\to0^-\) 时极限为 \(1\)，故 \(f'_x(0,0)\) 不存在。

而
\[
f'_y(0,0)=\lim_{h\to0}\frac{e^{-h^2}-1}{h}=0.
\]
所以
\[
\boxed{f'_x(0,0)\text{ 不存在},\quad f'_y(0,0)\text{ 存在}}.
\]
\[
\boxed{\text{B}}
\]
\examnote{偏导只沿坐标轴取极限，含 \(|x|\) 时左右导数常不一致。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 设函数 \(z=f(x,y)\) 在点 \((x_0,y_0)\) 处有
\[
f'_x(x_0,y_0)=a,\qquad f'_y(x_0,y_0)=b.
\]
判断下列结论哪一个正确。
\end{problemblock}

\begin{solutionblock}
\analysis{偏导存在只能保证沿对应坐标方向的一元函数在该点连续，不能推出二元连续或可微。}
偏导 \(f'_x(x_0,y_0)\) 存在，说明一元函数 \(x\mapsto f(x,y_0)\) 在 \(x_0\) 处可导，因而
\[
\lim_{x\to x_0}f(x,y_0)=f(x_0,y_0).
\]
同理
\[
\lim_{y\to y_0}f(x_0,y)=f(x_0,y_0).
\]
所以这两个沿坐标轴的极限都存在且相等。

但偏导存在不能推出二元极限存在、连续或可微。
\[
\boxed{\text{D}}
\]
\examnote{“偏导存在 \(\nRightarrow\) 连续 \(\nRightarrow\) 可微”，这是多元微分学第一类易错点。}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 设
\[
f(x,y)=
\begin{cases}
\dfrac{xy}{\sqrt{x^2+y^2}},&(x,y)\ne(0,0),\\
0,&(x,y)=(0,0).
\end{cases}
\]
判断 \(f(x,y)\) 在 \((0,0)\) 处的性质。
\end{problemblock}

\begin{solutionblock}
\analysis{先看偏导，再看可微性。}
沿 \(x\) 轴与 \(y\) 轴，
\[
f(h,0)=0,\qquad f(0,h)=0,
\]
故
\[
f'_x(0,0)=f'_y(0,0)=0.
\]
又
\[
|f(x,y)|=\frac{|xy|}{\sqrt{x^2+y^2}}\le \frac{x^2+y^2}{2\sqrt{x^2+y^2}}\to0,
\]
所以函数连续。

若可微，则应有
\[
\frac{f(x,y)-0}{\sqrt{x^2+y^2}}\to0.
\]
但沿 \(y=x\)，
\[
\frac{f(x,x)}{\sqrt{2x^2}}
=\frac{|x|/\sqrt2}{\sqrt2|x|}
=\frac12.
\]
故不可微。
\[
\boxed{\text{B}}
\]
\examnote{可微要检查余项除以 \(\rho=\sqrt{x^2+y^2}\) 是否趋零。}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 设
\[
f(x,y)=
\begin{cases}
(x^2+y^2)\sin\dfrac1{x^2+y^2},&(x,y)\ne(0,0),\\
0,&(x,y)=(0,0).
\end{cases}
\]
判断 \(f(x,y)\) 在 \((0,0)\) 处的性质。
\end{problemblock}

\begin{solutionblock}
\analysis{函数量级为 \(r^2\)，所以可微；但偏导表达式含 \(1/r\) 型振荡项，不连续。}
有
\[
|f(x,y)|\le x^2+y^2.
\]
因此
\[
\frac{|f(x,y)-0|}{\sqrt{x^2+y^2}}\le \sqrt{x^2+y^2}\to0,
\]
故 \(f\) 在原点可微，且
\[
f'_x(0,0)=f'_y(0,0)=0.
\]
但在 \((x,y)\ne(0,0)\) 时，偏导中会出现
\[
-\frac{2x}{x^2+y^2}\cos\frac1{x^2+y^2}
\]
这类项，沿不同路径振荡且无界，所以偏导数在原点不连续。
\[
\boxed{\text{D}}
\]
\examnote{\(r^2\sin(1/r^2)\) 型函数可微，但偏导通常不连续。}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 设函数 \(f(x,y)\) 可微，且对任意 \(x,y\) 都有
\[
\frac{\partial f}{\partial x}>0,\qquad \frac{\partial f}{\partial y}<0.
\]
使不等式
\[
f(x_1,y_1)<f(x_2,y_2)
\]
成立的一个充分条件是什么？
\end{problemblock}

\begin{solutionblock}
\analysis{\(x\) 增大时 \(f\) 增大，\(y\) 增大时 \(f\) 减小。}
若
\[
x_1<x_2,\qquad y_1>y_2,
\]
则先固定 \(y_1\)，由 \(f_x>0\) 得
\[
f(x_1,y_1)<f(x_2,y_1).
\]
再固定 \(x_2\)，由于 \(y_1>y_2\) 且 \(f_y<0\)，得
\[
f(x_2,y_1)<f(x_2,y_2).
\]
所以
\[
f(x_1,y_1)<f(x_2,y_2).
\]
\[
\boxed{\text{D}}
\]
\examnote{偏导符号题可分两步走：先变 \(x\)，再变 \(y\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 设可微函数 \(f(x,y)\) 满足
\[
\frac{\partial f}{\partial x}>1,\qquad \frac{\partial f}{\partial y}<-1,\qquad f(0,0)=0.
\]
判断下列结论正确的是哪一个。
\end{problemblock}

\begin{solutionblock}
\analysis{用路径积分估计函数增量。}
从 \((0,0)\) 到 \((1,-1)\)，先沿 \(x\) 方向：
\[
f(1,0)-f(0,0)=\int_0^1 f_x(x,0)\,dx>1.
\]
再沿 \(y\) 方向从 \(0\) 到 \(-1\)：
\[
f(1,-1)-f(1,0)=\int_0^{-1} f_y(1,y)\,dy.
\]
因为 \(f_y<-1\)，而积分上限小于下限，故
\[
\int_0^{-1} f_y(1,y)\,dy>1.
\]
所以
\[
f(1,-1)>2.
\]
\[
\boxed{\text{D}}
\]
\examnote{当积分方向反向时，不等号方向容易误判；这里 \(dy<0\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 设函数 \(f(x,y)\) 满足
\[
\frac{\partial f}{\partial x}<0,\qquad \frac{\partial f}{\partial y}>1.
\]
判断下列结论正确的是哪一个。
\end{problemblock}

\begin{solutionblock}
\analysis{从 \((0,0)\) 到 \((-1,1)\) 分段积分。}
先沿 \(x\) 方向从 \(0\) 到 \(-1\)。由于 \(f_x<0\)，反向积分使函数增加：
\[
f(-1,0)-f(0,0)=\int_0^{-1}f_x(x,0)\,dx>0.
\]
再沿 \(y\) 方向从 \(0\) 到 \(1\)：
\[
f(-1,1)-f(-1,0)=\int_0^1f_y(-1,y)\,dy>1.
\]
故
\[
f(-1,1)>f(0,0)+1.
\]
\[
\boxed{\text{C}}
\]
\examnote{偏导不等式可以沿折线路径积分，得到函数值比较。}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 设函数 \(f(x,y)\) 在点 \((0,0)\) 的某邻域内有定义，且
\[
\lim_{(x,y)\to(0,0)}
\frac{f(x,y)-(x^2+y^2)}{\sqrt{x^2+y^2}}=1.
\]
判断 \(f(x,y)\) 在 \((0,0)\) 处的性质。
\end{problemblock}

\begin{solutionblock}
\analysis{该条件表明 \(f(x,y)=x^2+y^2+\sqrt{x^2+y^2}+o(r)\)，主部含 \(r\)，沿坐标轴有尖点。}
由题设
\[
f(x,y)=x^2+y^2+\sqrt{x^2+y^2}+o\left(\sqrt{x^2+y^2}\right).
\]
沿 \(x\) 轴，
\[
f(x,0)=x^2+|x|+o(|x|).
\]
若取 \(f(0,0)=0\)，则
\[
\frac{f(x,0)-f(0,0)}{x}
=x+\frac{|x|}{x}+o(1),
\]
右极限为 \(1\)，左极限为 \(-1\)，故 \(f'_x(0,0)\) 不存在。类似地 \(f'_y(0,0)\) 也不存在。
\[
\boxed{\text{B}}
\]
\examnote{出现 \(\sqrt{x^2+y^2}\) 主部时，沿正负坐标轴通常产生左右导数不一致。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 已知 \(f(x,y)\) 在 \((0,0)\) 点连续，且
\[
\lim_{(x,y)\to(0,0)}
\frac{f(x,y)+2x-y+x^2+y^2}{\sqrt{x^2+y^2}^{\,2}}=0.
\]
判断下列结论不正确的是哪一个。
\end{problemblock}

\begin{solutionblock}
\analysis{分母就是 \(x^2+y^2\)。条件给出了 \(f\) 的二阶展开。}
由题设
\[
f(x,y)=-2x+y-x^2-y^2+o(x^2+y^2).
\]
因此 \(f\) 在原点可微，且
\[
f'_x(0,0)=-2,\qquad f'_y(0,0)=1.
\]
所以“\(f'_x(0,0)\) 和 \(f'_y(0,0)\) 都不一定存在”这一说法不正确。
\[
\boxed{\text{D}}
\]
\examnote{若能写出一次线性主部，就能直接读出偏导数并判断可微。}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 设 \(z=f(x,y)\) 满足
\[
\frac{\partial^2 z}{\partial y^2}=2,\qquad f(x,0)=1,\qquad f'_y(x,0)=x.
\]
求 \(f(x,y)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{对 \(y\) 连续积分两次，积分“常数”可以是 \(x\) 的函数。}
由
\[
f_{yy}=2
\]
对 \(y\) 积分得
\[
f_y=2y+A(x).
\]
由
\[
f_y(x,0)=x
\]
得
\[
A(x)=x.
\]
再对 \(y\) 积分：
\[
f=y^2+xy+B(x).
\]
由
\[
f(x,0)=1
\]
得
\[
B(x)=1.
\]
所以
\[
\boxed{f(x,y)=1+xy+y^2}.
\]
\[
\boxed{\text{B}}
\]
\examnote{对某个变量积分时，积分常数要写成另一个变量的函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 已知函数 \(f(x,y)\) 在 \((0,0)\) 的某邻域内连续，且
\[
\lim_{(x,y)\to(0,0)}
\frac{f(x,y)-(x^2+y^2)}{\sqrt{x^2+y^2}}=a>0.
\]
判断 \((0,0)\) 是何种点。
\end{problemblock}

\begin{solutionblock}
\analysis{连续性给出 \(f(0,0)=0\)。邻近点上 \(f\) 的主部为 \(a r\)，且 \(a>0\)。}
由连续性和极限条件，
\[
f(0,0)=0.
\]
当 \((x,y)\ne(0,0)\) 且充分接近原点时，
\[
f(x,y)=x^2+y^2+a\sqrt{x^2+y^2}+o(\sqrt{x^2+y^2})>0.
\]
所以 \((0,0)\) 是极小值点。

但由于主部含 \(\sqrt{x^2+y^2}\)，偏导数在原点一般不存在，因此它不是驻点。
\[
\boxed{\text{C}}
\]
\examnote{极值点不一定是驻点；费马定理要求偏导存在。}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 设函数 \(z=f(x,y)\) 的全微分为
\[
dz=x\,dx+y\,dy.
\]
判断点 \((0,0)\) 的性质。
\end{problemblock}

\begin{solutionblock}
\analysis{由全微分读出 \(f_x=x,\ f_y=y\)，再积分或看 Hessian。}
由
\[
dz=f_xdx+f_ydy=x\,dx+y\,dy
\]
得
\[
f_x=x,\qquad f_y=y.
\]
因此
\[
f(x,y)=\frac12x^2+\frac12y^2+C.
\]
显然 \((0,0)\) 是极小值点。
\[
\boxed{\text{D}}
\]
\examnote{全微分给出的就是梯度；本题本质是正定二次型。}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 设函数 \(f(x)\) 具有二阶连续导数，且 \(f(x)>0,\ f'(0)=0\)。函数
\[
z=f(x)\ln f(y)
\]
在点 \((0,0)\) 处取得极小值的一个充分条件是什么？
\end{problemblock}

\begin{solutionblock}
\analysis{计算二阶偏导。由于 \(f'(0)=0\)，混合项为零。}
设 \(c=f(0)>0\)。在 \((0,0)\) 处，
\[
z_{xx}=f''(0)\ln c,
\]
\[
z_{yy}=f(0)\cdot \frac{f''(0)f(0)-[f'(0)]^2}{f^2(0)}
=f''(0),
\]
且
\[
z_{xy}=0.
\]
要使 Hessian 正定，需
\[
z_{xx}>0,\qquad z_{yy}>0.
\]
即
\[
f''(0)>0,\qquad \ln f(0)>0.
\]
因此
\[
f(0)>1,\qquad f''(0)>0.
\]
\[
\boxed{\text{A}}
\]
\examnote{二元极值充分条件看 Hessian；混合项为零时只需两个二阶偏导同为正。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 设函数 \(f(x),g(x)\) 均有二阶连续导数，满足
\[
f(0)>0,\qquad g(0)<0,\qquad f'(0)=g'(0)=0.
\]
函数
\[
z=f(x)g(y)
\]
在点 \((0,0)\) 处取得极小值的一个充分条件是什么？
\end{problemblock}

\begin{solutionblock}
\analysis{二阶偏导为 \(z_{xx}=f''(0)g(0)\)，\(z_{yy}=f(0)g''(0)\)，混合项为零。}
在 \((0,0)\) 处，
\[
z_{xx}=f''(0)g(0),\qquad
z_{yy}=f(0)g''(0),\qquad
z_{xy}=f'(0)g'(0)=0.
\]
要取得极小值，Hessian 正定，故需要
\[
f''(0)g(0)>0,\qquad f(0)g''(0)>0.
\]
由于
\[
g(0)<0,\qquad f(0)>0,
\]
得到
\[
f''(0)<0,\qquad g''(0)>0.
\]
\[
\boxed{\text{A}}
\]
\examnote{乘积型函数先看各因子的符号，再判断二阶项正负。}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 设 \(F(x,y)\) 具有二阶连续偏导数，且
\[
F(x_0,y_0)=0,\qquad F'_x(x_0,y_0)=0,\qquad F'_y(x_0,y_0)>0.
\]
若一元函数 \(y=y(x)\) 是由方程 \(F(x,y)=0\) 所确定的在点 \((x_0,y_0)\) 附近的隐函数，求 \(x_0\) 是函数 \(y=y(x)\) 的极小值点的一个充分条件。
\end{problemblock}

\begin{solutionblock}
\analysis{隐函数求导：\(y'=-F_x/F_y\)，再在 \(F_x=0\) 处求二阶导。}
由隐函数求导公式
\[
y'=-\frac{F_x}{F_y}.
\]
在 \((x_0,y_0)\) 处，
\[
y'(x_0)=0.
\]
继续求导。由于 \(y'(x_0)=0\)，有
\[
y''(x_0)=-\frac{F_{xx}(x_0,y_0)}{F_y(x_0,y_0)}.
\]
要使 \(x_0\) 为 \(y(x)\) 的极小值点，需要
\[
y''(x_0)>0.
\]
又 \(F_y(x_0,y_0)>0\)，故充分条件为
\[
F_{xx}(x_0,y_0)<0.
\]
\[
\boxed{\text{B}}
\]
\examnote{隐函数极值题先求 \(y'\)，驻点后再用 \(y''\) 判别。}
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 设函数 \(u(x,y)\) 在有界闭区域 \(D\) 上连续，在 \(D\) 的内部具有二阶连续偏导数，且满足
\[
\frac{\partial^2u}{\partial x\partial y}\ne0,\qquad
\frac{\partial^2u}{\partial x^2}+\frac{\partial^2u}{\partial y^2}=0.
\]
判断最大值与最小值的位置。
\end{problemblock}

\begin{solutionblock}
\analysis{这是调和函数的最大值原理。条件 \(u_{xy}\ne0\) 排除了常函数情形。}
由
\[
u_{xx}+u_{yy}=0
\]
知 \(u\) 是区域内部的调和函数。非常值调和函数不能在内部取得最大值或最小值，否则由最大值原理可推出其为常数，与 \(u_{xy}\ne0\) 矛盾。

又 \(u\) 在有界闭区域 \(D\) 上连续，最大值和最小值一定能取得。因此最大值和最小值都在边界上取得。
\[
\boxed{\text{A}}
\]
\examnote{看到 \(u_{xx}+u_{yy}=0\)，立刻想到调和函数最大值原理。}
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 设
\[
z=\frac{x(\cos y-1)-(y-1)\cos x}{1+\sin x+\sin(y-1)},
\]
求
\[
\left.\frac{\partial z}{\partial y}\right|_{(0,1)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{在点 \((0,1)\) 处分子为 \(0\)，所以求偏导时商法则大幅简化。}
记
\[
N=x(\cos y-1)-(y-1)\cos x,\qquad
D=1+\sin x+\sin(y-1).
\]
在 \((0,1)\) 处，
\[
N(0,1)=0,\qquad D(0,1)=1.
\]
因此
\[
z_y(0,1)=\frac{N_y(0,1)}{D(0,1)}.
\]
而
\[
N_y=-x\sin y-\cos x,
\]
故
\[
N_y(0,1)=-1.
\]
所以
\[
\boxed{z_y(0,1)=-1}.
\]
\examnote{分式在目标点分子为零时，商法则只剩分子导数除以分母值。}
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 设
\[
z=\arctan\frac{x}{y^2},
\]
求
\[
\left.\frac{\partial^2z}{\partial y\partial x}\right|_{(0,1)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先对 \(x\) 求偏导，再对 \(y\) 求偏导。}
先求
\[
z_x=\frac{1}{1+(x/y^2)^2}\cdot\frac1{y^2}
=\frac{y^2}{x^2+y^4}.
\]
再对 \(y\) 求导：
\[
z_{xy}
=\frac{2y(x^2+y^4)-y^2\cdot4y^3}{(x^2+y^4)^2}
=\frac{2yx^2-2y^5}{(x^2+y^4)^2}.
\]
代入 \((0,1)\)，得
\[
\boxed{z_{xy}(0,1)=-2}.
\]
\examnote{混合偏导的顺序要按题目写法执行：\(\partial^2z/\partial y\partial x\) 是先 \(x\) 后 \(y\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{19.} 设
\[
z=(x+e^y)^x,
\]
求
\[
\left.\frac{\partial z}{\partial x}\right|_{(1,0)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{幂指函数对 \(x\) 求导，先取对数。}
\[
\ln z=x\ln(x+e^y).
\]
对 \(x\) 求偏导：
\[
\frac{z_x}{z}=\ln(x+e^y)+\frac{x}{x+e^y}.
\]
在 \((1,0)\) 处，
\[
z=2,\qquad \ln(x+e^y)=\ln2,\qquad \frac{x}{x+e^y}=\frac12.
\]
故
\[
z_x(1,0)=2\left(\ln2+\frac12\right)=\boxed{2\ln2+1}.
\]
\examnote{变量同时在底数和指数中时，对数求导最稳。}
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 设
\[
z=(1+xy)^{xy},
\]
求
\[
dz\big|_{(1,1)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(u=xy\)，则 \(z=(1+u)^u\)。}
设
\[
u=xy.
\]
则
\[
dz=z\left[\ln(1+u)+\frac{u}{1+u}\right]du.
\]
在 \((1,1)\) 处，
\[
u=1,\qquad z=2,\qquad du=y\,dx+x\,dy=dx+dy.
\]
所以
\[
dz\big|_{(1,1)}
=2\left(\ln2+\frac12\right)(dx+dy)
=\boxed{(2\ln2+1)(dx+dy)}.
\]
\examnote{全微分题要把 \(dx,dy\) 的线性组合写完整。}
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 设函数 \(z=z(x,y)\) 由方程
\[
(z+y)^x=xy
\]
确定，求
\[
\left.\frac{\partial z}{\partial x}\right|_{(1,2)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先求点上的 \(z\)，再对隐式方程取对数求导。}
当 \((x,y)=(1,2)\) 时，
\[
z+2=2,
\]
所以
\[
z=0.
\]
对方程取对数：
\[
x\ln(z+y)=\ln x+\ln y.
\]
对 \(x\) 求偏导：
\[
\ln(z+y)+x\frac{z_x}{z+y}=\frac1x.
\]
代入 \((1,2,0)\)，得
\[
\ln2+\frac{z_x}{2}=1.
\]
故
\[
\boxed{z_x(1,2)=2(1-\ln2)}.
\]
\examnote{幂式隐函数常先取对数再求导。}
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 设
\[
u=x^2e^{yz^3},
\]
其中 \(z=z(x,y)\) 由方程
\[
x^3+y^3+z^3-3xyz=0
\]
所确定，求
\[
du\big|_{x=-1,y=0}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{在目标点先由隐式方程求 \(z\)。对 \(\ln u\) 求微分最简。}
当 \(x=-1,y=0\) 时，
\[
-1+z^3=0,\qquad z=1.
\]
取对数：
\[
\ln u=2\ln|x|+yz^3.
\]
微分：
\[
d(\ln u)=2\frac{dx}{x}+z^3dy+3yz^2dz.
\]
在 \((-1,0,1)\) 处，\(y=0,\ u=1\)，所以
\[
d(\ln u)=-2dx+dy.
\]
因此
\[
du=u\,d(\ln u)=\boxed{-2dx+dy}.
\]
\examnote{指数复合函数求微分，常先求 \(d\ln u\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 设 \(z=f(x,y)\) 满足
\[
\frac{\partial^2z}{\partial x\partial y}=x+y,\qquad
f(x,0)=x,\qquad f(0,y)=y^2.
\]
求 \(f(x,y)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{从 \(f_{xy}\) 积分，积分“常数”分别是单变量函数，再用边界条件确定。}
由
\[
f_{xy}=x+y
\]
先对 \(y\) 积分：
\[
f_x=xy+\frac12y^2+\varphi(x).
\]
由 \(f(x,0)=x\)，得
\[
f_x(x,0)=1,
\]
所以
\[
\varphi(x)=1.
\]
再对 \(x\) 积分：
\[
f(x,y)=\frac12x^2y+\frac12xy^2+x+\psi(y).
\]
由 \(f(0,y)=y^2\)，得
\[
\psi(y)=y^2.
\]
故
\[
\boxed{f(x,y)=x+y^2+\frac12x^2y+\frac12xy^2}.
\]
\examnote{二阶混合偏导积分两次，每次都要补上“任意函数”。}
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 设 \(u(x,y)\) 有连续二阶偏导数，
\[
u_{xx}=u_{yy},
\]
且
\[
u(x,2x)=x,\qquad u_x(x,2x)=x^2.
\]
求
\[
u_{xx}(x,2x).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{沿曲线 \(y=2x\) 对给定条件求导，得到关于 \(u_{xx},u_{xy}\) 的方程组。}
由
\[
u(x,2x)=x
\]
求导：
\[
u_x(x,2x)+2u_y(x,2x)=1.
\]
再求导：
\[
u_{xx}+4u_{xy}+4u_{yy}=0.
\]
由 \(u_{xx}=u_{yy}\)，得
\[
5u_{xx}+4u_{xy}=0. \tag{1}
\]
又由
\[
u_x(x,2x)=x^2
\]
求导：
\[
u_{xx}+2u_{xy}=2x. \tag{2}
\]
联立 (1)(2)，由 \(2\times(2)\) 得
\[
2u_{xx}+4u_{xy}=4x.
\]
与 (1) 相减：
\[
3u_{xx}=-4x.
\]
故
\[
\boxed{u_{xx}(x,2x)=-\frac{4x}{3}}.
\]
\examnote{沿曲线给条件时，对复合函数求导会产生链式法则方程组。}
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 设函数 \(z=z(x,y)\) 由方程
\[
F\left(x+\frac{z}{y},\,y+\frac{z}{x}\right)=0
\]
确定，求
\[
x\frac{\partial z}{\partial x}+y\frac{\partial z}{\partial y}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{按题面所给条件，不能唯一确定该量。若额外假设 \(F\) 的零集具有相应齐次性，才可套用欧拉齐次公式；但原题没有给出这个条件。}
题面只说明
\[
F\left(x+\frac{z}{y},\,y+\frac{z}{x}\right)=0,
\]
并未说明 \(F\) 是齐次函数，也未说明其零集关于伸缩不变。因此 \(z\) 不一定是二次齐次函数。

例如取
\[
F(u,v)=u-1.
\]
则方程变为
\[
x+\frac{z}{y}=1,
\]
从而
\[
z=y(1-x).
\]
于是
\[
xz_x+yz_y=x(-y)+y(1-x)=y-2xy,
\]
并不等于某个只由 \(z\) 固定决定的通式，如 \(2z\)。

因此按页图题面，
\[
\boxed{\text{条件不足，不能唯一确定。}}
\]
\examnote{考研中若要用欧拉公式 \(xz_x+yz_y=nz\)，必须先证明或题设给出 \(z\) 是 \(n\) 次齐次函数。}
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 已知
\[
df(x,y)\big|_{(x_0,y_0)}=2dx+dy,
\]
求
\[
\lim_{t\to0}\frac{f(x_0+2t,y_0)-f(x_0,y_0-t)}{t}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{由全微分知 \(f_x(x_0,y_0)=2,\ f_y(x_0,y_0)=1\)。}
可微展开：
\[
f(x_0+2t,y_0)=f(x_0,y_0)+2\cdot 2t+o(t)
=f_0+4t+o(t),
\]
\[
f(x_0,y_0-t)=f(x_0,y_0)+1\cdot(-t)+o(t)
=f_0-t+o(t).
\]
两式相减：
\[
f(x_0+2t,y_0)-f(x_0,y_0-t)=5t+o(t).
\]
故极限为
\[
\boxed{5}.
\]
\examnote{全微分就是一阶线性近似，直接代增量即可。}
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 已知函数 \(z=f(x,y)\) 连续且满足
\[
\lim_{\substack{x\to1\\y\to0}}
\frac{f(x,y)-x+2y+2}{\sqrt{(x-1)^2+y^2}}=0.
\]
求
\[
\lim_{t\to0}\frac{f(1+t,0)-f(1,2t)}{t}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{极限条件给出 \(f(x,y)=x-2y-2+o(r)\)。}
由题设，
\[
f(x,y)=x-2y-2+o\left(\sqrt{(x-1)^2+y^2}\right).
\]
于是
\[
f(1+t,0)=(1+t)-2+o(t)=-1+t+o(t),
\]
\[
f(1,2t)=1-4t-2+o(t)=-1-4t+o(t).
\]
所以
\[
f(1+t,0)-f(1,2t)=5t+o(t).
\]
故
\[
\boxed{5}.
\]
\examnote{这类题不需要先求偏导，直接用给出的局部线性展开。}
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 设
\[
z=\int_0^1|xy-t|f(t)\,dt,\qquad 0\le x\le1,\quad0\le y\le1,
\]
其中 \(f(x)\) 为连续函数，求
\[
z_{xx}+z_{yy}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(s=xy\)，则 \(z\) 是 \(s\) 的函数。利用 \(\frac{d^2}{ds^2}\int|s-t|f(t)dt=2f(s)\)。}
令
\[
G(s)=\int_0^1|s-t|f(t)\,dt,\qquad s=xy.
\]
则
\[
z=G(xy).
\]
由于 \(0\le xy\le1\)，有
\[
G''(s)=2f(s).
\]
于是
\[
z_{xx}=G''(xy)y^2=2y^2f(xy),
\]
\[
z_{yy}=G''(xy)x^2=2x^2f(xy).
\]
故
\[
\boxed{z_{xx}+z_{yy}=2(x^2+y^2)f(xy)}.
\]
\examnote{\(|s-t|\) 对 \(s\) 求二阶导会产生 \(2\delta(s-t)\)，在常规考研写法中体现为 \(G''(s)=2f(s)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 设
\[
u=f(x,y,z),\qquad z=\ln\sqrt{x^2+y^2},
\]
求
\[
\frac{\partial u}{\partial x},\qquad \frac{\partial^2u}{\partial x^2},
\]
其中 \(f\) 有二阶连续偏导数。
\end{problemblock}

\begin{solutionblock}
\analysis{这里 \(u(x,y)=f(x,y,z(x,y))\)，只有第三个变量 \(z\) 依赖于 \(x,y\)。}
记 \(r^2=x^2+y^2\)。因为
\[
z=\ln\sqrt{x^2+y^2}=\frac12\ln r^2,
\]
所以
\[
z_x=\frac{x}{r^2},\qquad
z_{xx}=\frac{y^2-x^2}{r^4}.
\]
于是
\[
\boxed{u_x=f_x+f_z\frac{x}{x^2+y^2}}.
\]
继续求导：
\[
u_{xx}=f_{xx}+2f_{xz}z_x+f_{zz}z_x^2+f_z z_{xx}.
\]
代入 \(z_x,z_{xx}\)，得
\[
\boxed{
u_{xx}=f_{xx}
+\frac{2x}{x^2+y^2}f_{xz}
+\frac{x^2}{(x^2+y^2)^2}f_{zz}
+\frac{y^2-x^2}{(x^2+y^2)^2}f_z }.
\]
其中各偏导均在 \((x,y,z)\) 处取值。
\examnote{复合函数二阶偏导要同时包含 \(f_{zz}z_x^2\) 和 \(f_z z_{xx}\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 设函数 \(z=f(x,y)\) 在点 \((1,1)\) 处可微，且
\[
f(1,1)=1,\qquad f_x(1,1)=2,\qquad f_y(1,1)=3.
\]
令
\[
\varphi(x)=f[x,f(x,x)].
\]
求
\[
\left.\frac{d}{dx}\varphi^3(x)\right|_{x=1}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先求 \(\varphi(1)\) 与 \(\varphi'(1)\)，再对 \(\varphi^3\) 求导。}
由
\[
f(1,1)=1
\]
得
\[
\varphi(1)=f[1,f(1,1)]=f(1,1)=1.
\]
设
\[
g(x)=f(x,x).
\]
则
\[
g'(1)=f_x(1,1)+f_y(1,1)=2+3=5.
\]
又
\[
\varphi(x)=f(x,g(x)).
\]
所以
\[
\varphi'(1)=f_x(1,1)+f_y(1,1)g'(1)
=2+3\cdot5=17.
\]
因此
\[
\left.(\varphi^3)'(x)\right|_{x=1}
=3\varphi^2(1)\varphi'(1)
=3\cdot1^2\cdot17
=\boxed{51}.
\]
\examnote{嵌套复合 \(f[x,f(x,x)]\) 要从内层 \(g(x)=f(x,x)\) 开始求导。}
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 设 \(u=f(x,y,z)\) 有连续的一阶偏导数，又函数 \(y=y(x)\) 及 \(z=z(x)\) 分别由
\[
e^{xy}-xy=2
\]
和
\[
e^x=\int_0^{x-z}\frac{\sin t}{t}\,dt
\]
确定，求
\[
\frac{du}{dx}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{链式法则：
\[
\frac{du}{dx}=f_x+f_y y'+f_z z'.
\]
分别由两个隐式方程求 \(y',z'\)。}
对
\[
e^{xy}-xy=2
\]
求导：
\[
e^{xy}(y+xy')-(y+xy')=0.
\]
由于由原方程可知 \(e^{xy}-1=xy+1\ne0\)，故
\[
y+xy'=0,\qquad y'=-\frac{y}{x}.
\]
对
\[
e^x=\int_0^{x-z}\frac{\sin t}{t}\,dt
\]
求导：
\[
e^x=\frac{\sin(x-z)}{x-z}(1-z').
\]
因此
\[
z'=1-\frac{e^x(x-z)}{\sin(x-z)}.
\]
所以
\[
\boxed{
\frac{du}{dx}
=f_x-\frac{y}{x}f_y
+\left[1-\frac{e^x(x-z)}{\sin(x-z)}\right]f_z }.
\]
其中 \(f_x,f_y,f_z\) 均在 \((x,y,z)\) 处取值。
\examnote{多层隐函数链式求导时，先分别求出内层函数导数，再代入总微分。}
\end{solutionblock}

\begin{problemblock}
\textbf{32.} 设变换
\[
u=x-2y,\qquad v=x+ay\quad(a\ne-2)
\]
可把方程
\[
6z_{xx}+z_{xy}-z_{yy}=0
\]
简化为
\[
z_{uv}=0.
\]
求常数 \(a\)。
\end{problemblock}

\begin{solutionblock}
\analysis{用算子变换：
\[
\partial_x=\partial_u+\partial_v,\qquad
\partial_y=-2\partial_u+a\partial_v.
\]}
有
\[
z_{xx}=z_{uu}+2z_{uv}+z_{vv},
\]
\[
z_{xy}=-2z_{uu}+(a-2)z_{uv}+az_{vv},
\]
\[
z_{yy}=4z_{uu}-4az_{uv}+a^2z_{vv}.
\]
代入
\[
6z_{xx}+z_{xy}-z_{yy}
\]
得
\[
(10+5a)z_{uv}+(6+a-a^2)z_{vv}.
\]
要化为 \(z_{uv}=0\)，需
\[
6+a-a^2=0.
\]
解得
\[
a=3\quad\text{或}\quad a=-2.
\]
题设 \(a\ne-2\)，故
\[
\boxed{a=3}.
\]
\examnote{二阶线性方程变量代换，目标是让 \(z_{uu}\)、\(z_{vv}\) 项系数消失。}
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 设函数 \(f(u)\) 有连续一阶导数，\(f(0)=2\)，且
\[
z=xf\left(\frac{y}{x}\right)+yf\left(\frac{y}{x}\right)
\]
满足
\[
\frac{\partial z}{\partial x}+\frac{\partial z}{\partial y}=\frac{y}{x}\qquad(x\ne0).
\]
求 \(z\) 的表达式。
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(v=y/x\)，则 \(z=(x+y)f(v)=x(1+v)f(v)\)。代入偏微分方程得到关于 \(f\) 的一阶线性方程。}
令
\[
v=\frac{y}{x}.
\]
则
\[
z=x(1+v)f(v).
\]
直接计算可得
\[
z_x+z_y=2f(v)+(1-v^2)f'(v).
\]
题设给出
\[
(1-v^2)f'(v)+2f(v)=v.
\]
这是线性方程：
\[
f'(v)+\frac{2}{1-v^2}f(v)=\frac{v}{1-v^2}.
\]
积分因子为
\[
\mu(v)=\frac{1+v}{1-v}.
\]
于是
\[
\left[\frac{1+v}{1-v}f(v)\right]'
=\frac{v}{(1-v)^2}.
\]
积分得
\[
\frac{1+v}{1-v}f(v)
=\frac{1}{1-v}+\ln(1-v)+C.
\]
由 \(f(0)=2\)，得
\[
1+C=2,\qquad C=1.
\]
所以
\[
f(v)=\frac{2-v+(1-v)\ln(1-v)}{1+v}.
\]
因此
\[
z=x(1+v)f(v)
=x\left[2-v+(1-v)\ln(1-v)\right].
\]
代回 \(v=y/x\)，得
\[
\boxed{z=2x-y+(x-y)\ln\left(1-\frac{y}{x}\right)}.
\]
\examnote{形如 \(f(y/x)\) 的题，令 \(v=y/x\) 是核心。}
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 设函数 \(f(x,y)\) 有连续二阶偏导数，满足
\[
\frac{\partial^2f}{\partial x\partial y}=0,
\]
且在极坐标系下可表示成
\[
f(x,y)=g(r),\qquad r=\sqrt{x^2+y^2}.
\]
求 \(f(x,y)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{径向函数 \(f=g(r)\) 的混合偏导含因子 \(xy[rg''(r)-g'(r)]\)。}
有
\[
f_x=g'(r)\frac{x}{r}.
\]
再对 \(y\) 求导：
\[
f_{xy}=xy\left(\frac{g''(r)}{r^2}-\frac{g'(r)}{r^3}\right)
=\frac{xy}{r^3}[rg''(r)-g'(r)].
\]
题设 \(f_{xy}=0\)，故
\[
rg''(r)-g'(r)=0.
\]
令 \(p=g'\)，则
\[
rp'-p=0,
\]
所以
\[
p=Cr.
\]
积分得
\[
g(r)=\frac C2r^2+D.
\]
因此
\[
\boxed{f(x,y)=A(x^2+y^2)+B}.
\]
\examnote{径向函数求偏导时，先写 \(r_x=x/r,\ r_y=y/r\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{35.} 设
\[
z=f\left(\sqrt{x^2+y^2}\right)
\]
具有二阶连续偏导数，且
\[
z_{xx}+z_{yy}-\frac1x z_x+z=x^2+y^2.
\]
求函数 \(z\) 的表达式。
\end{problemblock}

\begin{solutionblock}
\analysis{设 \(r=\sqrt{x^2+y^2}\)，径向函数满足
\[
z_{xx}+z_{yy}=f''(r)+\frac1r f'(r),\qquad \frac1x z_x=\frac1r f'(r).
\]
一阶项正好抵消。}
令
\[
r=\sqrt{x^2+y^2},\qquad z=f(r).
\]
则
\[
z_{xx}+z_{yy}=f''(r)+\frac1r f'(r),
\]
且
\[
\frac1x z_x=\frac1x f'(r)\frac{x}{r}=\frac1r f'(r).
\]
故方程化为
\[
f''(r)+f(r)=r^2.
\]
解此常微分方程：
\[
f(r)=C_1\cos r+C_2\sin r+r^2-2.
\]
由于 \(z=f(r)\) 在原点附近具有二阶连续偏导，需 \(f'(0)=0\)，故 \(C_2=0\)。于是
\[
\boxed{z=C\cos\sqrt{x^2+y^2}+x^2+y^2-2}.
\]
\examnote{径向 PDE 常能化为关于 \(r\) 的常微分方程；还要检查原点光滑性。}
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 求函数
\[
f(x,y)=x^4+y^4-(x+y)^2
\]
的极值。
\end{problemblock}

\begin{solutionblock}
\analysis{先求驻点，再用 Hessian 判别；判别失效的点需另作路径分析。}
一阶偏导为
\[
f_x=4x^3-2(x+y),\qquad
f_y=4y^3-2(x+y).
\]
令 \(f_x=f_y=0\)，相减得
\[
4(x^3-y^3)=0,
\]
所以
\[
x=y.
\]
代入
\[
4x^3-4x=0,
\]
得
\[
x=0,\ \pm1.
\]
驻点为
\[
(0,0),\quad(1,1),\quad(-1,-1).
\]
二阶偏导：
\[
f_{xx}=12x^2-2,\qquad f_{yy}=12y^2-2,\qquad f_{xy}=-2.
\]
在 \((1,1)\) 与 \((-1,-1)\) 处，
\[
A=10,\quad B=-2,\quad C=10,\quad AC-B^2=96>0,
\]
且 \(A>0\)，故均为极小值点。极小值为
\[
f(1,1)=f(-1,-1)=2-4=-2.
\]
在 \((0,0)\) 处 Hessian 判别失效。沿 \(y=-x\)，
\[
f(x,-x)=2x^4>0;
\]
沿 \(y=x\)，
\[
f(x,x)=2x^4-4x^2<0
\]
在 \(x\ne0\) 且充分小时成立，故 \((0,0)\) 不是极值点。

综上，函数在
\[
\boxed{(1,1),\ (-1,-1)}
\]
处取得极小值
\[
\boxed{-2},
\]
无极大值。
\examnote{Hessian 行列式为零时不能下结论，要用不同路径判断。}
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 求二元函数
\[
f(x,y)=\frac{x^2}{2+y^2}+y\ln y\qquad(y>0)
\]
的极值。
\end{problemblock}

\begin{solutionblock}
\analysis{先求驻点，再用 Hessian 判别。注意定义域要求 \(y>0\)。}
一阶偏导为
\[
f_x=\frac{2x}{2+y^2},
\]
\[
f_y=-\frac{2x^2y}{(2+y^2)^2}+\ln y+1.
\]
令 \(f_x=0\)，得
\[
x=0.
\]
再代入 \(f_y=0\)，得
\[
\ln y+1=0,\qquad y=e^{-1}.
\]
唯一驻点为
\[
\left(0,\frac1e\right).
\]
在该点，
\[
f_{xx}=\frac{2}{2+y^2}>0,\qquad f_{xy}=0,\qquad f_{yy}=\frac1y=e>0.
\]
Hessian 正定，故该点为极小值点。极小值为
\[
f\left(0,\frac1e\right)=\frac1e\ln\frac1e=-\frac1e.
\]
因此
\[
\boxed{\text{极小值 }-\frac1e,\text{ 在 }(0,1/e)\text{ 处取得；无极大值。}}
\]
\examnote{含 \(y\ln y\) 的题要先写明定义域 \(y>0\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{38.} 设
\[
z=f(xy,\,y g(x)),
\]
其中 \(f\) 具有二阶连续偏导数，函数 \(g(x)\) 可导且在 \(x=1\) 处取得极值，
\[
g(1)=1.
\]
求
\[
\left.\frac{\partial^2z}{\partial x\partial y}\right|_{(1,1)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(u=xy,\ v=yg(x)\)。因 \(g\) 在 \(x=1\) 处取极值，\(g'(1)=0\)。}
设
\[
u=xy,\qquad v=yg(x).
\]
则
\[
z_x=f_1u_x+f_2v_x
=y f_1+yg'(x)f_2.
\]
再对 \(y\) 求导：
\[
z_{xy}=f_1+y(f_{11}u_y+f_{12}v_y)
g'(x)f_2+yg'(x)(f_{21}u_y+f_{22}v_y).
\]
在 \((x,y)=(1,1)\) 处，
\[
u=1,\quad v=1,\quad u_y=1,\quad v_y=g(1)=1,\quad g'(1)=0.
\]
故
\[
\boxed{z_{xy}(1,1)=f_1(1,1)+f_{11}(1,1)+f_{12}(1,1)}.
\]
\examnote{极值条件 \(g'(1)=0\) 会消去一批链式法则项。}
\end{solutionblock}

\begin{problemblock}
\textbf{39.} 已知函数 \(f(u,v)\) 具有二阶连续偏导数，\(f(1,1)=2\) 是 \(f(u,v)\) 的极值，且
\[
z=f(x+y,\ f(x,y)).
\]
求
\[
\left.z_{xy}\right|_{(1,1)}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{按页图题面，外层 \(f\) 在 \((1,1)\) 处有极值，但 \(z(1,1)\) 的外层函数取值点是 \((2,2)\)，题目未给出 \(f\) 在 \((2,2)\) 处的偏导信息。}
在 \((x,y)=(1,1)\) 处，
\[
x+y=2,\qquad f(x,y)=f(1,1)=2.
\]
因此外层函数 \(f\) 的取值点为
\[
(2,2).
\]
而题设只给出
\[
f(1,1)=2
\]
是 \(f(u,v)\) 的极值，能推出的是
\[
f_u(1,1)=f_v(1,1)=0,
\]
并不能推出 \(f\) 在 \((2,2)\) 处的偏导数信息。

所以按页图题面，\(\left.z_{xy}\right|_{(1,1)}\) 不能由已知条件唯一确定。
\[
\boxed{\text{题面条件不足，无法唯一确定。}}
\]
\examnote{复合函数题必须核对“外层函数实际取值点”。极值点给的是 \((1,1)\)，但本题外层落在 \((2,2)\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{40.} 求由方程
\[
2x^2+2y^2+z^2+8xz-z+8=0
\]
所确定的函数 \(z=f(x,y)\) 的极值点。
\end{problemblock}

\begin{solutionblock}
\analysis{隐函数极值点满足 \(z_x=z_y=0\)。在 \(F_z\ne0\) 时，即 \(F_x=F_y=0\)。}
令
\[
F=2x^2+2y^2+z^2+8xz-z+8.
\]
则
\[
F_x=4x+8z,\qquad F_y=4y,\qquad F_z=2z+8x-1.
\]
极值点需满足
\[
F_x=0,\qquad F_y=0.
\]
故
\[
x=-2z,\qquad y=0.
\]
代入原方程：
\[
2(4z^2)+z^2+8(-2z)z-z+8=0,
\]
即
\[
7z^2+z-8=0.
\]
解得
\[
z=1,\qquad z=-\frac87.
\]
对应点为
\[
(-2,0,1),\qquad \left(\frac{16}{7},0,-\frac87\right).
\]
分类：在极值点处，
\[
z_{xx}=-\frac{F_{xx}}{F_z},\qquad z_{yy}=-\frac{F_{yy}}{F_z},\qquad z_{xy}=0.
\]
对 \((-2,0,1)\)，
\[
F_z=-15<0,
\]
Hessian 正定，故为极小值点。对 \((16/7,0,-8/7)\)，
\[
F_z=15>0,
\]
Hessian 负定，故为极大值点。

所以
\[
\boxed{(-2,0)\text{ 是极小值点},\quad (16/7,0)\text{ 是极大值点}.}
\]
\examnote{隐函数极值点先解 \(F_x=F_y=0\)，再用二阶隐导判别。}
\end{solutionblock}

\begin{problemblock}
\textbf{41.} 设 \(f(x,y)\) 有二阶连续偏导数，
\[
g(x,y)=f(e^{xy},x^2+y^2),
\]
且
\[
f(x,y)=1-x-y+o\bigl((x-1)^2+y^2\bigr).
\]
证明 \(g(x,y)\) 在 \((0,0)\) 取得极值，判断此极值是极大值还是极小值，并求出此极值。
\end{problemblock}

\begin{solutionblock}
\analysis{把 \(e^{xy}\) 和 \(x^2+y^2\) 代入 \(f\) 在 \((1,0)\) 附近的展开。}
由展开式得
\[
f(1,0)=0.
\]
当 \((x,y)\to(0,0)\) 时，
\[
e^{xy}=1+xy+o(x^2+y^2),
\]
且
\[
x^2+y^2=o(1).
\]
代入
\[
f(X,Y)=1-X-Y+o((X-1)^2+Y^2),
\]
其中
\[
X=e^{xy},\qquad Y=x^2+y^2.
\]
得
\[
g(x,y)
=1-e^{xy}-(x^2+y^2)+o(x^2+y^2).
\]
因此
\[
g(x,y)
=-xy-x^2-y^2+o(x^2+y^2).
\]
二次型
\[
x^2+xy+y^2
\]
正定，所以
\[
-x^2-xy-y^2
\]
负定。故 \(g\) 在 \((0,0)\) 取得极大值，极大值为
\[
g(0,0)=f(1,0)=\boxed{0}.
\]
\examnote{复合极值题常通过局部展开转化为二次型正负定判断。}
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 求函数
\[
f(x,y)=x^2+2y^2-x^2y^2
\]
在区域
\[
D=\{(x,y)\mid x^2+y^2\le4,\ y\ge0\}
\]
上的最大值和最小值。
\end{problemblock}

\begin{solutionblock}
\analysis{闭区域上连续函数必有最值。分别考察内部驻点、直径边界 \(y=0\) 与半圆边界 \(x^2+y^2=4\)。}
内部驻点满足
\[
f_x=2x(1-y^2)=0,\qquad
f_y=2y(2-x^2)=0.
\]
在内部 \(y>0\)，得
\[
y=1,\qquad x=\pm\sqrt2,
\]
函数值为
\[
f(\pm\sqrt2,1)=2.
\]
边界 \(y=0\) 上，
\[
f=x^2,\qquad 0\le x^2\le4,
\]
故取值范围为 \([0,4]\)。

边界 \(x^2+y^2=4,\ y\ge0\) 上，令 \(s=x^2\)，则 \(y^2=4-s\)，
\[
f=s+2(4-s)-s(4-s)=s^2-5s+8,\qquad 0\le s\le4.
\]
该二次函数在 \(s=5/2\) 处取最小值 \(7/4\)，在端点处最大值为 \(8\)。

综合比较，最小值为
\[
\boxed{0}
\]
在 \((0,0)\) 处取得；最大值为
\[
\boxed{8}
\]
在 \((0,2)\) 处取得。
\examnote{闭区域最值题按“内部驻点 + 各段边界”逐项比较。}
\end{solutionblock}

\begin{problemblock}
\textbf{43.} 设函数 \(z=z(x,y)\) 的微分为
\[
dz=\left(2x+\frac12y\right)dx+\left(\frac12x+4y\right)dy,
\]
且 \(z(0,0)=0\)。求 \(z=z(x,y)\) 在
\[
4x^2+y^2\le25
\]
上的最大值。
\end{problemblock}

\begin{solutionblock}
\analysis{先由全微分还原 \(z\)，再在椭圆上求正定二次型最大值。}
由
\[
z_x=2x+\frac12y
\]
积分得
\[
z=x^2+\frac12xy+\varphi(y).
\]
再由
\[
z_y=\frac12x+\varphi'(y)=\frac12x+4y
\]
得
\[
\varphi(y)=2y^2+C.
\]
由 \(z(0,0)=0\)，得 \(C=0\)。故
\[
z=x^2+\frac12xy+2y^2.
\]
令
\[
X=2x,\qquad Y=y,
\]
则约束为
\[
X^2+Y^2\le25,
\]
且
\[
z=\frac14X^2+\frac14XY+2Y^2.
\]
对应矩阵为
\[
\begin{pmatrix}
1/4&1/8\\
1/8&2
\end{pmatrix}.
\]
其最大特征值为
\[
\lambda_{\max}=\frac{9+5\sqrt2}{8}.
\]
所以最大值为
\[
\boxed{\frac{25(9+5\sqrt2)}{8}}.
\]
\examnote{椭圆约束下二次型最值，可先把椭圆化成圆，再求矩阵特征值。}
\end{solutionblock}

\begin{problemblock}
\textbf{44.} 求函数
\[
u=xy+2yz
\]
在约束条件
\[
x^2+y^2+z^2=10
\]
下的最大值和最小值。
\end{problemblock}

\begin{solutionblock}
\analysis{这是球面上二次型最值，等于半径平方乘矩阵特征值。}
写成二次型
\[
u=
\begin{pmatrix}x&y&z\end{pmatrix}
\begin{pmatrix}
0&1/2&0\\
1/2&0&1\\
0&1&0
\end{pmatrix}
\begin{pmatrix}x\\y\\z\end{pmatrix}.
\]
该矩阵特征值为
\[
0,\quad \frac{\sqrt5}{2},\quad -\frac{\sqrt5}{2}.
\]
在
\[
x^2+y^2+z^2=10
\]
上，二次型最大值和最小值分别为
\[
10\cdot\frac{\sqrt5}{2}=5\sqrt5,
\]
\[
10\cdot\left(-\frac{\sqrt5}{2}\right)=-5\sqrt5.
\]
故
\[
\boxed{u_{\max}=5\sqrt5,\qquad u_{\min}=-5\sqrt5}.
\]
\examnote{球面约束下的二次型最值就是特征值问题。}
\end{solutionblock}

\begin{problemblock}
\textbf{45.} 求函数
\[
u=x^2+y^2+z^2
\]
在约束条件
\[
z=x^2+y^2,\qquad x+y+z=4
\]
下的最大值与最小值。
\end{problemblock}

\begin{solutionblock}
\analysis{由第一个约束令 \(z=x^2+y^2\)，则目标化为 \(u=z+z^2\)。再确定 \(z\) 的可取范围。}
由
\[
z=x^2+y^2
\]
和
\[
x+y+z=4
\]
得
\[
x+y=4-z.
\]
对实数 \(x,y\)，有
\[
(x+y)^2\le2(x^2+y^2)=2z.
\]
所以
\[
(4-z)^2\le2z.
\]
即
\[
z^2-10z+16\le0,
\]
故
\[
2\le z\le8.
\]
目标函数
\[
u=x^2+y^2+z^2=z+z^2
\]
在 \(z\ge0\) 上单调递增，因此
\[
u_{\min}=2+2^2=6,
\]
\[
u_{\max}=8+8^2=72.
\]
当 \(z=2\) 时，\(x+y=2,\ x^2+y^2=2\)，得 \(x=y=1\)。当 \(z=8\) 时，\(x+y=-4,\ x^2+y^2=8\)，得 \(x=y=-2\)。
故
\[
\boxed{u_{\min}=6,\quad u_{\max}=72}.
\]
\examnote{多个约束时，能消元先消元；本题消成单变量 \(z\) 最快。}
\end{solutionblock}

\begin{problemblock}
\textbf{46.} 在椭圆
\[
3x^2+2xy+3y^2=1
\]
的第一象限部分上求一点，使该点的切线与两坐标轴所围成三角形面积最小，并求面积的最小值。
\end{problemblock}

\begin{solutionblock}
\analysis{二次曲线 \(Q(x,y)=1\) 在点 \((x_0,y_0)\) 处的切线可由极化写出。}
设切点为 \((x_0,y_0)\)。椭圆对应二次型
\[
Q=3x^2+2xy+3y^2.
\]
切线为
\[
(3x_0+y_0)x+(x_0+3y_0)y=1.
\]
两截距分别为
\[
a=\frac1{3x_0+y_0},\qquad
b=\frac1{x_0+3y_0}.
\]
面积
\[
S=\frac12ab
=\frac1{2(3x_0+y_0)(x_0+3y_0)}.
\]
要使 \(S\) 最小，需使
\[
P=(3x+y)(x+3y)
=3x^2+10xy+3y^2
\]
最大，且
\[
3x^2+2xy+3y^2=1.
\]
注意
\[
P=1+8xy.
\]
在第一象限内，由对称性或 \(x,y\) 的乘积最大条件，取
\[
x=y.
\]
代入约束：
\[
8x^2=1,
\qquad x=y=\frac1{2\sqrt2}.
\]
此时
\[
P=2,
\]
所以
\[
S_{\min}=\frac1{2P}=\boxed{\frac14}.
\]
所求点为
\[
\boxed{\left(\frac1{2\sqrt2},\frac1{2\sqrt2}\right)}.
\]
\examnote{椭圆切线截距面积题，常把面积最小转为截距分母乘积最大。}
\end{solutionblock}

\begin{problemblock}
\textbf{47.}（仅数学一要求）已知曲线
\[
C:\begin{cases}
x^2+y^2-2z^2=0,\\
x+y+3z=5.
\end{cases}
\]
求 \(C\) 上距离 \(xOy\) 面最远的点和最近的点。
\end{problemblock}

\begin{solutionblock}
\analysis{到 \(xOy\) 面距离为 \(|z|\)。由约束推出 \(z\) 的取值范围。}
由平面方程
\[
x+y=5-3z.
\]
又
\[
x^2+y^2=2z^2.
\]
实数 \(x,y\) 满足
\[
(x+y)^2\le2(x^2+y^2)=4z^2.
\]
所以
\[
(5-3z)^2\le4z^2.
\]
化简：
\[
z^2-6z+5\le0,
\]
故
\[
1\le z\le5.
\]
因此最近点对应 \(z=1\)，最远点对应 \(z=5\)。

当 \(z=1\) 时，
\[
x+y=2,\quad x^2+y^2=2,
\]
得
\[
x=y=1.
\]
最近点为
\[
\boxed{(1,1,1)}.
\]
当 \(z=5\) 时，
\[
x+y=-10,\quad x^2+y^2=50,
\]
得
\[
x=y=-5.
\]
最远点为
\[
\boxed{(-5,-5,5)}.
\]
\examnote{距离坐标面最远/最近，本质是求对应坐标绝对值的范围。}
\end{solutionblock}

\begin{problemblock}
\textbf{48.}（仅数学一要求）求椭球面
\[
\frac{x^2}{3}+\frac{y^2}{2}+z^2=1
\]
被平面
\[
x+y+z=0
\]
截得的椭圆长半轴与短半轴之长。
\end{problemblock}

\begin{solutionblock}
\analysis{中心截面椭圆的半轴由二次型
\[
\operatorname{diag}(1/3,1/2,1)
\]
限制在平面 \(x+y+z=0\) 上的特征值决定。}
取平面 \(x+y+z=0\) 的一组标准正交基
\[
e_1=\frac{1}{\sqrt2}(1,-1,0),\qquad
e_2=\frac{1}{\sqrt6}(1,1,-2).
\]
在该基下，二次型矩阵为
\[
\begin{pmatrix}
5/12&-1/(12\sqrt3)\\
-1/(12\sqrt3)&29/36
\end{pmatrix}.
\]
其特征值为
\[
\lambda_1=\frac{11-\sqrt{13}}{18},\qquad
\lambda_2=\frac{11+\sqrt{13}}{18}.
\]
截面椭圆方程化为
\[
\lambda_1 \xi^2+\lambda_2\eta^2=1.
\]
故长半轴为
\[
a=\frac1{\sqrt{\lambda_1}}
=\sqrt{\frac{18}{11-\sqrt{13}}}
=\boxed{\sqrt{\frac{11+\sqrt{13}}{6}}},
\]
短半轴为
\[
b=\frac1{\sqrt{\lambda_2}}
=\sqrt{\frac{18}{11+\sqrt{13}}}
=\boxed{\sqrt{\frac{11-\sqrt{13}}{6}}}.
\]
\examnote{中心椭球被过原点平面截得椭圆，半轴长度来自限制二次型的特征值。}
\end{solutionblock}

\begin{problemblock}
\textbf{49.} 已知 \(p>1\)，
\[
\frac1p+\frac1q=1,\qquad x,y>0.
\]
证明：
\[
xy\le \frac{x^p}{p}+\frac{y^q}{q}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是 Young 不等式。可由凸函数或一元函数最小值证明。}
固定 \(y>0\)，考虑
\[
\phi(x)=\frac{x^p}{p}-xy+\frac{y^q}{q}.
\]
则
\[
\phi'(x)=x^{p-1}-y.
\]
令 \(\phi'(x)=0\)，得
\[
x=y^{1/(p-1)}.
\]
由
\[
\phi''(x)=(p-1)x^{p-2}>0,
\]
该点为最小点。

又由
\[
\frac1p+\frac1q=1
\]
得
\[
q=\frac{p}{p-1}.
\]
在 \(x=y^{1/(p-1)}\) 处，
\[
x^p=y^{p/(p-1)}=y^q,
\]
且
\[
xy=y^{1+1/(p-1)}=y^q.
\]
所以
\[
\phi_{\min}=\frac{y^q}{p}-y^q+\frac{y^q}{q}
=y^q\left(\frac1p+\frac1q-1\right)=0.
\]
故对任意 \(x,y>0\)，
\[
\phi(x)\ge0,
\]
即
\[
\boxed{xy\le \frac{x^p}{p}+\frac{y^q}{q}}.
\]
\examnote{Young 不等式是 Hölder、Minkowski 等不等式的基础，考研中常用一元函数最值证明。}
\end{solutionblock}

\begin{problemblock}
\textbf{52.} 设 \(f(x,y)\) 在圆域
\[
x^2+y^2\le1
\]
上有连续一阶偏导数，且 \(|f(x,y)|\le1\)。求证在单位圆内至少有一点
\((x_0,y_0)\)，可使
\[
\left[\frac{\partial f(x_0,y_0)}{\partial x}\right]^2+
\left[\frac{\partial f(x_0,y_0)}{\partial y}\right]^2<16.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{题目要证明“存在一点梯度模小于 \(4\)”。这类题不能只沿某一条直径套中值定理，因为一维中值定理只能控制某个方向导数，不能直接控制整个梯度模。关键是从反面看：若处处 \(|\nabla f|\ge4\)，沿最速下降方向每走单位长度，函数值至少下降 \(4\)，而题设 \(|f|\le1\) 只允许函数值总变化不超过 \(2\)，这会与单位圆的半径为 \(1\) 冲突。}

记
\[
D=\{(x,y):x^2+y^2\le1\},\qquad \nabla f=(f_x,f_y).
\]
用反证法。假设结论不成立，则对任意 \((x,y)\in D\)，都有
\[
f_x^2(x,y)+f_y^2(x,y)\ge16,
\]
即
\[
|\nabla f(x,y)|\ge4.
\]
特别地，\(\nabla f\) 在 \(D\) 内处处不为零。

从圆心 \(O=(0,0)\) 出发，沿函数的最速下降方向作曲线 \(\gamma(s)\)，并用弧长 \(s\) 作参数：
\[
\gamma(0)=O,\qquad
\gamma'(s)=-\frac{\nabla f(\gamma(s))}{|\nabla f(\gamma(s))|}.
\]
由于 \(\nabla f\) 连续且在反设下不为零，上式所给方向场连续，故这样的下降曲线在到达边界前可以存在。又因为
\[
|\gamma'(s)|=1,
\]
所以参数 \(s\) 正是从圆心走过的路程。

沿这条曲线对 \(f(\gamma(s))\) 求导，得
\[
\frac{\mathrm d}{\mathrm ds}f(\gamma(s))
=\nabla f(\gamma(s))\cdot \gamma'(s)
=-|\nabla f(\gamma(s))|
\le -4.
\]
于是只要曲线仍在圆域内，就有
\[
f(\gamma(s))\le f(O)-4s.
\]
而题设给出
\[
-1\le f(O)\le1,\qquad -1\le f(\gamma(s))\le1.
\]
若曲线在圆域内至少走到 \(s=\frac12\)，则
\[
f(\gamma(1/2))\le f(O)-2\le -1.
\]
并且当 \(f(O)<1\) 时右端严格小于 \(-1\)，直接矛盾；当 \(f(O)=1\) 时，由于一开始导数
\[
\frac{\mathrm d}{\mathrm ds}f(\gamma(s))\le-4
\]
且处处梯度不小于 \(4\)，任取 \(s>\frac12\) 便得到
\[
f(\gamma(s))< -1,
\]
仍与 \(|f|\le1\) 矛盾。故下降曲线不可能在圆域内走到长度 \(\frac12\)。

但是从圆心到单位圆边界的最短距离等于 \(1\)。任何从圆心出发、在长度小于 \(1\) 时到达边界的曲线都不存在，因为曲线长度至少不小于两端点的直线距离。因此下降曲线若要离开单位圆，至少要走 \(1\) 的路程；而上面推出它在走到 \(\frac12\) 之前就已经不可能继续留在圆域内。矛盾。

所以反设不成立，必存在 \((x_0,y_0)\in D\)，使
\[
|\nabla f(x_0,y_0)|<4,
\]
即
\[
\boxed{
\left[\frac{\partial f(x_0,y_0)}{\partial x}\right]^2+
\left[\frac{\partial f(x_0,y_0)}{\partial y}\right]^2<16
}.
\]

\examnote{本题的考研要点是把 \(f_x^2+f_y^2\) 识别为梯度模平方。若只证明某点某个方向导数小于 \(4\)，并不能推出梯度模小于 \(4\)；必须利用二维区域的整体几何约束。}
\end{solutionblock}

\section{本章小结}
第五章原题中可见题号已全部补充解析。第 \(25\) 题与第 \(39\) 题按题面文字存在条件不足之处，解析中已给出说明与反例，便于复习时和原书勘误核对。
"""


CH06_TEX = r"""\chapter{二重积分}

\section{原题页索引}
本章原题对应做题本第 96--111 页。第 109 页原题题号从 \(34\) 跳到 \(36\)，原书可见页面中未出现第 \(35\) 题。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_096.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 设 \(f(x,y)\) 连续，判断下列二次积分换序结果。
\begin{enumerate}
\item \(\displaystyle \int_1^2 dx\int_x^2 f(x,y)\,dy+\int_1^2dy\int_y^{4-y}f(x,y)\,dx\).
\item \(\displaystyle \int_{\pi/2}^{\pi}dx\int_{\sin x}^1 f(x,y)\,dy\).
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{换序题的核心是还原积分区域。本题两问都是选择题，答案分别为 C、B。}
\begin{enumerate}
\item 第一部分区域为
\[
1\le x\le2,\qquad x\le y\le2,
\]
换成 \(y\) 先固定时是 \(1\le y\le2,\,1\le x\le y\)。第二部分已经是
\[
1\le y\le2,\qquad y\le x\le4-y.
\]
合并后
\[
1\le y\le2,\qquad 1\le x\le4-y.
\]
故
\[
\boxed{\int_1^2dy\int_1^{4-y}f(x,y)\,dx}.
\]
\item 原区域为
\[
\frac{\pi}{2}\le x\le\pi,\qquad \sin x\le y\le1.
\]
当 \(0\le y\le1\) 时，在 \([\pi/2,\pi]\) 上满足 \(\sin x\le y\) 的 \(x\) 为
\[
\pi-\arcsin y\le x\le\pi.
\]
故
\[
\boxed{\int_0^1dy\int_{\pi-\arcsin y}^{\pi}f(x,y)\,dx}.
\]
\end{enumerate}
\examnote{含三角函数的换序要先看反三角函数所在象限；本题不能把下限误写成 \(\arcsin y\)。}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 将极坐标形式的累次积分改写为直角坐标积分。
\begin{enumerate}
\item \(\displaystyle \int_{\pi/4}^{\pi/2}d\theta\int_0^{2\sin\theta} f(r\cos\theta,r\sin\theta)\,r\,dr\).
\item \(\displaystyle \int_0^{\pi/4}d\theta\int_0^{2\cos\theta} f(r\cos\theta,r\sin\theta)\,r\,dr\).
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{先把极坐标边界化成圆，再结合角度限制确定区域。}
\begin{enumerate}
\item \(r=2\sin\theta\) 化为
\[
x^2+(y-1)^2=1.
\]
又 \(\pi/4\le\theta\le\pi/2\)，故区域在圆内且 \(y\ge x,x\ge0\)。按 \(x\) 积分可写成
\[
\boxed{\int_0^1dx\int_x^{1+\sqrt{1-x^2}}f(x,y)\,dy}.
\]
选择题答案为 D。
\item \(r=2\cos\theta\) 化为
\[
(x-1)^2+y^2=1.
\]
又 \(0\le\theta\le\pi/4\)，故区域在圆内且 \(0\le y\le x\)。按 \(y\) 积分为
\[
\boxed{\int_0^1dy\int_y^{1+\sqrt{1-y^2}}f(x,y)\,dx}.
\]
选择题答案为 B。
\end{enumerate}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 设 \(f(x,y)\) 连续，求
\[
\int_0^{\pi/4}d\theta\int_0^1f(r\cos\theta,r\sin\theta)\,r\,dr
\]
对应的直角坐标形式。
\end{problemblock}

\begin{solutionblock}
\analysis{这是单位圆第一象限内 \(0\le\theta\le\pi/4\) 的扇形，即 \(0\le y\le x\)。}
区域为
\[
x^2+y^2\le1,\qquad 0\le y\le x.
\]
按 \(y\) 先固定，
\[
0\le y\le\frac{\sqrt2}{2},\qquad y\le x\le\sqrt{1-y^2}.
\]
故
\[
\boxed{\int_0^{\sqrt2/2}dy\int_y^{\sqrt{1-y^2}}f(x,y)\,dx}.
\]
选择题答案为 C。
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 设 \(f(x,y)\) 连续，判断
\[
\int_0^1dy\int_{-\sqrt{1-y^2}}^{1-y}f(x,y)\,dx
\]
的极坐标形式。
\end{problemblock}

\begin{solutionblock}
\analysis{左边界是单位圆左半弧，右边界是直线 \(x+y=1\)。}
区域在上半平面。极坐标下直线为
\[
r(\cos\theta+\sin\theta)=1.
\]
当 \(0\le\theta\le\pi/2\) 时，边界先遇到直线；当 \(\pi/2\le\theta\le\pi\) 时，边界为单位圆。因此
\[
\boxed{
\int_0^{\pi/2}d\theta\int_0^{1/(\cos\theta+\sin\theta)}
 f(r\cos\theta,r\sin\theta)\,r\,dr
+\int_{\pi/2}^{\pi}d\theta\int_0^1
 f(r\cos\theta,r\sin\theta)\,r\,dr}.
\]
选择题答案为 D。
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 设区域 \(D\) 由 \(y=\sin x,\ x=\pm\frac{\pi}{2},\ y=1\) 围成，求
\[
\iint_D(xy^5-1)\,dxdy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{区域关于 \(y\) 轴对称，\(xy^5\) 关于 \(x\) 为奇函数。}
因此
\[
\iint_D xy^5\,dxdy=0.
\]
区域面积为
\[
S_D=\int_{-\pi/2}^{\pi/2}(1-\sin x)\,dx=\pi.
\]
故
\[
\iint_D(xy^5-1)\,dxdy=-S_D=\boxed{-\pi}.
\]
选择题答案为 D。
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 设 \(f(x,y)\) 连续，且
\[
f(x,y)=xy+\iint_D f(x,y)\,dxdy,
\]
其中 \(D\) 由 \(y=0,y=x^2,x=1\) 围成，求 \(f(x,y)\)。
\end{problemblock}

\begin{solutionblock}
\analysis{把积分项看成常数 \(C\)，再由两边积分确定 \(C\)。}
令
\[
C=\iint_D f(x,y)\,dxdy.
\]
则
\[
f(x,y)=xy+C.
\]
又
\[
D:\quad 0\le x\le1,\quad 0\le y\le x^2,
\]
所以
\[
C=\int_0^1dx\int_0^{x^2}(xy+C)\,dy
=\frac1{12}+\frac{C}{3}.
\]
解得
\[
C=\frac18.
\]
故
\[
\boxed{f(x,y)=xy+\frac18}.
\]
选择题答案为 C。
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 设 \(0<a<1\)，区域 \(D\) 由坐标轴、直线 \(x+y=a\) 与 \(x+y=1\) 围成，比较
\[
I=\iint_D\sin^2(x+y)\,d\sigma,\quad
J=\iint_D\ln^3(x+y)\,d\sigma,\quad
K=\iint_D(x+y)\,d\sigma.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(u=x+y\)。在本区域内 \(a\le u\le1\)，横截长度为 \(u\)。}
因为 \(0<u<1\) 时
\[
\ln^3u<0,\qquad 0<\sin^2u<u,
\]
所以逐点比较得
\[
\ln^3(x+y)<\sin^2(x+y)<x+y.
\]
积分保持不等号，故
\[
\boxed{J<I<K}.
\]
选择题答案为 D。
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 比较
\[
I=\iint_{|x|+|y|\le1}(x^2+y^3)\,d\sigma,\quad
J=\iint_{x^2+y^2\le1}(x^4-y^4)\,d\sigma,\quad
K=\iint_{x^2+y^2\le1}(x^3-y^2)\,d\sigma.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{对称性是本题最快方法。}
在菱形区域中，\(y^3\) 为关于 \(y\) 的奇函数，积分为零，故
\[
I=\iint_{|x|+|y|\le1}x^2\,d\sigma>0.
\]
单位圆关于 \(x,y\) 对称，故
\[
J=\iint(x^4-y^4)\,d\sigma=0.
\]
又 \(x^3\) 关于 \(x\) 为奇函数，故
\[
K=-\iint_{x^2+y^2\le1}y^2\,d\sigma<0.
\]
于是
\[
\boxed{K<J<I}.
\]
选择题答案为 D。
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 设
\[
I_1=\iint_D\frac{x+y}{4}\,d\sigma,\quad
I_2=\iint_D\sqrt{\frac{x+y}{4}}\,d\sigma,\quad
I_3=\iint_D\sqrt[3]{\frac{x+y}{4}}\,d\sigma,
\]
其中 \(D:(x-1)^2+(y-1)^2\le2\)。比较三者大小。
\end{problemblock}

\begin{solutionblock}
\analysis{圆盘上 \(0\le (x+y)/4\le1\)，比较 \(u,u^{1/2},u^{1/3}\) 即可。}
令
\[
u=\frac{x+y}{4}.
\]
在 \(D\) 上，\(x+y\) 的最小值为 \(0\)，最大值为 \(4\)，故 \(0\le u\le1\)。当 \(0<u<1\) 时
\[
u<u^{1/2}<u^{1/3}.
\]
因此
\[
\boxed{I_1<I_2<I_3}.
\]
选择题答案为 A。
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 正方形 \(|x|\le1,|y|\le1\) 被对角线划分成四个区域 \(D_k\)，
\[
I_k=\iint_{D_k}y\cos x\,dxdy.
\]
求 \(\max I_k\)。
\end{problemblock}

\begin{solutionblock}
\analysis{在 \([-1,1]\) 上 \(\cos x>0\)，积分大小主要由 \(y\) 的符号决定。}
图中 \(D_1\) 位于上方，\(y>0\)，故 \(I_1>0\)。\(D_3\) 位于下方，故 \(I_3<0\)。左右两个区域关于 \(x\) 轴对称，\(y\cos x\) 关于 \(y\) 为奇函数，故
\[
I_2=I_4=0.
\]
所以最大者为
\[
\boxed{I_1}.
\]
选择题答案为 A。
\end{solutionblock}

\begin{problemblock}
\textbf{11.} \(D_k\) 是单位圆域在第 \(k\) 象限的部分，
\[
I_k=\iint_{D_k}(y-x)\,dxdy.
\]
判断哪个 \(I_k>0\)。
\end{problemblock}

\begin{solutionblock}
\analysis{第一象限中 \(x,y\) 对称，第二象限中 \(y-x\) 恒正。}
第一象限
\[
\iint_{D_1}y\,d\sigma=\iint_{D_1}x\,d\sigma,
\]
故 \(I_1=0\)。第二象限有 \(y\ge0,x\le0\)，且除边界外 \(y-x>0\)，故
\[
I_2>0.
\]
第三象限 \(y-x\) 的积分仍因对称为 \(0\)，第四象限 \(y-x<0\)。故答案为
\[
\boxed{I_2>0}.
\]
选择题答案为 B。
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 已知
\[
\lim_{t\to0^+}\frac{\displaystyle\int_0^t dx\int_t^x e^{-y^2}\,dy}{t^\alpha}=\beta\ne0,
\]
求 \(\alpha,\beta\)。
\end{problemblock}

\begin{solutionblock}
\analysis{小区域极限先用 \(e^{-y^2}\sim1\) 抓主部。注意内层上限 \(x<t\)，积分为负。}
当 \(t\to0^+\) 时，
\[
\int_t^x e^{-y^2}\,dy\sim x-t.
\]
故分子
\[
\int_0^t(x-t)\,dx=-\frac{t^2}{2}.
\]
要使极限为非零常数，应取
\[
\alpha=2,\qquad \beta=-\frac12.
\]
选择题答案为 C。
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 交换积分次序：
\[
\int_0^4dx\int_{\sqrt{4x-x^2}}^{2\sqrt{x}}f(x,y)\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{边界 \(y=\sqrt{4x-x^2}\) 是圆 \((x-2)^2+y^2=4\) 的上半部分，\(y=2\sqrt{x}\) 是抛物线 \(x=y^2/4\)。水平切片时区域分成两块。}
原区域满足
\[
0\le x\le4,\qquad \sqrt{4x-x^2}\le y\le2\sqrt{x}.
\]
等价于
\[
y^2\le4x,\qquad y^2\ge4x-x^2.
\]
当 \(0\le y\le2\) 时，圆的不等式给出两段；当 \(2\le y\le4\) 时只受抛物线限制。故
\[
\boxed{
\int_0^2dy\left(
\int_{y^2/4}^{\,2-\sqrt{4-y^2}} f(x,y)\,dx
+\int_{2+\sqrt{4-y^2}}^{4} f(x,y)\,dx\right)
+\int_2^4dy\int_{y^2/4}^{4}f(x,y)\,dx }.
\]
\examnote{本题最易漏掉 \(0\le y\le2\) 时右侧的小区域。}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 交换积分次序：
\[
\int_0^2dx\int_x^{\sqrt{2x-x^2}}f(x,y)\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{题面外层到 \(2\)，但当 \(1<x<2\) 时上限 \(\sqrt{2x-x^2}\) 小于下限 \(x\)，所以这是有向积分。应拆成正向区域减去反向区域。}
先写成
\[
I=\int_0^1dx\int_x^{\sqrt{2x-x^2}}f\,dy
-\int_1^2dx\int_{\sqrt{2x-x^2}}^x f\,dy.
\]
第一块区域为
\[
0\le y\le1,\qquad 1-\sqrt{1-y^2}\le x\le y.
\]
第二块区域分为
\[
0\le y\le1,\quad 1+\sqrt{1-y^2}\le x\le2,
\]
以及
\[
1\le y\le2,\quad y\le x\le2.
\]
因此
\[
\boxed{
I=\int_0^1dy\int_{1-\sqrt{1-y^2}}^y f(x,y)\,dx
-\int_0^1dy\int_{1+\sqrt{1-y^2}}^2f(x,y)\,dx
-\int_1^2dy\int_y^2f(x,y)\,dx }.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 计算
\[
\int_0^1dx\int_{x^2}^{1}\frac{xy}{\sqrt{1+y^3}}\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{先换序，内层对 \(x\) 积分即可。}
区域为
\[
0\le x\le1,\qquad x^2\le y\le1,
\]
即
\[
0\le y\le1,\qquad 0\le x\le\sqrt y.
\]
于是
\[
\begin{aligned}
I&=\int_0^1dy\int_0^{\sqrt y}\frac{xy}{\sqrt{1+y^3}}\,dx\\
&=\frac12\int_0^1\frac{y^2}{\sqrt{1+y^3}}\,dy
=\frac13(\sqrt2-1).
\end{aligned}
\]
故
\[
\boxed{\frac{\sqrt2-1}{3}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 计算
\[
\int_0^1dy\int_{y/2}^{y}\cos x^2\,dx
+\int_1^2dy\int_{y/2}^{1}\cos x^2\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{被积函数只含 \(x\)，换序后内层长度会变成 \(x\)。}
两个区域合并为
\[
0\le x\le1,\qquad x\le y\le2x.
\]
故
\[
I=\int_0^1dx\int_x^{2x}\cos x^2\,dy
=\int_0^1x\cos x^2\,dx
=\boxed{\frac12\sin1}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 计算
\[
\int_0^1dy\int_y^1(x^2-y^2)\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{本题直接积分即可，也可先换序。}
\[
\begin{aligned}
I&=\int_0^1\left[\frac{x^3}{3}-y^2x\right]_{x=y}^{1}dy\\
&=\int_0^1\left(\frac13-y^2+\frac23y^3\right)dy
=\boxed{\frac16}.
\end{aligned}
\]
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 计算
\[
\iint_{x^2+y^2\le1}\left((x+1)^2+2y^2\right)\,dxdy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{单位圆上奇函数项积分为零，且 \(\iint x^2=\iint y^2=\pi/4\)。}
展开得
\[
(x+1)^2+2y^2=x^2+2x+1+2y^2.
\]
故
\[
I=\frac{\pi}{4}+0+\pi+2\cdot\frac{\pi}{4}
=\boxed{\frac{7\pi}{4}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{19.} 设 \(D=\{(x,y):0\le x\le1,0\le y\le1\}\)，讨论
\[
\iint_D\frac{dxdy}{x^2+y^2}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{唯一问题在原点，这是二重反常积分。}
在第一象限靠近原点的小扇形内，用极坐标有
\[
\frac{1}{x^2+y^2}\,dxdy=\frac1{r^2}\cdot r\,drd\theta=\frac{dr}{r}d\theta.
\]
而
\[
\int_0^\varepsilon\frac{dr}{r}=+\infty.
\]
所以该反常积分
\[
\boxed{\text{发散，且趋于 }+\infty}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 计算
\[
I=\int_0^{\pi/2}d\theta\int_0^{2\cos\theta}
\left[(r\cos\theta-1)^3+r\sin\theta\right]r\,dr.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{区域是圆 \((x-1)^2+y^2\le1\) 的上半部分。}
令 \(u=x-1\)，则 \((x-1)^3=u^3\)。区域关于 \(u=0\) 对称，所以
\[
\iint_Du^3\,d\sigma=0.
\]
剩下
\[
I=\iint_D y\,d\sigma.
\]
这是半径为 \(1\) 的上半圆对 \(x\) 轴的一阶矩：
\[
\int_{-1}^1du\int_0^{\sqrt{1-u^2}}y\,dy
=\frac12\int_{-1}^1(1-u^2)\,du
=\boxed{\frac23}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 求极限
\[
\lim_{t\to0^+}\frac1{\sin^2t}\int_0^t dx\int_x^t e^{-(x-y)^2}\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{小三角形面积给出主部，\(e^{-(x-y)^2}\to1\)，\(\sin^2t\sim t^2\)。}
\[
\int_0^t dx\int_x^t e^{-(x-y)^2}\,dy
\sim \int_0^t(t-x)\,dx=\frac{t^2}{2}.
\]
因此
\[
\boxed{\frac12}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 设
\[
f(t)=\int_0^t dx\int_x^{\sqrt{x}}\frac{\sin y}{y}\,dy,
\]
求 \(f(t)\) 在 \([0,\pi]\) 上的最大值。
\end{problemblock}

\begin{solutionblock}
\analysis{先由变上限求导确定最大点，再换序计算最大值。}
由微积分基本定理，
\[
f'(t)=\int_t^{\sqrt t}\frac{\sin y}{y}\,dy.
\]
当 \(0<t<1\) 时，\(\sqrt t>t\)，且 \(\sin y/y>0\)，故 \(f'(t)>0\)；当 \(1<t\le\pi\) 时，\(\sqrt t<t\)，故 \(f'(t)<0\)。所以最大值在 \(t=1\) 取得。

计算
\[
f(1)=\int_0^1dx\int_x^{\sqrt x}\frac{\sin y}{y}\,dy.
\]
区域等价于
\[
0\le y\le1,\qquad y^2\le x\le y.
\]
于是
\[
f(1)=\int_0^1(y-y^2)\frac{\sin y}{y}\,dy
=\int_0^1(1-y)\sin y\,dy
=\boxed{1-\sin1}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 求极限
\[
\lim_{n\to\infty}\frac1n\left(\int_{1/n}^1e^{-y^2}dy+\int_{2/n}^1e^{-y^2}dy+\cdots+\int_{(n-1)/n}^1e^{-y^2}dy\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是函数 \(F(x)=\int_x^1e^{-y^2}dy\) 的 Riemann 和。}
\[
\lim_{n\to\infty}\frac1n\sum_{k=1}^{n-1}\int_{k/n}^1e^{-y^2}dy
=\int_0^1dx\int_x^1e^{-y^2}dy.
\]
换序得
\[
\int_0^1e^{-y^2}\left(\int_0^y dx\right)dy
=\int_0^1y e^{-y^2}dy
=\boxed{\frac{1-e^{-1}}2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 求极限
\[
\lim_{t\to0^+}\frac1{t^6}\int_0^t dx\int_x^t\sin (xy)^2\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{令 \(x=tu,y=tv\)，则 \((xy)^2=t^4u^2v^2\)，面积元给出 \(t^2\)。}
\[
\begin{aligned}
\int_0^t dx\int_x^t\sin (xy)^2\,dy
&=t^2\int_0^1du\int_u^1\sin(t^4u^2v^2)\,dv\\
&\sim t^6\int_0^1du\int_u^1u^2v^2\,dv.
\end{aligned}
\]
所以极限为
\[
\int_0^1u^2\frac{1-u^3}{3}\,du
=\frac13\left(\frac13-\frac16\right)
=\boxed{\frac1{18}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 计算
\[
\int_{1/4}^{1/2}dy\int_{1/2}^{\sqrt y}e^{y/x}\,dx
+\int_{1/2}^{1}dy\int_y^{\sqrt y}e^{y/x}\,dx.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{原区域由 \(x=\frac12,\ y=x^2,\ y=x\) 围成。换序后 \(y/x\) 适合直接积分。}
换序得
\[
I=\int_{1/2}^1dx\int_{x^2}^{x}e^{y/x}\,dy.
\]
令 \(u=y/x\)，则 \(dy=x\,du\)，内层上下限为 \(u=x\) 到 \(u=1\)。故
\[
\begin{aligned}
I&=\int_{1/2}^1x\int_x^1e^u\,du\,dx\\
&=\int_{1/2}^1x(e-e^x)\,dx\\
&=\frac{3e}{8}-\frac{\sqrt e}{2}.
\end{aligned}
\]
故
\[
\boxed{\frac{3e}{8}-\frac{\sqrt e}{2}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 计算
\[
\iint_D|x^2+y^2-1|\,d\sigma,\qquad
D=\{(x,y):0\le x\le1,0\le y\le1\}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{单位正方形被第一象限单位圆弧分成两部分。}
在四分之一单位圆内，积分为 \(1-r^2\)；在其外，积分为 \(r^2-1\)。于是
\[
\begin{aligned}
I&=\int_0^{\pi/2}\int_0^1(1-r^2)r\,drd\theta
+\iint_{[0,1]^2}(x^2+y^2-1)\,d\sigma\\
&\quad-\int_0^{\pi/2}\int_0^1(r^2-1)r\,drd\theta\\
&=\frac{\pi}{8}+\left(\frac23-1\right)+\frac{\pi}{8}\\
&=\boxed{\frac{\pi}{4}-\frac13}.
\end{aligned}
\]
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 计算
\[
\iint_D\max\{xy,1\}\,dxdy,\qquad
D=\{(x,y):0\le x\le2,0\le y\le2\}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{按双曲线 \(xy=1\) 分区。}
当 \(0\le x\le\frac12\) 时，\(xy\le1\) 恒成立；当 \(\frac12\le x\le2\) 时，以 \(y=1/x\) 分割。因此
\[
\begin{aligned}
I&=\int_0^{1/2}2\,dx
+\int_{1/2}^2\left(\int_0^{1/x}1\,dy+\int_{1/x}^2xy\,dy\right)dx\\
&=1+\int_{1/2}^2\left(2x+\frac1{2x}\right)dx\\
&=\boxed{\frac{19}{4}+\ln2}.
\end{aligned}
\]
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 设
\[
D=\{(x,y):x^2+y^2\le2,\ x\ge0,\ y\ge0\},
\]
\([1+x^2+y^2]\) 表示不超过 \(1+x^2+y^2\) 的最大整数，计算
\[
\iint_Dxy[1+x^2+y^2]\,dxdy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{极坐标下取整项只依赖 \(r\)：\(0\le r<1\) 时为 \(1\)，\(1\le r<\sqrt2\) 时为 \(2\)。}
令 \(x=r\cos\theta,y=r\sin\theta\)，则
\[
0\le\theta\le\frac{\pi}{2},\quad 0\le r\le\sqrt2.
\]
所求积分为
\[
\int_0^{\pi/2}\cos\theta\sin\theta\,d\theta
\left(\int_0^1r^3\,dr+2\int_1^{\sqrt2}r^3\,dr\right).
\]
故
\[
I=\frac12\left(\frac14+\frac32\right)=\boxed{\frac78}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 计算
\[
\iint_D(x-y)\,dxdy,
\]
其中
\[
D=\{(x,y):(x-1)^2+(y-1)^2\le2,\ y\ge x\}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{绕圆心旋转坐标，使 \(y-x\) 成为一个坐标轴。}
令
\[
u=\frac{x+y}{\sqrt2},\qquad v=\frac{y-x}{\sqrt2}.
\]
则 \(x-y=-\sqrt2v\)，圆域变成
\[
(u-\sqrt2)^2+v^2\le2,
\]
且 \(y\ge x\) 即 \(v\ge0\)。因此
\[
I=-\sqrt2\iint_{\substack{(u-\sqrt2)^2+v^2\le2\\v\ge0}}v\,dudv.
\]
半径 \(R=\sqrt2\) 的上半圆对直径的一阶矩为 \(2R^3/3=4\sqrt2/3\)，故
\[
I=-\sqrt2\cdot\frac{4\sqrt2}{3}
=\boxed{-\frac83}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 计算
\[
I=\int_0^{\pi/4}\int_0^{\sec\theta}
r^2\sin\theta\sqrt{1-r^2\cos^2\theta}\,drd\theta.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{虽然题面用极坐标给出，但化回直角坐标后更简单。}
令 \(x=r\cos\theta,y=r\sin\theta\)。区域为
\[
0\le x\le1,\qquad 0\le y\le x.
\]
又
\[
r^2\sin\theta\,drd\theta
=y\,dxdy,
\qquad
\sqrt{1-r^2\cos^2\theta}=\sqrt{1-x^2}.
\]
故
\[
I=\int_0^1dx\int_0^xy\sqrt{1-x^2}\,dy
=\frac12\int_0^1x^2\sqrt{1-x^2}\,dx.
\]
令 \(x=\sin t\)，得
\[
I=\frac12\int_0^{\pi/2}\sin^2t\cos^2t\,dt
=\boxed{\frac{\pi}{32}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 计算
\[
\iint_D\frac{\sqrt{x^2+y^2}}{\sqrt{4a^2-x^2-y^2}}\,d\sigma,
\]
其中 \(D\) 是由曲线 \(y=-a+\sqrt{a^2-x^2}\ (a>0)\) 和直线 \(y=-x\) 围成的区域。
\end{problemblock}

\begin{solutionblock}
\analysis{曲线是圆 \(x^2+(y+a)^2=a^2\) 的上半部分，与直线 \(y=-x\) 围成第四象限内的小区域。}
极坐标下圆为
\[
r=-2a\sin\theta,
\]
区域为
\[
-\frac{\pi}{4}\le\theta\le0,\qquad 0\le r\le-2a\sin\theta.
\]
积分化为
\[
I=\int_{-\pi/4}^0d\theta\int_0^{-2a\sin\theta}
\frac{r^2}{\sqrt{4a^2-r^2}}\,dr.
\]
利用
\[
\int\frac{r^2}{\sqrt{R^2-r^2}}\,dr
=\frac{R^2}{2}\arcsin\frac rR-\frac r2\sqrt{R^2-r^2},
\]
取 \(R=2a\)，代入上限 \(r=-2a\sin\theta\)，得内层积分
\[
-2a^2\theta+2a^2\sin\theta\cos\theta.
\]
故
\[
I=a^2\left[-\theta^2+\sin^2\theta\right]_{-\pi/4}^0
=\boxed{a^2\left(\frac{\pi^2}{16}-\frac12\right)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{32.} 计算
\[
\iint_D(x+y)^3\,dxdy,
\]
其中 \(D\) 由曲线 \(x=\sqrt{1+y^2}\) 与直线 \(x+\sqrt2y=0,\ x-\sqrt2y=0\) 围成。
\end{problemblock}

\begin{solutionblock}
\analysis{区域关于 \(x\) 轴对称，展开 \((x+y)^3\) 后含奇次 \(y\) 的项积分为零。}
区域可写为
\[
-1\le y\le1,\qquad \sqrt2|y|\le x\le\sqrt{1+y^2}.
\]
展开
\[
(x+y)^3=x^3+3x^2y+3xy^2+y^3.
\]
含 \(y\) 奇次的两项积分为零，故
\[
I=\int_{-1}^1dy\int_{\sqrt2|y|}^{\sqrt{1+y^2}}(x^3+3xy^2)\,dx.
\]
利用偶对称，
\[
\begin{aligned}
I&=2\int_0^1\left[
\frac{x^4}{4}+\frac{3}{2}y^2x^2
\right]_{\sqrt2y}^{\sqrt{1+y^2}}dy\\
&=2\int_0^1\left(\frac14+2y^2-\frac94y^4\right)dy\\
&=\boxed{\frac{14}{15}}.
\end{aligned}
\]
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 计算
\[
\iint_D(x+y^2)\,dxdy,
\]
其中
\[
D=\{(x,y):x^2+y^2\le2x+2y\}.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{区域是以 \((1,1)\) 为圆心、半径 \(\sqrt2\) 的圆盘。}
令 \(u=x-1,v=y-1\)，则区域为 \(u^2+v^2\le2\)。有
\[
\iint_Dx\,d\sigma=1\cdot \pi(\sqrt2)^2=2\pi.
\]
又
\[
y^2=(v+1)^2=v^2+2v+1,
\]
其中 \(\iint 2v\,d\sigma=0\)，
\[
\iint_{u^2+v^2\le2}v^2\,dudv=\frac{\pi R^4}{4}=\pi.
\]
故
\[
\iint_Dy^2\,d\sigma=\pi+2\pi=3\pi.
\]
所以
\[
\boxed{5\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 求
\[
\iint_D(\sqrt{x^2+y^2}+y)\,d\sigma,
\]
其中 \(D\) 是由圆 \(x^2+y^2=4\) 和 \((x+1)^2+y^2=1\) 所围成的阴影区域。
\end{problemblock}

\begin{solutionblock}
\analysis{由图可知 \(D\) 为大圆盘去掉左侧小圆盘。区域关于 \(x\) 轴对称，\(y\) 项积分为零。}
故只需计算
\[
\iint_D\sqrt{x^2+y^2}\,d\sigma.
\]
大圆盘贡献为
\[
\int_0^{2\pi}d\theta\int_0^2r^2\,dr=\frac{16\pi}{3}.
\]
小圆 \((x+1)^2+y^2\le1\) 在极坐标中为
\[
\frac{\pi}{2}\le\theta\le\frac{3\pi}{2},\qquad 0\le r\le-2\cos\theta.
\]
其贡献为
\[
\int_{\pi/2}^{3\pi/2}d\theta\int_0^{-2\cos\theta}r^2\,dr
=\frac{32}{9}.
\]
因此
\[
\boxed{\frac{16\pi}{3}-\frac{32}{9}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 计算
\[
\int_{\pi/4}^{3\pi/4}d\theta\int_0^{2\sin\theta}
\left(\sin\theta+\cos\theta\sqrt{1+r^2\sin^2\theta}\right)r^2\,dr.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{积分区域关于 \(y\) 轴对称，含 \(\cos\theta\) 的部分化为关于 \(x\) 的奇函数，积分为零。}
令 \(x=r\cos\theta,y=r\sin\theta\)。区域关于 \(y\) 轴对称。第二项
\[
r^2\cos\theta\sqrt{1+r^2\sin^2\theta}\,drd\theta
=x\sqrt{1+y^2}\,dxdy
\]
关于 \(x\) 为奇函数，积分为零。

因此只需算
\[
\int_{\pi/4}^{3\pi/4}\int_0^{2\sin\theta}r^2\sin\theta\,drd\theta
=\frac83\int_{\pi/4}^{3\pi/4}\sin^4\theta\,d\theta.
\]
又
\[
\int_{\pi/4}^{3\pi/4}\sin^4\theta\,d\theta=\frac{3\pi}{16}+\frac12,
\]
故
\[
\boxed{\frac{\pi}{2}+\frac43}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 计算
\[
\int_{-1}^{1}dx\int_{|x|}^{1+\sqrt{1-x^2}}
(x^3+1)\sqrt{x^2+y^2}\,dy.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{区域关于 \(y\) 轴对称，\(x^3\sqrt{x^2+y^2}\) 关于 \(x\) 为奇函数，积分为零。}
剩下
\[
\iint_D\sqrt{x^2+y^2}\,d\sigma.
\]
极坐标下区域为
\[
\frac{\pi}{4}\le\theta\le\frac{3\pi}{4},\qquad 0\le r\le2\sin\theta.
\]
故
\[
I=\int_{\pi/4}^{3\pi/4}d\theta\int_0^{2\sin\theta}r^2\,dr
=\frac83\int_{\pi/4}^{3\pi/4}\sin^3\theta\,d\theta.
\]
计算
\[
\int_{\pi/4}^{3\pi/4}\sin^3\theta\,d\theta
=\int_{\pi/4}^{3\pi/4}\sin\theta(1-\cos^2\theta)\,d\theta
=\left[-\cos\theta+\frac{\cos^3\theta}{3}\right]_{\pi/4}^{3\pi/4}
=\frac{5\sqrt2}{6}.
\]
故
\[
\boxed{\frac{20\sqrt2}{9}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{38.} 设
\[
f(t)=\int_0^t dx\int_x^t y^2e^{-y^2}\,dy.
\]
证明对一切 \(t\in(-\infty,+\infty)\)，有
\[
0\le f(t)<\frac12.
\]
\end{problemblock}

\begin{solutionblock}
\analysis{把 \(f(t)\) 看成变上限函数求导，可得到一元函数表达式。}
由 Leibniz 公式，
\[
f'(t)=t\cdot t^2e^{-t^2}=t^3e^{-t^2},\qquad f(0)=0.
\]
因此
\[
f(t)=\int_0^t s^3e^{-s^2}\,ds
=\frac12\left[1-(t^2+1)e^{-t^2}\right].
\]
令 \(u=t^2\ge0\)。因为
\[
(u+1)e^{-u}\le1,
\]
且当 \(u>0\) 时严格小于 \(1\)，所以
\[
f(t)\ge0.
\]
又 \((u+1)e^{-u}>0\)，故
\[
f(t)<\frac12.
\]
命题得证。
\end{solutionblock}

\begin{problemblock}
\textbf{39.} 设 \(D=\{(x,y):0\le x\le2,0\le y\le2\}\)。
\begin{enumerate}
\item 计算 \(b=\iint_D|xy-1|\,d\sigma\)。
\item 设 \(f(x,y)\) 在 \(D\) 上连续，且
\[
\iint_Df(x,y)\,d\sigma=0,\qquad
\iint_Dxyf(x,y)\,d\sigma=1.
\]
证明存在 \((\xi,\eta)\in D\)，使
\[
|f(\xi,\eta)|\ge\frac1b.
\]
\end{enumerate}
\end{problemblock}

\begin{solutionblock}
\analysis{第一问按双曲线 \(xy=1\) 分割；第二问用积分绝对值估计和连续函数最大值。}
\begin{enumerate}
\item 当 \(0\le x\le\frac12\) 时，\(xy\le1\)；当 \(\frac12\le x\le2\) 时，以 \(y=1/x\) 分割。于是
\[
\begin{aligned}
b&=\int_0^{1/2}\int_0^2(1-xy)\,dy\,dx\\
&\quad+\int_{1/2}^2\left(\int_0^{1/x}(1-xy)\,dy+\int_{1/x}^{2}(xy-1)\,dy\right)dx\\
&=\frac34+\int_{1/2}^2\left(2x-2+\frac1x\right)dx\\
&=\boxed{\frac32+2\ln2}.
\end{aligned}
\]
\item 由条件
\[
1=\iint_Dxyf\,d\sigma-\iint_Df\,d\sigma
=\iint_D(xy-1)f(x,y)\,d\sigma.
\]
所以
\[
1\le \iint_D|xy-1|\,|f(x,y)|\,d\sigma
\le \max_D|f|\cdot \iint_D|xy-1|\,d\sigma
=b\max_D|f|.
\]
因此
\[
\max_D|f|\ge\frac1b.
\]
由于 \(f\) 连续，\(|f|\) 在闭区域 \(D\) 上能取到最大值，故存在 \((\xi,\eta)\in D\)，使
\[
|f(\xi,\eta)|\ge\frac1b.
\]
\end{enumerate}
\end{solutionblock}

\begin{problemblock}
\textbf{40.} 设 \(f(x),g(x)\) 在 \([0,1]\) 上连续，且同时单调增，证明
\[
\int_0^1f(x)g(x)\,dx\ge
\left(\int_0^1f(x)\,dx\right)
\left(\int_0^1g(x)\,dx\right).
\]
\end{problemblock}

\begin{solutionblock}
\analysis{这是积分形式的 Chebyshev 不等式。考研中常用“双重积分对称化”证明。}
因为 \(f,g\) 同时单调增，所以对任意 \(x,y\in[0,1]\)，有
\[
(f(x)-f(y))(g(x)-g(y))\ge0.
\]
对单位正方形积分，得
\[
\int_0^1\int_0^1(f(x)-f(y))(g(x)-g(y))\,dxdy\ge0.
\]
展开左边：
\[
\begin{aligned}
&\int_0^1\int_0^1(f(x)-f(y))(g(x)-g(y))\,dxdy\\
&=2\int_0^1f(x)g(x)\,dx
-2\left(\int_0^1f(x)\,dx\right)\left(\int_0^1g(x)\,dx\right).
\end{aligned}
\]
于是
\[
\int_0^1f(x)g(x)\,dx\ge
\left(\int_0^1f(x)\,dx\right)
\left(\int_0^1g(x)\,dx\right).
\]
证毕。
\examnote{若二者一个增一个减，则不等号方向相反。}
\end{solutionblock}

\section{本章小结}
第六章可见题号为 \(1\)--\(34\)、\(36\)--\(40\)，原书页面中未见第 \(35\) 题。本章核心方法是画区域、换序、对称性、极坐标与积分估计；其中第 \(13\)、\(14\) 题要特别注意区域分裂和有向积分。
"""


CH07_TEX = r"""\chapter{无穷级数}

\section{原题页索引}
本章原题对应做题本第 112--129 页。第 123 页后原题题号从 \(34\) 跳到 \(36\)，可见页面中未出现第 \(35\) 题。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_112.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 判断命题正误。
\end{problemblock}
\begin{solutionblock}
\analysis{本题考查级数基本性质，尤其是“发散”与“通项比较”不能随意互推。}
A 错，例如 \(\sum 1/(n\ln n)\) 发散，但 \(1/(n\ln n)<1/n\)。B 错，例如 \(a_{2n-1}=1,a_{2n}=-1\)，成对级数为 \(0\)，原级数不收敛。D 错，例如 \(a_n=1,b_n=1/n^2\)，\(\sum|a_nb_n|\) 收敛但 \(\sum a_n^2\) 发散。C 正确：若 \(\sum(|a_n|+|b_n|)\) 收敛，则 \(\sum|a_n|\)、\(\sum|b_n|\) 都收敛，从而两个原级数都绝对收敛，与“至少一个发散”矛盾。
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 判断四个命题中正确的个数。
\end{problemblock}
\begin{solutionblock}
\analysis{注意极限比较和夹逼判别都需要相应的正项或非负项结构。}
(1) 正确。若 \(\sum a_n\) 收敛，则其部分和有界，而 \((-1)^n/n\) 单调趋零，由 Dirichlet 判别法，\(\sum (-1)^n a_n/n\) 收敛。(2) 错，\(a_n=1/n\) 满足 \(a_{n+1}/a_n<1\)，但级数发散。(3) 错，缺少正项条件时极限比较不能直接用。(4) 正确。由 \(0\le b_n-a_n\le c_n-a_n\)，且 \(\sum(c_n-a_n)\) 收敛，得 \(\sum(b_n-a_n)\) 收敛，故 \(\sum b_n\) 收敛。
\answer{2 个，选 C}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} \(f(x)\) 在 \([0,1]\) 上连续，
\[
a_n=\sqrt n\int_{1/(n+1)}^{1/n}f(x)\,dx.
\]
判断 \(\sum a_n\) 的敛散性。
\end{problemblock}
\begin{solutionblock}
\analysis{连续函数有界，小区间长度约为 \(1/n^2\)。}
设 \(|f(x)|\le M\)，则
\[
|a_n|\le M\sqrt n\left(\frac1n-\frac1{n+1}\right)
=O\left(\frac1{n^{3/2}}\right).
\]
故 \(\sum|a_n|\) 收敛。
\answer{绝对收敛，选 B}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 设 \(p>0\)，讨论
\[
\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}{\ln(en+p)}.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{分母趋于无穷，通项正部 \(1/\ln(en+p)\) 单调趋零，但绝对值级数比调和级数更慢。}
由交错级数判别法，原级数收敛。绝对级数
\[
\sum\frac1{\ln(en+p)}
\]
发散，因为其通项不小于常数倍 \(1/n\) 对充分大 \(n\) 成立。
\answer{条件收敛，选 B}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} 判断比较判别相关命题。
\end{problemblock}
\begin{solutionblock}
\analysis{若没有正项条件，很多“极限比较”说法都不成立。}
A、B 都是错误的比较方向；C 错，例如 \(a_n=b_n=1/n\)，则 \(a_nb_n\to0\)，但两个级数都发散。D 正确：若 \(\sum a_n,\sum b_n\) 都收敛，则 \(a_n\to0,b_n\to0\)，于是 \(a_nb_n\to0\)，与 \(\lim a_nb_n=1\) 矛盾。
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 已知 \(\sum a_n\) 收敛，判断哪个结论不正确。
\end{problemblock}
\begin{solutionblock}
\analysis{线性组合和平方差望远镜通常保收敛，但隔项差不一定。}
A、B 都是对原收敛级数的有限错位与分组，收敛。D 为
\[
\sum(a_n^2-a_{n+1}^2),
\]
部分和等于 \(a_1^2-a_{N+1}^2\)，而 \(a_n\to0\)，故收敛。C 不一定，例如 \(a_n=(-1)^n/\sqrt n\) 时 \(\sum a_n\) 收敛，但
\[
a_{2n}-a_{2n+1}\sim \frac1{\sqrt{2n}}+\frac1{\sqrt{2n+1}},
\]
对应级数发散。
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} \(a_n>0,\sum a_n\) 收敛，\(\lambda\in(0,\pi/2)\)，讨论
\[
\sum_{n=1}^{\infty}(-1)^n\left(n\tan\frac{\lambda}{n}\right)a_{2n}.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{\(n\tan(\lambda/n)\to\lambda\)，而正项收敛级数的子级数也收敛。}
有
\[
n\tan\frac{\lambda}{n}\to\lambda,
\]
故绝对值级数与 \(\sum a_{2n}\) 同敛散。因为 \(\sum a_n\) 收敛且 \(a_n>0\)，\(\sum a_{2n}\) 收敛，所以原级数绝对收敛。
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 设 \(\sum u_n\) 收敛，判断必收敛的级数。
\end{problemblock}
\begin{solutionblock}
\analysis{严格地说，按题面 A 与 D 都必收敛；若原题作单选，则题面不唯一。}
D 中
\[
\sum_{n=1}^N(u_n+u_{n+1})=S_N+S_{N+1}-u_1\to2S-u_1,
\]
必收敛。A 也必收敛：\(\sum u_n\) 的部分和有界，而 \((-1)^n/n\) 趋零且总变差有限，由 Abel 变换可得 \(\sum(-1)^nu_n/n\) 收敛。B 可取 \(u_n=(-1)^n/\sqrt n\) 反例；C 同样由交错调和型反例可否定。
\answer{A、D 均必收敛；若按常规单选，D 是最直接选项。}
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 若 \(\sum a_n\) 收敛，判断必收敛的级数。
\end{problemblock}
\begin{solutionblock}
\analysis{错位平均保持收敛；乘以 \((-1)^n\) 或相邻项相乘不一定。}
D 中
\[
\sum_{n=1}^N\frac{a_n+a_{n+1}}2
=\frac12(S_N+S_{N+1}-a_1)\to S-\frac{a_1}{2}.
\]
A 不一定绝对收敛；B 取 \(a_n=(-1)^n/n\)，变为调和型发散；C 取 \(a_n=(-1)^n/\sqrt n\)，则 \(a_na_{n+1}\sim-1/n\) 发散。
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 若 \(a_n\to0\)，判断与 \(\sum b_n\) 有关的命题。
\end{problemblock}
\begin{solutionblock}
\analysis{只有绝对收敛与有界因子相乘最稳。}
由 \(a_n\to0\) 知 \(\{a_n\}\) 有界。若 \(\sum|b_n|\) 收敛，则 \(\sum b_n^2\) 收敛，从而
\[
\sum a_n^2b_n^2
\]
收敛。A、B、D 均可由条件收敛或发散级数构造反例。
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{11.} \(a_n>0\)，\(\sum a_n\) 发散而 \(\sum(-1)^{n-1}a_n\) 收敛，判断结论。
\end{problemblock}
\begin{solutionblock}
\analysis{交错级数收敛并不推出奇项或偶项正项级数分别收敛，但成对差就是原交错级数的分组。}
有
\[
\sum_{n=1}^{\infty}(a_{2n-1}-a_{2n})
=\sum_{n=1}^{\infty}(-1)^{n-1}a_n
\]
按相邻两项分组，故收敛。其他关于奇项、偶项正项级数的断言不一定成立。
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 设 \(\{u_n\}\) 为数列，判断命题正确项。
\end{problemblock}
\begin{solutionblock}
\analysis{收敛级数可以相邻分组，但反向由分组收敛推出原级数收敛是错误的。}
若 \(\sum u_n\) 收敛，则
\[
\sum_{n=1}^{\infty}(u_{2n-1}+u_{2n})
\]
是原级数按两项分组，必收敛。B 可取 \(u_{2n-1}=1,u_{2n}=-1\)；C 可取交错调和型反例；D 同样不成立。
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 已知
\[
\sum (-1)^n\sqrt n\sin\frac1{n^\alpha}
\]
绝对收敛，且
\[
\sum\frac{(-1)^n}{n^{2-\alpha}}
\]
条件收敛，求 \(\alpha\) 范围。
\end{problemblock}
\begin{solutionblock}
\analysis{分别化为 \(p\)-级数与交错 \(p\)-级数。}
\[
\sqrt n\sin\frac1{n^\alpha}\sim n^{1/2-\alpha}.
\]
绝对收敛要求
\[
1/2-\alpha<-1,\quad \alpha>\frac32.
\]
第二个级数条件收敛要求
\[
0<2-\alpha\le1,
\]
即 \(1\le\alpha<2\)。交集为
\[
\boxed{\frac32<\alpha<2}.
\]
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 设 \(a_n\) 为正项数列，判断正确选项。
\end{problemblock}
\begin{solutionblock}
\analysis{交错级数判别需要 \(a_n\to0\)，而不仅是递减。}
A 缺少 \(a_n\to0\)，错。B 错，交错级数收敛不必严格递减。C 错，如 \(a_n=1/(n\ln^2 n)\) 收敛，但不存在合适 \(p>1\) 使 \(n^pa_n\) 有有限极限。D 正确：若存在 \(p>1\)，使 \(\lim n^pa_n\) 为有限值，则 \(a_n=O(1/n^p)\)，故 \(\sum a_n\) 收敛。
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 若幂级数 \(\sum_{n=0}^{\infty}a_n(x+1)^n\) 在 \(x=1\) 处收敛，判断 \(\sum a_n\)。
\end{problemblock}
\begin{solutionblock}
\analysis{\(x=1\) 对应中心变量 \(t=x+1=2\)，而 \(\sum a_n\) 对应 \(t=1\)，属于收敛圆内部。}
幂级数在 \(t=2\) 处收敛，故收敛半径 \(R\ge2\)。当 \(t=1\) 时在收敛圆内部，所以绝对收敛。
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{16.} \(\sum (x-a)^n/n\) 在 \(x=-2\) 处条件收敛，判断 \(\sum n^2(x-a)^n\) 在 \(x=\ln(1/2)\) 处的敛散性。
\end{problemblock}
\begin{solutionblock}
\analysis{\(\sum t^n/n\) 在 \(t=-1\) 条件收敛。}
由 \(-2-a=-1\)，得 \(a=-1\)。当 \(x=\ln(1/2)=-\ln2\) 时，
\[
x-a=1-\ln2,
\]
其绝对值小于 \(1\)。级数 \(\sum n^2t^n\) 在 \(|t|<1\) 内绝对收敛。
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{17.} \(a_n\) 单调减且 \(a_n\to0\)，\(S_n=\sum_{k=1}^n a_k\) 无界，求
\[
\sum_{n=1}^{\infty}a_n(x-1)^n
\]
的收敛域。
\end{problemblock}
\begin{solutionblock}
\analysis{半径为 \(1\)。右端点是正项级数发散，左端点是交错级数收敛。}
当 \(|x-1|<1\) 时收敛，即 \(0<x<2\)。当 \(x=2\) 时为 \(\sum a_n\)，由 \(S_n\) 无界知发散；当 \(x=0\) 时为 \(\sum a_n(-1)^n\)，由 Leibniz 判别法收敛。故收敛域为
\[
\boxed{[0,2)}.
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{18.} \(a_n>0,p>1\)，且
\[
\lim_{n\to\infty}n^p(e^{1/n}-1)a_n=1.
\]
若 \(\sum a_n\) 收敛，求 \(p\) 范围。
\end{problemblock}
\begin{solutionblock}
\analysis{\(e^{1/n}-1\sim1/n\)，所以 \(a_n\) 等价于 \(1/n^{p-1}\)。}
由题设
\[
a_n\sim \frac1{n^p(e^{1/n}-1)}\sim\frac1{n^{p-1}}.
\]
正项级数收敛要求
\[
p-1>1,
\]
即
\[
\boxed{p>2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{19.} 若 \(\sum a_nx^n\) 的收敛半径为 \(3\)，求
\[
\sum_{n=1}^{\infty}n a_n(x-1)^{n+1}
\]
的收敛区间。
\end{problemblock}
\begin{solutionblock}
\analysis{乘以 \(n\) 和多乘一个 \((x-1)\) 不改变收敛半径。}
中心变量为 \(t=x-1\)，半径仍为 \(3\)，故开区间为
\[
\boxed{(-2,4)}.
\]
仅由原半径不能确定端点。
\end{solutionblock}

\begin{problemblock}
\textbf{20.} \(\sum a_n(x+2)^n\) 在 \(x=0\) 收敛，在 \(x=-4\) 发散，求 \(\sum a_n(x-3)^n\) 的收敛域。
\end{problemblock}
\begin{solutionblock}
\analysis{旧级数中心为 \(-2\)，两个端点对应 \(t=\pm2\)。}
由 \(x=0\) 收敛、\(x=-4\) 发散可知半径为 \(2\)，且 \(t=2\) 收敛，\(t=-2\) 发散。新级数中心为 \(3\)，故
\[
|x-3|<2.
\]
右端点 \(x=5\) 对应 \(t=2\)，收敛；左端点 \(x=1\) 对应 \(t=-2\)，发散。收敛域为
\[
\boxed{(1,5]}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 正项数列 \(a_n\) 单调减，且 \(a_n\ln n\to1\)，求
\[
\sum_{n=1}^{\infty}\frac{(-1)^na_n}{n}(x+1)^n
\]
的收敛区间。
\end{problemblock}
\begin{solutionblock}
\analysis{系数约为 \(1/(n\ln n)\)，半径为 \(1\)。}
当 \(|x+1|<1\) 时收敛。右端点 \(x=0\) 为
\[
\sum\frac{(-1)^na_n}{n},
\]
交错收敛；左端点 \(x=-2\) 为
\[
\sum\frac{a_n}{n}\sim\sum\frac1{n\ln n},
\]
发散。故
\[
\boxed{(-2,0]}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 已知 \(\sum(-1)^na_n\) 条件收敛，求
\[
\sum_{n=1}^{\infty}\frac{(-1)^na_n}{n}(x+1)^n
\]
的收敛区间。
\end{problemblock}
\begin{solutionblock}
\analysis{题面未给 \(a_n\) 单调或 \(\sum a_n/n\) 的信息，左端点不能唯一确定。}
一般可确定的是：半径通常为 \(1\)，在 \(-2<x<0\) 内绝对收敛；右端点 \(x=0\) 为 \(\sum(-1)^na_n/n\)，在常规交错条件下收敛。左端点 \(x=-2\) 变为 \(\sum a_n/n\)，仅由 \(\sum(-1)^na_n\) 条件收敛不能判断。例如 \(a_n=1/\sqrt n\) 时 \(\sum a_n/n\) 收敛；\(a_n=1/\ln n\) 时 \(\sum a_n/n\) 发散。
\answer{可确定部分为 \((-2,0]\)，但 \(x=-2\) 端点题面条件不足。}
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 若 \(\sum a_nx^n\) 在 \(x=2\) 条件收敛，求
\[
\sum a_nx^{2n}
\]
的收敛域。
\end{problemblock}
\begin{solutionblock}
\analysis{令 \(u=x^2\)，新级数就是旧级数在 \(u\) 处的取值。}
旧级数半径为 \(2\)，且 \(u=2\) 时条件收敛。因此
\[
x^2<2
\]
时绝对收敛；当 \(x^2=2\) 时条件收敛。故收敛域为
\[
\boxed{[-\sqrt2,\sqrt2]}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 求幂级数
\[
\sum_{n=1}^{\infty}\frac{(-1)^nx^n}{n[(-3)^n+2^n]}
\]
的收敛域。
\end{problemblock}
\begin{solutionblock}
\analysis{主导项为 \((-3)^n\)，半径为 \(3\)，再判端点。}
当 \(|x|<3\) 时绝对收敛。当 \(x=3\) 时，通项约为 \(1/n\)，发散；当 \(x=-3\) 时，通项约为 \((-1)^n/n\)，条件收敛。因此
\[
\boxed{[-3,3)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 判定级数敛散性。
\end{problemblock}
\begin{solutionblock}
\analysis{分别使用根值、比较、交错级数判别。}
\begin{enumerate}
\item \(\sum 1/(a^n n^a)\)：当 \(a>1\) 收敛；当 \(a=1\) 为调和级数发散；当 \(0<a<1\) 通项不趋零，发散。
\item \(\displaystyle \sum\frac{\sqrt n}{\int_0^n\sqrt[4]{1+x^4}\,dx}\) 收敛，因为分母 \(\sim n^2/2\)，通项 \(\sim2/n^{3/2}\)。
\item \(\displaystyle \sum\frac{n^3(\sqrt2+(-1)^n)^n}{3^n}\) 绝对收敛，偶、奇子列的指数比均小于 \(1\)。
\item \(\displaystyle \sum(-1)^n\frac{n-1}{n+1}\frac1{\sqrt n}\) 条件收敛；绝对值与 \(\sum1/\sqrt n\) 同阶发散。
\end{enumerate}
\end{solutionblock}

\begin{problemblock}
\textbf{26.} \(y'=x+y,\ y(0)=1\)，讨论
\[
\sum_{n=1}^{\infty}\left[y\left(\frac1n\right)-1-\frac1n\right]
\]
的敛散性。
\end{problemblock}
\begin{solutionblock}
\analysis{先解微分方程，再看通项等价。}
解得
\[
y=2e^x-x-1.
\]
因此
\[
y\left(\frac1n\right)-1-\frac1n
=2e^{1/n}-2-\frac2n
=2\left(e^{1/n}-1-\frac1n\right)
\sim\frac1{n^2}.
\]
故级数收敛。
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 将
\[
f(x)=\frac{x}{x^2+7x+6}
\]
在 \(x=4\) 处展开为幂级数。
\end{problemblock}
\begin{solutionblock}
\analysis{先部分分式，再令 \(t=x-4\)。}
\[
\frac{x}{(x+1)(x+6)}=-\frac1{5(x+1)}+\frac6{5(x+6)}.
\]
令 \(t=x-4\)，则
\[
f(x)=-\frac1{25}\frac1{1+t/5}+\frac3{25}\frac1{1+t/10}.
\]
所以
\[
\boxed{
f(x)=\sum_{n=0}^{\infty}(-1)^n\left(-\frac1{25\cdot5^n}+\frac3{25\cdot10^n}\right)(x-4)^n},
\quad |x-4|<5.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 将
\[
\ln\frac1{2+2x+x^2}
\]
在 \(x=-1\) 处展开。
\end{problemblock}
\begin{solutionblock}
\analysis{令 \(t=x+1\)，分母化为 \(1+t^2\)。}
\[
\ln\frac1{2+2x+x^2}=-\ln(1+t^2).
\]
故
\[
\boxed{
\ln\frac1{2+2x+x^2}
=\sum_{n=1}^{\infty}\frac{(-1)^n}{n}(x+1)^{2n}},
\quad |x+1|<1.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 将
\[
\arctan\frac{4+x^2}{4-x^2}
\]
展开为 \(x\) 的幂级数。
\end{problemblock}
\begin{solutionblock}
\analysis{利用 \(\tan(\pi/4+u)=(1+\tan u)/(1-\tan u)\)。}
令 \(t=x^2/4\)，则
\[
\arctan\frac{1+t}{1-t}=\frac{\pi}{4}+\arctan t.
\]
因此
\[
\boxed{
\arctan\frac{4+x^2}{4-x^2}
=\frac{\pi}{4}+\sum_{n=0}^{\infty}\frac{(-1)^nx^{4n+2}}{(2n+1)4^{2n+1}}},
\quad |x|<2.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 求
\[
S(x)=x+2\sum_{n=1}^{\infty}\frac{(-1)^{n+1}}{4n^2-1}x^{2n+1}
\]
的收敛域及和函数。
\end{problemblock}
\begin{solutionblock}
\analysis{对幂级数求导可化为 \(\arctan x\)。}
半径为 \(1\)，端点因系数 \(O(1/n^2)\) 均绝对收敛，收敛域为 \([-1,1]\)。
\[
S'(x)=1+2\sum_{n=1}^{\infty}\frac{(-1)^{n+1}x^{2n}}{2n-1}
=1+2x\arctan x.
\]
又 \(S(0)=0\)，故
\[
S(x)=\int_0^x(1+2t\arctan t)\,dt
=\boxed{(1+x^2)\arctan x}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 求
\[
\sum_{n=0}^{\infty}\frac{x^{4n}}{(4n)!}
\]
的收敛域与和函数。
\end{problemblock}
\begin{solutionblock}
\analysis{这是 \(e^x\) 中只保留 \(4n\) 次幂的部分。}
收敛域为 \((-\infty,+\infty)\)。由根筛法，
\[
\sum_{n=0}^{\infty}\frac{x^{4n}}{(4n)!}
=\frac{e^x+e^{-x}+e^{ix}+e^{-ix}}4
=\boxed{\frac{\cosh x+\cos x}{2}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{32.} 求
\[
S(x)=\sum_{n=1}^{\infty}\frac{(-1)^{n-1}x^{2n+1}}{n(2n-1)}
\]
的收敛域及和函数。
\end{problemblock}
\begin{solutionblock}
\analysis{分解 \(1/[n(2n-1)]=-1/n+2/(2n-1)\)。}
半径为 \(1\)，两端点绝对收敛，故收敛域 \([-1,1]\)。有
\[
\begin{aligned}
S(x)
&=-x\sum_{n=1}^{\infty}\frac{(-1)^{n-1}x^{2n}}n
+2x^3\sum_{m=0}^{\infty}\frac{(-1)^mx^{2m}}{2m+1}\\
&=\boxed{2x^2\arctan x-x\ln(1+x^2)}.
\end{aligned}
\]
\end{solutionblock}

\begin{problemblock}
\textbf{33.} 求
\[
\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}{(2n-1)(2n+1)}
\]
的和。
\end{problemblock}
\begin{solutionblock}
\analysis{拆成两个 Leibniz 反正切级数。}
\[
\frac1{(2n-1)(2n+1)}=\frac12\left(\frac1{2n-1}-\frac1{2n+1}\right).
\]
且
\[
\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}{2n-1}=\frac{\pi}{4}.
\]
故原和为
\[
\boxed{\frac{\pi}{4}-\frac12}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{34.} 将
\[
f(x)=
\begin{cases}
\dfrac{1+x^2}{x}\arctan x,&x\ne0,\\
1,&x=0
\end{cases}
\]
展开，并求
\[
\sum_{n=1}^{\infty}\frac{(-1)^n}{1-4n^2}.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{由 \(\arctan x/x\) 的展开乘以 \(1+x^2\)。}
\[
\frac{\arctan x}{x}=\sum_{n=0}^{\infty}\frac{(-1)^nx^{2n}}{2n+1}.
\]
整理得
\[
f(x)=1+\sum_{n=1}^{\infty}\frac{2(-1)^{n-1}}{4n^2-1}x^{2n},\quad |x|\le1.
\]
取 \(x=1\)，
\[
f(1)=2\arctan1=\frac{\pi}{2}
=1+2\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}{4n^2-1}.
\]
而
\[
\frac{(-1)^n}{1-4n^2}=\frac{(-1)^{n-1}}{4n^2-1},
\]
故所求和为
\[
\boxed{\frac{\pi}{4}-\frac12}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 幂级数 \(\sum a_nx^n\) 在全实轴收敛，和函数满足
\[
y''-2xy'-4y=0,\quad y(0)=0,\quad y'(0)=1.
\]
证明递推式并求 \(y(x)\)。
\end{problemblock}
\begin{solutionblock}
\analysis{把 \(y=\sum a_nx^n\) 代入微分方程比较系数。}
比较 \(x^n\) 系数：
\[
(n+2)(n+1)a_{n+2}-(2n+4)a_n=0,
\]
即
\[
a_{n+2}=\frac{2}{n+1}a_n.
\]
初值给出 \(a_0=0,a_1=1\)，偶次系数全为 \(0\)。直接求解微分方程也可发现
\[
\boxed{y=xe^{x^2}},
\]
它满足方程和初值。
\end{solutionblock}

\begin{problemblock}
\textbf{37.} \(a_0=3,a_1=1,\ a_{n-2}-n(n-1)a_n=0\)，\(S(x)=\sum a_nx^n\)。证明 \(S''-S=0\)，并求 \(S(x)\)。
\end{problemblock}
\begin{solutionblock}
\analysis{递推式正好对应二阶导数的系数。}
由
\[
n(n-1)a_n=a_{n-2}
\]
得
\[
S''(x)=\sum_{n=0}^{\infty}(n+2)(n+1)a_{n+2}x^n
=\sum_{n=0}^{\infty}a_nx^n=S(x).
\]
又
\[
S(0)=3,\qquad S'(0)=1.
\]
解 \(S''-S=0\)，得
\[
S=C e^x+D e^{-x}.
\]
由 \(C+D=3,\ C-D=1\)，得
\[
\boxed{S(x)=2e^x+e^{-x}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{38.} \(a_0=1,a_1=\frac12\)，且 \(n a_n=(n-\frac12)a_{n-1}\)。证明 \(|x|<1\) 时幂级数收敛并求和函数。
\end{problemblock}
\begin{solutionblock}
\analysis{该递推正是 \((1-x)^{-1/2}\) 的二项式系数递推。}
设
\[
S(x)=\sum_{n=0}^{\infty}a_nx^n.
\]
由递推式知系数与
\[
(1-x)^{-1/2}=\sum_{n=0}^{\infty}\binom{-1/2}{n}(-x)^n
\]
完全相同，且半径为 \(1\)。故
\[
\boxed{S(x)=\frac1{\sqrt{1-x}}},\qquad |x|<1.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{39.} \(a_0=2,\ n a_n=a_{n-1}+n-1\)，求幂级数和函数。
\end{problemblock}
\begin{solutionblock}
\analysis{先猜出一个特解 \(a_n=1\)，再看偏差。}
令 \(b_n=a_n-1\)，则
\[
n b_n=b_{n-1},\qquad b_0=1.
\]
所以
\[
b_n=\frac1{n!},\qquad a_n=1+\frac1{n!}.
\]
因此
\[
S(x)=\sum_{n=0}^{\infty}x^n+\sum_{n=0}^{\infty}\frac{x^n}{n!}
=\boxed{\frac1{1-x}+e^x},\quad |x|<1.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{40.} \(f\) 在 \(0\) 附近有连续一阶导数，且
\[
\lim_{x\to0}\frac{f(x)}x=2.
\]
证明
\[
\sum_{n=1}^{\infty}(-1)^nf\left(\frac1n\right)
\]
条件收敛。
\end{problemblock}
\begin{solutionblock}
\analysis{由条件得 \(f(0)=0,f'(0)=2\)。连续导数保证 \(f'(x)>0\) 在足够小邻域内成立，从而 \(f(1/n)\) 终究正且递减。}
因为 \(f'(0)=2\)，存在 \(\delta>0\)，使 \(0<x<\delta\) 时 \(f'(x)>0\)。故 \(f(x)\) 在该邻域内递增，且
\[
f\left(\frac1n\right)\to0.
\]
于是对充分大 \(n\)，\(f(1/n)>0\) 且随 \(n\) 递减，交错级数判别法给出收敛。

又
\[
f\left(\frac1n\right)\sim\frac2n,
\]
故绝对值级数与调和级数同敛散，发散。因此原级数条件收敛。
\end{solutionblock}

\begin{problemblock}
\textbf{41.} \(f(x)=|x-\frac12|\)，
\[
b_n=2\int_0^1f(x)\sin n\pi x\,dx,\qquad
S(x)=\sum_{n=1}^{\infty}b_n\sin n\pi x.
\]
求 \(S(-9/4)\)。
\end{problemblock}
\begin{solutionblock}
\analysis{这是 \([0,1]\) 上的 Fourier 正弦级数，对应奇延拓并以 \(2\) 为周期。}
由周期性，
\[
S\left(-\frac94\right)=S\left(-\frac14\right).
\]
正弦级数为奇延拓，故
\[
S\left(-\frac14\right)=-S\left(\frac14\right).
\]
在 \(0<x<1\) 内，\(S(x)=f(x)\)，所以
\[
S\left(\frac14\right)=\left|\frac14-\frac12\right|=\frac14.
\]
故
\[
\boxed{-\frac14}.
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 设
\[
x^2=\sum_{n=0}^{\infty}a_n\cos nx,\qquad -\pi\le x\le\pi.
\]
求 \(a_2\)。
\end{problemblock}
\begin{solutionblock}
\analysis{这是偶函数 Fourier 余弦系数。}
当 \(n\ge1\) 时
\[
a_n=\frac1\pi\int_{-\pi}^{\pi}x^2\cos nx\,dx
=\frac{4(-1)^n}{n^2}.
\]
故
\[
\boxed{a_2=1}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{43.} \(f\) 在 \([0,+\infty)\) 连续，且 \(\int_0^{+\infty}f^2(x)\,dx\) 收敛。令
\[
a_n=\int_0^1f(nx)\,dx.
\]
证明 \(\sum a_n^2/n^\alpha\ (\alpha>0)\) 收敛。
\end{problemblock}
\begin{solutionblock}
\analysis{换元后用 Cauchy 不等式估计 \(a_n\)。}
有
\[
a_n=\frac1n\int_0^n f(u)\,du.
\]
由 Cauchy 不等式，
\[
a_n^2\le\frac1{n^2}\cdot n\int_0^n f^2(u)\,du
\le\frac{C}{n},
\]
其中 \(C=\int_0^{+\infty}f^2(u)\,du\)。故
\[
\frac{a_n^2}{n^\alpha}\le \frac{C}{n^{1+\alpha}},
\]
而 \(\alpha>0\)，右侧级数收敛，命题得证。
\end{solutionblock}

\begin{problemblock}
\textbf{44.} \(a_n>0,b_n>0\)，且
\[
\frac{a_{n+1}}{a_n}\le\frac{b_{n+1}}{b_n}.
\]
证明相关比较结论。
\end{problemblock}
\begin{solutionblock}
\analysis{条件等价于 \(a_n/b_n\) 单调不增。}
由题设
\[
\frac{a_{n+1}}{b_{n+1}}\le\frac{a_n}{b_n},
\]
故
\[
\frac{a_n}{b_n}\le\frac{a_1}{b_1}.
\]
于是
\[
a_n\le\frac{a_1}{b_1}b_n.
\]
若 \(\sum b_n\) 收敛，则由比较判别法 \(\sum a_n\) 收敛。第二问是第一问的逆否命题：若 \(\sum a_n\) 发散而 \(\sum b_n\) 收敛，则推出 \(\sum a_n\) 收敛，矛盾；故 \(\sum b_n\) 必发散。
\end{solutionblock}

\begin{problemblock}
\textbf{45.} \(u_1=3,u_2=5,u_n=u_{n-1}+u_{n-2}\ (n\ge3)\)，证明
\[
\sum_{n=1}^{\infty}\frac1{u_n}
\]
收敛。
\end{problemblock}
\begin{solutionblock}
\analysis{递推数列至少每隔两项翻倍，倒数可按奇偶拆成几何级数比较。}
因为
\[
u_{n+2}=u_{n+1}+u_n\ge2u_n,
\]
所以
\[
\frac1{u_{n+2}}\le\frac12\frac1{u_n}.
\]
于是奇数项倒数子列和偶数项倒数子列都分别被公比 \(1/2\) 的几何级数控制，故原级数收敛。
\end{solutionblock}

\begin{problemblock}
\textbf{46.} 将 \(f(x)=x-1\ (0\le x\le2)\) 展开成周期为 \(4\) 的余弦级数。
\end{problemblock}
\begin{solutionblock}
\analysis{半区间余弦展开，\(L=2\)。}
\[
f(x)\sim \frac{a_0}{2}+\sum_{n=1}^{\infty}a_n\cos\frac{n\pi x}{2},
\]
其中
\[
a_0=\int_0^2(x-1)\,dx=0,
\]
\[
a_n=\int_0^2(x-1)\cos\frac{n\pi x}{2}\,dx
=\frac{4[(-1)^n-1]}{n^2\pi^2}.
\]
故
\[
\boxed{
x-1\sim -\frac8{\pi^2}\sum_{\substack{n\ge1\\ n\ \mathrm{odd}}}
\frac{\cos(n\pi x/2)}{n^2}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{47.} 将 \(f(x)=1-x^2\ (0\le x\le\pi)\) 展开成余弦级数，并求 \(\sum(-1)^{n-1}/n^2\)。
\end{problemblock}
\begin{solutionblock}
\analysis{半区间余弦展开，取 \(x=0\) 可得交错平方倒数和。}
\[
a_0=\frac2\pi\int_0^\pi(1-x^2)\,dx=2\left(1-\frac{\pi^2}{3}\right),
\]
\[
a_n=\frac2\pi\int_0^\pi(1-x^2)\cos nx\,dx
=-\frac{4(-1)^n}{n^2}.
\]
故
\[
1-x^2\sim 1-\frac{\pi^2}{3}-4\sum_{n=1}^{\infty}\frac{(-1)^n}{n^2}\cos nx.
\]
令 \(x=0\)，得
\[
1=1-\frac{\pi^2}{3}-4\sum_{n=1}^{\infty}\frac{(-1)^n}{n^2},
\]
因此
\[
\boxed{\sum_{n=1}^{\infty}\frac{(-1)^{n-1}}{n^2}=\frac{\pi^2}{12}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{48.} 将 \(f(x)=2+|x|\ (-1\le x\le1)\) 展开成以 \(2\) 为周期的 Fourier 级数，并求 \(\sum1/n^2\)。
\end{problemblock}
\begin{solutionblock}
\analysis{函数为偶函数，只含余弦项。}
取 \(L=1\)。有
\[
\frac{a_0}{2}=\frac12\int_{-1}^{1}(2+|x|)\,dx=\frac52,
\]
\[
a_n=\int_{-1}^{1}(2+|x|)\cos n\pi x\,dx
=2\int_0^1(2+x)\cos n\pi x\,dx
=\frac{2[(-1)^n-1]}{n^2\pi^2}.
\]
故
\[
2+|x|\sim \frac52+\sum_{n=1}^{\infty}
\frac{2[(-1)^n-1]}{n^2\pi^2}\cos n\pi x.
\]
取 \(x=0\)，得奇数项平方倒数和
\[
\sum_{\substack{n\ge1\\ n\ \mathrm{odd}}}\frac1{n^2}=\frac{\pi^2}{8}.
\]
又偶数项和为 \(\frac14\sum1/n^2\)，故
\[
\sum_{n=1}^{\infty}\frac1{n^2}
=\frac{\pi^2}{8}+\frac14\sum_{n=1}^{\infty}\frac1{n^2},
\]
解得
\[
\boxed{\sum_{n=1}^{\infty}\frac1{n^2}=\frac{\pi^2}{6}}.
\]
\end{solutionblock}

\section{本章小结}
第七章可见题号为 \(1\)--\(34\)、\(36\)--\(48\)，原书页面中未见第 \(35\) 题。第 \(8\) 题按严格数学判断有两个必收敛选项；第 \(22\) 题左端点需要额外条件才能唯一确定，解析中已单独标注。
"""


CH08_TEX = r"""\chapter{向量代数与空间解析几何及多元微分学在几何上的应用}

\section{原题页索引}
本章原题对应做题本第 130--140 页。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_130.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 求直线
\[
L_1:\frac{x-1}{1}=\frac{y-5}{-2}=\frac{z+8}{1},\qquad
L_2:\begin{cases}x-y=6,\\2y+z=3\end{cases}
\]
的夹角。
\end{problemblock}
\begin{solutionblock}
\analysis{直线夹角由方向向量夹角确定。}
\[
\boldsymbol d_1=(1,-2,1).
\]
\(L_2\) 是两平面交线，方向向量为两法向量叉乘：
\[
\boldsymbol d_2=(1,-1,0)\times(0,2,1)=(-1,-1,2).
\]
于是
\[
\cos\theta=\frac{|\boldsymbol d_1\cdot\boldsymbol d_2|}{|\boldsymbol d_1||\boldsymbol d_2|}
=\frac3{6}=\frac12.
\]
故夹角
\[
\boxed{\theta=\frac{\pi}{3}}.
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 判断直线
\[
L:\begin{cases}x+3y+2z+1=0,\\2x-y-10z+3=0\end{cases}
\]
与平面 \(\Pi:4x-2y+z-2=0\) 的关系。
\end{problemblock}
\begin{solutionblock}
\analysis{交线方向向量为两平面法向量叉乘，再与 \(\Pi\) 的法向量比较。}
\[
(1,3,2)\times(2,-1,-10)=(-28,14,-7)=-7(4,-2,1).
\]
这正与 \(\Pi\) 的法向量 \((4,-2,1)\) 平行，所以直线 \(L\) 垂直于 \(\Pi\)。
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} 曲面 \(z=4-x^2-y^2\) 上点 \(P\) 的切平面平行于 \(2x+2y+z-1=0\)，求 \(P\)。
\end{problemblock}
\begin{solutionblock}
\analysis{曲面写成 \(F=x^2+y^2+z-4=0\)，切平面法向量为 \((2x,2y,1)\)。}
平行条件给
\[
(2x,2y,1)\parallel(2,2,1),
\]
故
\[
x=1,\quad y=1,\quad z=4-1-1=2.
\]
\[
\boxed{P=(1,1,2)}.
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 曲线 \(x=t,y=-t^2,z=t^3\) 的切线中，与平面 \(x+2y+z=4\) 平行的有几条？
\end{problemblock}
\begin{solutionblock}
\analysis{切线平行平面等价于切向量垂直平面法向量。}
切向量为
\[
\boldsymbol r'(t)=(1,-2t,3t^2).
\]
平面法向量为 \((1,2,1)\)，故
\[
\boldsymbol r'(t)\cdot(1,2,1)=1-4t+3t^2=0.
\]
解得
\[
t=1,\quad t=\frac13.
\]
故共有两条。
\answer{B}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} \(f_x(0,0)=3,f_y(0,0)=1\)，判断相关结论。
\end{problemblock}
\begin{solutionblock}
\analysis{题面只给偏导数存在，没有明确给出可微；因此不能直接断言全微分或曲面切平面一定存在。沿 \(y=0\) 的截线切向量则可由 \(f_x\) 给出。}
曲线
\[
y=0,\qquad z=f(x,y)
\]
可参数化为
\[
\boldsymbol r(x)=(x,0,f(x,0)).
\]
在 \(x=0\) 处切向量为
\[
\boldsymbol r'(0)=(1,0,f_x(0,0))=(1,0,3).
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{6.} 求 \(f(x,y)=\arctan(x/y)\) 在 \((0,1)\) 处的梯度。
\end{problemblock}
\begin{solutionblock}
\[
f_x=\frac{y}{x^2+y^2},\qquad f_y=-\frac{x}{x^2+y^2}.
\]
故
\[
\nabla f(0,1)=(1,0)=\boldsymbol i.
\]
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 求曲面
\[
x^2+\cos(xy)+yz+x=0
\]
在 \((0,1,-1)\) 处的切平面。
\end{problemblock}
\begin{solutionblock}
\analysis{隐式曲面切平面法向量为 \(\nabla F\)。}
令
\[
F=x^2+\cos(xy)+yz+x.
\]
则
\[
F_x=2x-y\sin(xy)+1,\quad F_y=-x\sin(xy)+z,\quad F_z=y.
\]
在 \((0,1,-1)\) 处
\[
\nabla F=(1,-1,1).
\]
切平面为
\[
x-(y-1)+(z+1)=0,
\]
即
\[
\boxed{x-y+z=-2}.
\]
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{8.} 已知 \((\boldsymbol a\times\boldsymbol b)\cdot\boldsymbol c=2\)，求
\[
[(\boldsymbol a+\boldsymbol b)\times(\boldsymbol b+\boldsymbol c)]\cdot(\boldsymbol c+\boldsymbol a).
\]
\end{problemblock}
\begin{solutionblock}
\analysis{用混合积的线性性和循环不变性。}
\[
(\boldsymbol a+\boldsymbol b)\times(\boldsymbol b+\boldsymbol c)
=\boldsymbol a\times\boldsymbol b+\boldsymbol a\times\boldsymbol c+\boldsymbol b\times\boldsymbol c.
\]
与 \(\boldsymbol c+\boldsymbol a\) 点乘后，仅
\[
(\boldsymbol a\times\boldsymbol b)\cdot\boldsymbol c,\qquad
(\boldsymbol b\times\boldsymbol c)\cdot\boldsymbol a
\]
非零，且二者相等，均为 \(2\)。故结果为
\[
\boxed{4}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 求点 \((2,1,0)\) 到平面 \(3x+4y+5z=0\) 的距离。
\end{problemblock}
\begin{solutionblock}
\[
d=\frac{|3\cdot2+4\cdot1+5\cdot0|}{\sqrt{3^2+4^2+5^2}}
=\frac{10}{5\sqrt2}
=\boxed{\sqrt2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{10.} 求与两直线
\[
x=1,\ y=-1+t,\ z=2+t;\qquad
\frac{x+1}{1}=\frac{y+2}{2}=\frac{z-1}{1}
\]
都平行且过原点的平面。
\end{problemblock}
\begin{solutionblock}
两方向向量为
\[
\boldsymbol d_1=(0,1,1),\qquad \boldsymbol d_2=(1,2,1).
\]
平面法向量
\[
\boldsymbol n=\boldsymbol d_1\times\boldsymbol d_2=(-1,1,-1).
\]
过原点，故
\[
\boxed{x-y+z=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{11.} 求过 \(M(1,2,-1)\) 且与直线
\[
x=-t+2,\quad y=3t-4,\quad z=t-1
\]
垂直的平面。
\end{problemblock}
\begin{solutionblock}
直线方向向量为
\[
(-1,3,1),
\]
它即为所求平面的法向量。故
\[
-(x-1)+3(y-2)+(z+1)=0,
\]
即
\[
\boxed{x-3y-z+4=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{12.} 求过
\[
L_1:\frac{x-1}{1}=\frac{y-2}{0}=\frac{z-3}{-1}
\]
且平行于
\[
L_2:\frac{x+2}{2}=\frac{y-1}{1}=\frac{z}{1}
\]
的平面。
\end{problemblock}
\begin{solutionblock}
两个方向向量为
\[
\boldsymbol d_1=(1,0,-1),\qquad \boldsymbol d_2=(2,1,1).
\]
平面法向量
\[
\boldsymbol n=\boldsymbol d_1\times\boldsymbol d_2=(1,-3,1).
\]
平面过 \(L_1\) 上点 \((1,2,3)\)，故
\[
(x-1)-3(y-2)+(z-3)=0,
\]
即
\[
\boxed{x-3y+z+2=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{13.} 平面过原点及点 \((6,-3,2)\)，且与 \(4x-y+2z=8\) 垂直，求方程。
\end{problemblock}
\begin{solutionblock}
所求平面含向量
\[
\boldsymbol p=(6,-3,2),
\]
其法向量还应垂直于已知平面法向量
\[
\boldsymbol n_0=(4,-1,2).
\]
故可取
\[
\boldsymbol n=\boldsymbol p\times\boldsymbol n_0=(-4,-4,6)\sim(-2,-2,3).
\]
过原点，方程为
\[
\boxed{-2x-2y+3z=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{14.} 曲线
\[
3x^2+2y^2=12,\quad z=0
\]
绕 \(y\) 轴旋转得到旋转面，求其在 \((0,\sqrt3,\sqrt2)\) 处指向外侧的单位法向量。
\end{problemblock}
\begin{solutionblock}
\analysis{绕 \(y\) 轴旋转时 \(x^2\) 变成 \(x^2+z^2\)。}
旋转面为
\[
F=3(x^2+z^2)+2y^2-12=0.
\]
法向量
\[
\nabla F=(6x,4y,6z).
\]
在点 \((0,\sqrt3,\sqrt2)\) 处
\[
\nabla F=(0,4\sqrt3,6\sqrt2).
\]
其模为 \(2\sqrt{30}\)，故外侧单位法向量为
\[
\boxed{\left(0,\frac{\sqrt{10}}5,\frac{\sqrt{15}}5\right)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{15.} 直线
\[
\frac{x-1}{0}=\frac{y-1}{1}=\frac{z-1}{1}
\]
绕 \(y\) 轴旋转，求旋转曲面方程。
\end{problemblock}
\begin{solutionblock}
直线可写为
\[
x=1,\qquad z=y.
\]
绕 \(y\) 轴旋转时保持 \(y\) 不变，且半径平方
\[
x^2+z^2=1+y^2.
\]
故旋转曲面为
\[
\boxed{x^2+z^2=1+y^2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{16.} 求 \(u=\ln(x^2+y^2+z^2)\) 在 \(M(1,2,-2)\) 处的梯度。
\end{problemblock}
\begin{solutionblock}
\[
\nabla u=\frac{2(x,y,z)}{x^2+y^2+z^2}.
\]
在 \(M\) 处分母为 \(9\)，所以
\[
\boxed{\nabla u|_M=\left(\frac29,\frac49,-\frac49\right)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{17.} 求 \(f=x^2y+z^2\) 在 \((1,2,0)\) 处沿 \(\boldsymbol n=(1,2,2)\) 的方向导数。
\end{problemblock}
\begin{solutionblock}
\[
\nabla f=(2xy,x^2,2z),
\qquad \nabla f(1,2,0)=(4,1,0).
\]
单位方向向量为
\[
\frac{(1,2,2)}3.
\]
方向导数为
\[
(4,1,0)\cdot\frac{(1,2,2)}3=\boxed{2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{18.} \(u=1+x^2/6+y^2/12+z^2/18\)，\(\boldsymbol n=(1,1,1)/\sqrt3\)，求 \(\partial u/\partial n\) 在 \((1,2,3)\) 处的值。
\end{problemblock}
\begin{solutionblock}
\[
\nabla u=\left(\frac x3,\frac y6,\frac z9\right),
\quad
\nabla u(1,2,3)=\left(\frac13,\frac13,\frac13\right).
\]
故
\[
\frac{\partial u}{\partial n}
=\left(\frac13,\frac13,\frac13\right)\cdot\frac{(1,1,1)}{\sqrt3}
=\boxed{\frac1{\sqrt3}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{19.} \(\nabla f=(1,2,3)\)，求沿 \(\boldsymbol l=(1,1,1)\) 方向的方向导数。
\end{problemblock}
\begin{solutionblock}
单位方向向量为 \((1,1,1)/\sqrt3\)，故
\[
D_{\boldsymbol l}f=(1,2,3)\cdot\frac{(1,1,1)}{\sqrt3}
=\boxed{2\sqrt3}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{20.} \(u=3x^2y-2yz+z^3,\ v=4xy-z^3\)，求 \(u\) 在 \(P(1,-1,1)\) 处沿 \(\nabla v\) 方向的方向导数。
\end{problemblock}
\begin{solutionblock}
\[
\nabla u=(6xy,3x^2-2z,-2y+3z^2),
\quad
\nabla u(P)=(-6,1,5).
\]
\[
\nabla v=(4y,4x,-3z^2),
\quad
\nabla v(P)=(-4,4,-3).
\]
方向导数为
\[
\nabla u(P)\cdot\frac{\nabla v(P)}{|\nabla v(P)|}
=\frac{24+4-15}{\sqrt{41}}
=\boxed{\frac{13}{\sqrt{41}}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 隐函数 \(u(x,y,z)\) 由
\[
x+y+z+u+xy^2z^3e^u=1
\]
确定。求其在 \((0,0,0)\) 处沿椭球面
\[
x^2+2y^2+3(z-1)^2=3
\]
在该点外法线方向的方向导数。
\end{problemblock}
\begin{solutionblock}
\analysis{先求该点对应的 \(u\)，再求隐函数梯度。}
当 \(x=y=z=0\) 时，由方程得
\[
u=1.
\]
设
\[
F=x+y+z+u+xy^2z^3e^u-1.
\]
在该点，乘积项各偏导均为 \(0\)，且 \(F_u=1\)，故
\[
u_x=u_y=u_z=-1.
\]
即
\[
\nabla u=(-1,-1,-1).
\]
椭球在 \((0,0,0)\) 处的外法线方向为
\[
(0,0,-1).
\]
方向导数为
\[
\boxed{1}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 求 \(u=x^2+y^2+z^2\) 在椭球面 \(2x^2+2y^2+z^2=1\) 上哪点沿哪方向方向导数最大，并求最大值。
\end{problemblock}
\begin{solutionblock}
\analysis{某点最大方向导数为 \(|\nabla u|\)，方向为梯度方向；再在椭球上最大化 \(u\)。}
\[
\nabla u=2(x,y,z),\qquad |\nabla u|=2\sqrt{x^2+y^2+z^2}.
\]
在约束
\[
2x^2+2y^2+z^2=1
\]
下，\(x^2+y^2+z^2\) 最大时取
\[
x=y=0,\quad z=\pm1.
\]
最大方向分别为
\[
(0,0,1)\quad\text{和}\quad(0,0,-1),
\]
最大方向导数为
\[
\boxed{2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{23.} 求曲线
\[
\begin{cases}
x^2+y^2+z^2=a^2,\\
x^2+y^2=ax
\end{cases}
\]
在 \(M_0(0,0,a)\) 处的切线及法平面。
\end{problemblock}
\begin{solutionblock}
两个曲面的法向量分别为
\[
\nabla F_1=(2x,2y,2z),\quad \nabla F_2=(2x-a,2y,0).
\]
在 \(M_0\) 处
\[
\nabla F_1=(0,0,2a),\quad \nabla F_2=(-a,0,0).
\]
切向量为二者叉乘，平行于 \(y\) 轴。因此切线为
\[
\boxed{x=0,\quad z=a},
\]
法平面垂直于切向量，故
\[
\boxed{y=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{24.} 求直线
\[
L:\frac{x-1}{1}=\frac{y}{1}=\frac{z-1}{-1}
\]
在平面 \(\Pi:x-y+2z-1=0\) 上的投影直线 \(L_0\)，并求 \(L_0\) 绕 \(y\) 轴旋转所得曲面。
\end{problemblock}
\begin{solutionblock}
\analysis{投影直线的方向为原方向在平面上的投影；点可取原直线上一点向平面作垂线投影。}
原直线方向
\[
\boldsymbol d=(1,1,-1),\quad \Pi\text{ 法向量 }\boldsymbol n=(1,-1,2).
\]
方向投影为
\[
\boldsymbol d_0=\boldsymbol d-\frac{\boldsymbol d\cdot\boldsymbol n}{|\boldsymbol n|^2}\boldsymbol n
=(1,1,-1)+\frac13(1,-1,2)\sim(4,2,-1).
\]
取 \(P=(1,0,1)\in L\)，其到平面的投影为
\[
P_0=P-\frac{2}{6}(1,-1,2)=\left(\frac23,\frac13,\frac13\right).
\]
故
\[
\boxed{\frac{x-2/3}{4}=\frac{y-1/3}{2}=\frac{z-1/3}{-1}}.
\]
令参数为 \(s\)，则
\[
x=2y,\qquad z=\frac{1-y}{2}.
\]
绕 \(y\) 轴旋转时 \(x^2+z^2\) 保持为半径平方，故曲面为
\[
\boxed{x^2+z^2=4y^2+\frac{(y-1)^2}{4}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{25.} 求椭球面 \(x^2+2y^2+3z^2=21\) 的切平面，使其过直线
\[
L:\frac{x-6}{2}=\frac{y-3}{1}=\frac{2z-1}{-2}.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{设切点为 \((x_0,y_0,z_0)\)，切平面为 \(x_0x+2y_0y+3z_0z=21\)，再代入直线参数。}
直线参数为
\[
x=6+2t,\quad y=3+t,\quad z=\frac12-t.
\]
代入切平面并令恒等于 \(21\)，得
\[
6x_0+6y_0+\frac32z_0=21,\qquad
2x_0+2y_0-3z_0=0.
\]
又切点在椭球上：
\[
x_0^2+2y_0^2+3z_0^2=21.
\]
由前两式得
\[
x_0+y_0=3,\quad z_0=2.
\]
代入椭球：
\[
x_0^2+2y_0^2=9.
\]
解得
\[
(x_0,y_0,z_0)=(3,0,2)\quad\text{或}\quad(1,2,2).
\]
对应切平面为
\[
\boxed{x+2z=7}
\]
或
\[
\boxed{x+4y+6z=21}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 求过直线
\[
\begin{cases}x+2y+z-1=0,\\x-y-2z+3=0\end{cases}
\]
且与曲线
\[
\begin{cases}x^2+y^2=\frac12z^2,\\x+y+2z=4\end{cases}
\]
在 \((1,-1,2)\) 处的切线平行的平面。
\end{problemblock}
\begin{solutionblock}
已知直线方向为
\[
(1,2,1)\times(1,-1,-2)\sim(1,-1,1).
\]
曲线在点处的切向量为两曲面法向量叉乘：
\[
(2,-2,-2)\times(1,1,2)\sim(1,3,-2).
\]
所求平面含这两个方向，法向量为
\[
(1,-1,1)\times(1,3,-2)=(-1,3,4).
\]
又平面过给定直线，可写成两已知平面的线性组合。最终得
\[
\boxed{-3x+9y+12z-17=0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 小山高度
\[
h(x,y)=75-x^2-y^2+xy,\quad D:x^2+y^2-xy\le75.
\]
\begin{enumerate}
\item 求在点 \(M(x_0,y_0)\) 处方向导数最大的方向及最大值 \(g(x_0,y_0)\)。
\item 在边界上求坡度最大的攀登起点。
\end{enumerate}
\end{problemblock}
\begin{solutionblock}
\analysis{平面上函数方向导数最大方向为梯度方向，最大值为梯度模。}
\[
\nabla h=(-2x+y,\ x-2y).
\]
因此在 \(M(x_0,y_0)\) 处最大方向为
\[
\boxed{\nabla h(x_0,y_0)}
\]
方向，最大值为
\[
\boxed{g(x_0,y_0)=\sqrt{(-2x_0+y_0)^2+(x_0-2y_0)^2}}.
\]
在边界
\[
x^2+y^2-xy=75
\]
上最大化
\[
g^2=5(x^2+y^2)-8xy.
\]
令
\[
s=x+y,\qquad d=x-y.
\]
则边界为
\[
s^2+3d^2=300,
\]
而
\[
g^2=\frac12s^2+\frac92d^2.
\]
显然当 \(s=0,d^2=100\) 时最大，即
\[
x+y=0,\qquad x-y=\pm10.
\]
故攀登起点为
\[
\boxed{(5,-5)\quad\text{或}\quad(-5,5)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 礼堂顶部为半椭球面
\[
z=4\sqrt{1-\frac{x^2}{16}-\frac{y^2}{36}},
\]
求下雨时过 \(P(1,3,\sqrt{11})\) 的雨水流下路线。
\end{problemblock}
\begin{solutionblock}
\analysis{不计摩擦时，雨水沿高度函数在 \(xOy\) 平面投影的负梯度方向流动。}
设
\[
z=z(x,y)=4\sqrt{1-\frac{x^2}{16}-\frac{y^2}{36}}.
\]
则
\[
z_x=-\frac{x}{4\sqrt Q},\qquad z_y=-\frac{2y}{9\sqrt Q},
\quad Q=1-\frac{x^2}{16}-\frac{y^2}{36}.
\]
负梯度方向满足
\[
\frac{dy}{dx}=\frac{-z_y}{-z_x}=\frac{8y}{9x}.
\]
解得
\[
\ln y=\frac89\ln x+C,
\]
过 \((1,3)\)，所以
\[
y=3x^{8/9}.
\]
因此雨水路线为空间曲线
\[
\boxed{
\begin{cases}
y=3x^{8/9},\\
z=4\sqrt{1-\dfrac{x^2}{16}-\dfrac{y^2}{36}}.
\end{cases}}
\]
\end{solutionblock}

\section{本章小结}
第八章共 \(28\) 题，重点是方向向量、法向量、切平面、方向导数和梯度的几何意义。遇到“方向导数最大”优先想到梯度方向。
"""


CH09_TEX = r"""\chapter{多元函数积分学及其应用}

\section{原题页索引}
本章原题对应做题本第 141--160 页。

\begin{center}
\includegraphics[width=.92\textwidth]{figures/original_pages/page_141.png}
\end{center}

\section{详细解析}

\begin{problemblock}
\textbf{1.} 已知
\[
\frac{(x+ay)\,dx+y\,dy}{(x+y)^2}
\]
为某函数的全微分，求 \(a\)。
\end{problemblock}
\begin{solutionblock}
\analysis{设 \(M=(x+ay)/(x+y)^2,\ N=y/(x+y)^2\)，全微分要求 \(M_y=N_x\)。}
\[
M_y=\frac{(a-2)x-ay}{(x+y)^3},\qquad
N_x=-\frac{2y}{(x+y)^3}.
\]
比较系数得 \(a-2=0,\ a=2\)。故
\[
\boxed{a=2}.
\]
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{2.} 比较上半球 \(\Omega_1\) 与第一卦限球体 \(\Omega_2\) 上的三重积分。
\end{problemblock}
\begin{solutionblock}
\analysis{上半球可按 \(x,y\) 符号分成四个全等部分。}
\(\iiint_{\Omega_1}x\,dv=\iiint_{\Omega_1}y\,dv=0\)，而 \(\iiint_{\Omega_2}x\,dv,\iiint_{\Omega_2}y\,dv>0\)，故 A、B 错。上半球关于 \(x,y\) 四象限对称，且 \(z\) 不变，所以
\[
\iiint_{\Omega_1}z\,dv=4\iiint_{\Omega_2}z\,dv.
\]
\answer{C}
\end{solutionblock}

\begin{problemblock}
\textbf{3.} \(S:x^2+y^2+z^2=a^2,\ x\ge0\)，\(S_1\) 为第一卦限部分，判断曲面积分关系。
\end{problemblock}
\begin{solutionblock}
\analysis{\(S\) 是半个球面，可由 \(y,z\) 符号分成四个全等部分。}
在四部分上 \(x\) 取值相同，故
\[
\iint_S x\,dS=4\iint_{S_1}x\,dS.
\]
而 \(y,z,xyz\) 在对称部分会抵消。
\answer{A}
\end{solutionblock}

\begin{problemblock}
\textbf{4.} 四条逆时针曲线 \(L_i\) 围成区域，比较
\[
I_i=\int_{L_i}\left(y+\frac{y^3}{6}\right)dx+\left(2x-\frac{x^3}{3}\right)dy.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{用 Green 公式化为区域积分。}
\[
Q_x-P_y=\left(2-x^2\right)-\left(1+\frac{y^2}{2}\right)
=1-x^2-\frac{y^2}{2}.
\]
分别计算四个区域：
\[
I_1=\frac{5\pi}{8},\quad I_2=\frac{\pi}{2},\quad
I_3=\frac{3\sqrt2\pi}{8},\quad I_4=\frac{\sqrt2\pi}{2}.
\]
最大为 \(I_4\)。
\answer{D}
\end{solutionblock}

\begin{problemblock}
\textbf{5.} \(u=\ln(x^2+y^2+z^2)\)，求 \(\operatorname{div}(\operatorname{grad}u)\)。
\end{problemblock}
\begin{solutionblock}
\[
\Delta\ln r^2=\frac{2}{r^2}\quad(r^2=x^2+y^2+z^2),
\]
故
\[
\boxed{\operatorname{div}(\operatorname{grad}u)=\frac{2}{x^2+y^2+z^2}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{6.} \(\boldsymbol A=(xy^2,yz^2,zx^2)\)，求
\[
\operatorname{grad}(\operatorname{div}\boldsymbol A)\big|_{(1,-1,2)}.
\]
\end{problemblock}
\begin{solutionblock}
\[
\operatorname{div}\boldsymbol A=y^2+z^2+x^2.
\]
故
\[
\operatorname{grad}(\operatorname{div}\boldsymbol A)=2(x,y,z),
\]
在 \((1,-1,2)\) 处为
\[
\boxed{(2,-2,4)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{7.} 给定 \(\boldsymbol A=(x^2y,y^2z,z^2x)\)，求
\[
\operatorname{rot}(\operatorname{grad}(\operatorname{div}\boldsymbol A)).
\]
\end{problemblock}
\begin{solutionblock}
\analysis{任意二阶连续数量场的梯度场旋度恒为零。}
\[
\boxed{\operatorname{rot}(\operatorname{grad}(\operatorname{div}\boldsymbol A))=\boldsymbol 0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{8.} \(\Omega:\frac{x^2}{a^2}+\frac{y^2}{b^2}+\frac{z^2}{c^2}\le1\)，求
\[
\iiint_{\Omega}(x+y+z)^2\,dv.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{区域关于三个坐标面对称，交叉项积分为零。}
椭球体积 \(V=4\pi abc/3\)，且
\[
\iiint_\Omega x^2\,dv=\frac{Va^2}{5},
\quad
\iiint_\Omega y^2\,dv=\frac{Vb^2}{5},
\quad
\iiint_\Omega z^2\,dv=\frac{Vc^2}{5}.
\]
故
\[
\boxed{\iiint_\Omega(x+y+z)^2\,dv
=\frac{4\pi abc}{15}(a^2+b^2+c^2)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{9.} 计算
\[
I=\int_0^{2\pi}d\theta\int_0^1dr\int_0^{1-r}e^{-(1-z)^2}\,dz.
\]
\end{problemblock}
\begin{solutionblock}
先对 \(r,z\) 区域换序：
\[
0\le z\le1,\qquad 0\le r\le1-z.
\]
所以
\[
I=2\pi\int_0^1(1-z)e^{-(1-z)^2}\,dz
=2\pi\int_0^1u e^{-u^2}\,du
=\boxed{\pi(1-e^{-1})}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{10.} \(C:\frac{x^2}{a^2}+\frac{y^2}{b^2}=1\)，周长为 \(L\)，求
\[
\int_C(bx+ay+1)^2\,ds.
\]
\end{problemblock}
\begin{solutionblock}
令 \(x=a\cos t,y=b\sin t\)，则
\[
bx+ay=ab(\cos t+\sin t).
\]
线性项沿中心对称闭曲线积分为零，且
\[
\int_C(\cos t+\sin t)^2\,ds=\int_C1\,ds=L
\]
中的 \(\sin2t\) 项对称抵消。故
\[
\boxed{\int_C(bx+ay+1)^2ds=(a^2b^2+1)L}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{11.} \(\Gamma:x^2+y^2+z^2=a^2,\ x+y+z=0\)，求
\[
\int_\Gamma\left[(x+2)^2+(y-3)^2\right]ds.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{\(\Gamma\) 是过原点平面截球所得圆，半径为 \(a\)。}
展开后一次项沿中心对称圆积分为零：
\[
(x+2)^2+(y-3)^2=x^2+y^2+4x-6y+13.
\]
在平面 \(x+y+z=0\) 内的圆上
\[
\int_\Gamma (x^2+y^2)\,ds=\frac{4\pi a^3}{3},
\quad
\int_\Gamma ds=2\pi a.
\]
故结果为
\[
\boxed{\frac{4\pi a^3}{3}+26\pi a}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{12.} \(L:y=1-|x|,\ -1\le x\le1\)，从 \((-1,0)\) 到 \((1,0)\)，求
\[
\int_L xy\,dx+x^2\,dy.
\]
\end{problemblock}
\begin{solutionblock}
用 \(x\) 轴线段闭合，闭合区域关于 \(y\) 轴对称。Green 公式中
\[
Q_x-P_y=2x-x=x.
\]
区域上 \(\iint x\,dA=0\)，且 \(x\) 轴线段积分为零，故
\[
\boxed{0}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{13.} \(L\) 为柱面 \(x^2+y^2=1\) 与平面 \(z=x+y\) 交线，方向从 \(z\) 轴正向看为逆时针，求
\[
\int_L xz\,dx+x\,dy+\frac{y^2}{2}\,dz.
\]
\end{problemblock}
\begin{solutionblock}
参数化：
\[
x=\cos t,\quad y=\sin t,\quad z=\cos t+\sin t,\quad 0\le t\le2\pi.
\]
代入后只有 \(\int_0^{2\pi}\cos^2t\,dt\) 留下，其余奇对称项为零。故
\[
\boxed{\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{14.} \(L:x^2+y^2=1\)，外法线为 \(\boldsymbol n\)，\(u=(x^4+y^4)/12\)，求
\[
\int_L\frac{\partial u}{\partial n}\,ds.
\]
\end{problemblock}
\begin{solutionblock}
由 Green 公式的法向形式，
\[
\int_L\frac{\partial u}{\partial n}ds
=\iint_D\Delta u\,dA.
\]
而
\[
\Delta u=x^2+y^2.
\]
故单位圆盘上积分为
\[
\int_0^{2\pi}\int_0^1r^2\cdot r\,drd\theta
=\boxed{\frac{\pi}{2}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{15.} \(\Sigma:x^2+y^2+z^2=R^2\)，求
\[
\iint_\Sigma (z+|x|)^2\,dS.
\]
\end{problemblock}
\begin{solutionblock}
展开为
\[
z^2+2z|x|+x^2.
\]
交叉项关于 \(z\) 对称积分为零。球面上
\[
\iint_\Sigma x^2\,dS=\iint_\Sigma z^2\,dS=\frac{4\pi R^4}{3}.
\]
故结果
\[
\boxed{\frac{8\pi R^4}{3}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{16.} \(\Sigma\) 为上半球面 \(x^2+y^2+z^2=a^2,z\ge0\)，求
\[
\iint_\Sigma(2x+z+1)^2\,dS.
\]
\end{problemblock}
\begin{solutionblock}
利用上半球关于 \(yOz\) 面对称，含 \(x\) 的一次项及 \(xz\) 项积分为零：
\[
\iint(2x+z+1)^2dS
=4\iint x^2dS+\iint z^2dS+\iint1\,dS+2\iint z\,dS.
\]
上半球上
\[
\iint x^2dS=\iint z^2dS=\frac{2\pi a^4}{3},\quad
\iint1\,dS=2\pi a^2,\quad
\iint z\,dS=\pi a^3.
\]
故
\[
\boxed{\frac{10\pi a^4}{3}+2\pi a^3+2\pi a^2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{17.} \(\Omega\) 由锥面 \(z=\sqrt{x^2+y^2}\) 与半球面 \(z=\sqrt{R^2-x^2-y^2}\) 围成，\(\Sigma\) 为整个边界外侧，求
\[
\iint_\Sigma x\,dydz+y\,dzdx+z\,dxdy.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{这是向量场 \((x,y,z)\) 的外通量。}
散度为 \(3\)。区域在柱坐标中
\[
0\le r\le\frac{R}{\sqrt2},\quad r\le z\le\sqrt{R^2-r^2}.
\]
体积为
\[
V=2\pi\int_0^{R/\sqrt2}\left(\sqrt{R^2-r^2}-r\right)r\,dr
=\frac{2\pi R^3}{3}\left(1-\frac1{\sqrt2}\right).
\]
故通量为
\[
\boxed{2\pi R^3\left(1-\frac1{\sqrt2}\right)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{18.} 圆柱面 \((x-1)^2+y^2=1\) 介于 \(z=0\) 与上半圆锥面 \(z=\sqrt{x^2+y^2}\) 之间的面积。
\end{problemblock}
\begin{solutionblock}
参数化
\[
x=1+\cos\theta,\quad y=\sin\theta.
\]
圆柱半径为 \(1\)，故 \(dS=d\theta dz\)。上界
\[
z=\sqrt{x^2+y^2}=\sqrt{2+2\cos\theta}=2|\cos(\theta/2)|.
\]
面积为
\[
\int_0^{2\pi}2|\cos(\theta/2)|\,d\theta=\boxed{8}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{19.} \(\Omega=\{(x,y,z):x^2+y^2\le z\le1\}\)，求形心竖坐标。
\end{problemblock}
\begin{solutionblock}
高度为 \(z\) 的截面面积为 \(\pi z\)。故
\[
V=\int_0^1\pi z\,dz=\frac{\pi}{2},
\quad
M_z=\int_0^1z\cdot\pi z\,dz=\frac{\pi}{3}.
\]
于是
\[
\boxed{\bar z=\frac{M_z}{V}=\frac23}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{20.} 计算
\[
\iiint_\Omega x(1+z)\,dv,
\]
其中 \(\Omega\) 由 \(x=y^2+z^2,\ x^2=y^2+z^2\) 围成。
\end{problemblock}
\begin{solutionblock}
在 \(yz\) 平面用极坐标 \(y=r\cos\theta,z=r\sin\theta\)，区域为
\[
0\le r\le1,\quad r^2\le x\le r.
\]
含 \(xz\) 的部分关于 \(z\) 对称为零，故
\[
I=2\pi\int_0^1r\,dr\int_{r^2}^{r}x\,dx
=\pi\int_0^1(r^3-r^5)\,dr
=\boxed{\frac{\pi}{12}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{21.} 计算
\[
\iiint_\Omega |z-x^2-y^2|\,dv,\quad 0\le z\le1,\ x^2+y^2\le1.
\]
\end{problemblock}
\begin{solutionblock}
柱坐标下 \(r^2=x^2+y^2\)，
\[
I=2\pi\int_0^1r\,dr\int_0^1|z-r^2|\,dz.
\]
而
\[
\int_0^1|z-a|dz=\frac{a^2}{2}+\frac{(1-a)^2}{2}.
\]
取 \(a=r^2\)，得
\[
I=2\pi\int_0^1r\left(r^4-r^2+\frac12\right)dr
=\boxed{\frac{\pi}{3}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{22.} 计算
\[
\int_0^1dx\int_0^{1-x}dy\int_0^{1-x-y}(1-y)e^{-(1-y-z)^2}\,dz.
\]
\end{problemblock}
\begin{solutionblock}
对 \(x\) 先积分，长度为 \(1-y-z\)。于是
\[
I=\int_{\substack{y,z\ge0\\y+z\le1}}(1-y)(1-y-z)e^{-(1-y-z)^2}\,dydz.
\]
令 \(v=1-y\)，再令 \(u=1-y-z\)，得
\[
I=\int_0^1v\int_0^v u e^{-u^2}\,du\,dv
=\frac12\int_0^1v(1-e^{-v^2})\,dv
=\boxed{\frac1{4e}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{23.} \(L\) 为第一象限中两段圆弧组成的曲线，求
\[
\int_L3x^2y\,dx+(x^3+x-2y)\,dy.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{用 \(y\) 轴线段闭合，Green 公式给面积。}
\[
Q_x-P_y=(3x^2+1)-3x^2=1.
\]
闭合区域面积为
\[
\frac14\pi(2)^2-\frac12\pi(1)^2=\frac{\pi}{2}.
\]
闭合线中 \(y\) 轴从 \((0,2)\) 到 \((0,0)\) 的积分为
\[
\int_2^0(-2y)\,dy=4.
\]
故原积分
\[
I+4=\frac{\pi}{2},
\quad
\boxed{I=\frac{\pi}{2}-4}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{24.} \(L:y=\sin x\) 从 \((- \pi,0)\) 到 \((\pi,0)\)，求
\[
\int_L(e^{-x^2}\sin x+3y-\cos y)\,dx+(x\sin y-y^4)\,dy.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{把微分形式拆成奇函数积分和全微分。}
\[
-\cos y\,dx+x\sin y\,dy=d(-x\cos y).
\]
两端点 \(y=0\)，故该部分贡献
\[
[-x\cos y]_{-\pi}^{\pi}=-2\pi.
\]
\(e^{-x^2}\sin x\,dx\) 与 \(3\sin x\,dx\) 在对称区间积分为零，\(-y^4dy\) 为全微分且端点 \(y=0\)，贡献为零。故
\[
\boxed{-2\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{25.} \(C\) 为上半椭圆从 \((-a,0)\) 到 \((a,0)\)，计算
\[
\int_C\frac{(x-y)dx+(x+y)dy}{x^2+y^2}.
\]
\end{problemblock}
\begin{solutionblock}
拆为
\[
\frac{x\,dx+y\,dy}{x^2+y^2}+\frac{-y\,dx+x\,dy}{x^2+y^2}.
\]
第一项为 \(\frac12d\ln(x^2+y^2)\)，端点半径相同，贡献为零。第二项为极角微分 \(d\theta\)。沿上半椭圆从左到右，极角由 \(\pi\) 变为 \(0\)，故
\[
\boxed{-\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{26.} 路径 \(L\) 从 \(A(-1,0)\) 经下半圆到 \(B(1,0)\)，再沿线段到 \(C(-1,2)\)，求
\[
\int_L\frac{x\,dy-y\,dx}{4x^2+y^2}.
\]
\end{problemblock}
\begin{solutionblock}
令 \(X=2x,Y=y\)，则
\[
\frac{xdy-ydx}{4x^2+y^2}
=\frac12\frac{X\,dY-Y\,dX}{X^2+Y^2}
=\frac12d\arg(X,Y).
\]
在变换后的路径上，极角总增量为
\[
\pi+\frac{3\pi}{4}=\frac{7\pi}{4}.
\]
故积分为
\[
\boxed{\frac{7\pi}{8}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{27.} 曲线积分
\[
\int_L2xy\,dx+Q(x,y)\,dy
\]
与路径无关，并满足题给两条路径积分相等，求 \(Q\)。
\end{problemblock}
\begin{solutionblock}
路径无关给
\[
Q_x=(2xy)_y=2x,
\]
所以
\[
Q=x^2+\varphi(y).
\]
势函数可取
\[
F=x^2y+\psi(y),\quad \psi'=\varphi.
\]
题设给
\[
F(t,1)-F(0,0)=F(1,t)-F(0,0),
\]
即
\[
t^2+\psi(1)=t+\psi(t).
\]
故
\[
\psi(t)=t^2-t+\psi(1),
\quad
\varphi(y)=2y-1.
\]
因此
\[
\boxed{Q(x,y)=x^2+2y-1}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{28.} 已知
\[
\int_{(0,0)}^{(t,t^2)}f(x,y)\,dx+x\cos y\,dy=t^2
\]
且积分与路径无关，求 \(f\)。
\end{problemblock}
\begin{solutionblock}
路径无关要求
\[
f_y=(x\cos y)_x=\cos y.
\]
故
\[
f=\sin y+\varphi(x).
\]
势函数可取
\[
F=x\sin y+\psi(x),\quad \psi'=\varphi.
\]
由题设
\[
t\sin(t^2)+\psi(t)-\psi(0)=t^2,
\]
故
\[
\psi(x)=x^2-x\sin x^2+\psi(0).
\]
于是
\[
\boxed{f(x,y)=\sin y+2x-\sin x^2-2x^2\cos x^2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{29.} 证明题给曲线积分与路径无关，并在 \(ab=cd\) 时求值。
\end{problemblock}
\begin{solutionblock}
记
\[
P=\frac1y+yf(xy),\qquad Q=xf(xy)-\frac{x}{y^2}.
\]
直接求偏导：
\[
P_y=-\frac1{y^2}+f(xy)+xyf'(xy)=Q_x.
\]
故在上半平面内路径无关。若 \(H'(u)=f(u)\)，势函数可取
\[
F=\frac{x}{y}+H(xy).
\]
于是从 \((a,b)\) 到 \((c,d)\) 的积分为
\[
\frac{c}{d}-\frac{a}{b}+H(cd)-H(ab).
\]
当 \(ab=cd\) 时，
\[
\boxed{I=\frac{c}{d}-\frac{a}{b}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{30.} 已知
\[
\int_L\frac{\varphi(y)\,dx+2xy\,dy}{2x^2+y^4}
\]
在围绕原点的任意简单闭曲线上恒为同一常数，求 \(\varphi\)。
\end{problemblock}
\begin{solutionblock}
\analysis{在右半平面无奇点，闭曲线积分应为零；再用 \(P_y=Q_x\)。}
对右半平面内任意闭曲线，可与不围绕原点的曲线连续变形，积分常数只能为 \(0\)。因此在 \(x>0\) 内
\[
P_y=Q_x.
\]
其中
\[
P=\frac{\varphi(y)}{2x^2+y^4},\qquad Q=\frac{2xy}{2x^2+y^4}.
\]
比较 \(x^2\) 与常数项系数，得
\[
\varphi'(y)=-2y,\qquad \varphi(y)=-y^2.
\]
故
\[
\boxed{\varphi(y)=-y^2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{31.} 已知任意简单闭曲线 \(C\) 上积分为零，求 \(f,g\) 并计算从 \((0,0)\) 到 \((1,1)\) 的积分。
\end{problemblock}
\begin{solutionblock}
由闭曲线积分恒为零，微分形式恰当：
\[
P_y=Q_x.
\]
比较得
\[
g'=f,\qquad f'=2e^x+2g.
\]
故
\[
g''-2g=2e^x,\quad g(0)=0,\quad g'(0)=0.
\]
解得
\[
g=\left(1+\frac{\sqrt2}{2}\right)e^{\sqrt2x}
\left(1-\frac{\sqrt2}{2}\right)e^{-\sqrt2x}-2e^x,
\quad f=g'.
\]
势函数为
\[
F=y^2g(x)+yf(x).
\]
故所求积分为
\[
\boxed{g(1)+f(1)}
\]
即
\[
\boxed{(1+\sqrt2)\left(1+\frac{\sqrt2}{2}\right)e^{\sqrt2}
(1-\sqrt2)\left(1-\frac{\sqrt2}{2}\right)e^{-\sqrt2}-4e }.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{32.} 证明
\[
\int_C\frac{\partial u}{\partial n}\,ds
=\iint_D(u_{xx}+u_{yy})\,dxdy.
\]
\end{problemblock}
\begin{solutionblock}
设外法线 \(\boldsymbol n=(n_x,n_y)\)。则
\[
\frac{\partial u}{\partial n}ds=u_x\,dy-u_y\,dx.
\]
由 Green 公式，
\[
\int_Cu_x\,dy-u_y\,dx
=\iint_D\left[(u_x)_x-(-u_y)_y\right]dxdy
=\iint_D(u_{xx}+u_{yy})dxdy.
\]
证毕。
\end{solutionblock}

\begin{problemblock}
\textbf{33.} \(f\) 在单位圆盘上二阶连续可微，且
\[
f_{xx}+f_{yy}=e^{-(x^2+y^2)}.
\]
计算
\[
\iint_{x^2+y^2\le1}(xf_x+yf_y)\,dxdy.
\]
\end{problemblock}
\begin{solutionblock}
记
\[
F(r)=\int_0^{2\pi}f(r,\theta)\,d\theta.
\]
由极坐标 Laplace 公式积分得
\[
(rF'(r))'=2\pi r e^{-r^2},
\]
且 \(rF'(r)|_{r=0}=0\)，故
\[
rF'(r)=\pi(1-e^{-r^2}).
\]
原积分为
\[
\int_0^1r^2F'(r)\,dr
=\pi\int_0^1r(1-e^{-r^2})\,dr
=\boxed{\frac{\pi}{2e}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{34.} \(\Gamma\) 为球 \(x^2+y^2+z^2=a^2\) 与平面 \(x+y+z=0\) 的交线，从 \(z\) 轴正向看为逆时针，求
\[
\int_\Gamma y\,dx+z\,dy+x\,dz.
\]
\end{problemblock}
\begin{solutionblock}
令 \(\boldsymbol F=(y,z,x)\)，则
\[
\nabla\times\boldsymbol F=(-1,-1,-1).
\]
取法向量 \(\boldsymbol n=(1,1,1)/\sqrt3\)，其 \(z\) 分量为正，符合题设方向。圆盘面积为 \(\pi a^2\)。由 Stokes 公式，
\[
I=(-1,-1,-1)\cdot\boldsymbol n\cdot\pi a^2
=\boxed{-\sqrt3\pi a^2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{35.} \(\Gamma\) 为锥面 \(z=\sqrt{x^2+y^2}\) 与柱面 \(x^2+y^2=2ax\) 的交线，从 \(z\) 轴正向看为逆时针，求
\[
\int_\Gamma xy\,dx+z^2\,dy+zx\,dz.
\]
\end{problemblock}
\begin{solutionblock}
令 \(\boldsymbol F=(xy,z^2,zx)\)，则
\[
\nabla\times\boldsymbol F=(-2z,-z,-x).
\]
取锥面 \(z=r\) 上投影圆盘 \(D:x^2+y^2\le2ax\)，上侧法向量对应
\[
(-z_x,-z_y,1)=\left(-\frac{x}{r},-\frac{y}{r},1\right).
\]
于是旋度点乘该向量化为
\[
x+y.
\]
因此
\[
I=\iint_D(x+y)\,dxdy.
\]
圆盘 \(D\) 圆心为 \((a,0)\)，半径为 \(a\)，故
\[
\iint_Dx\,dxdy=a\cdot\pi a^2=\pi a^3,\qquad
\iint_Dy\,dxdy=0.
\]
所以
\[
\boxed{\pi a^3}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{36.} 证明
\[
\iint_\Sigma (x+y+z+\sqrt3a)^3\,dS\ge108\pi a^5,
\]
其中
\[
\Sigma:x^2+y^2+z^2=2ax+2ay+2az-2a^2.
\]
\end{problemblock}
\begin{solutionblock}
配方得
\[
(x-a)^2+(y-a)^2+(z-a)^2=a^2,
\]
故 \(\Sigma\) 是半径为 \(a\)、中心 \((a,a,a)\) 的球面。对球面上任一点，
\[
(x-a)+(y-a)+(z-a)\ge-\sqrt3a,
\]
所以
\[
x+y+z+\sqrt3a\ge3a.
\]
因此
\[
\iint_\Sigma (x+y+z+\sqrt3a)^3\,dS
\ge (3a)^3\cdot4\pi a^2
=\boxed{108\pi a^5}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{37.} 椭球面 \(S:x^2+y^2+z^2-yz=1\)。求切平面与 \(xOy\) 面垂直时点 \(P\) 的轨迹 \(C\)，并计算题给曲面积分。
\end{problemblock}
\begin{solutionblock}
\analysis{切平面法向量为 \((2x,2y-z,2z-y)\)。与 \(xOy\) 面垂直等价于两个平面法向量垂直，即 \(2z-y=0\)。}
故轨迹为
\[
\boxed{C:\ y=2z,\quad x^2+3z^2=1}.
\]
把椭球投影到 \(yz\) 平面。由
\[
x=\pm\sqrt{1-y^2-z^2+yz},
\]
且
\[
dS=\frac{\sqrt{4+y^2+z^2-4yz}}{2|x|}\,dydz.
\]
两片 \(x>0,x<0\) 相加后，题中 integrand 化为
\[
\sqrt3\,\frac{|y-2z|}{\sqrt{1-y^2-z^2+yz}}\,dydz.
\]
在投影椭圆 \(y^2+z^2-yz\le1\) 的 \(C\) 上方取半边，作线性变换化为单位圆半盘，可得
\[
I=2\pi.
\]
故
\[
\boxed{I=2\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{38.} 计算
\[
\iint_\Sigma xz\,dydz+2zy\,dzdx+3xy\,dxdy,
\]
其中 \(\Sigma:z=1-x^2-y^2/4\) 为上侧。
\end{problemblock}
\begin{solutionblock}
向量场为 \((xz,2zy,3xy)\)，散度为
\[
z+2z+0=3z.
\]
用底面闭合，底面通量因 \(3xy\) 对称为零，故
\[
I=\iiint_\Omega3z\,dv.
\]
令 \(y=2v,x=u\)，底面化为单位圆，Jacobian 为 \(2\)。于是
\[
I=3\int_{u^2+v^2\le1}(1-u^2-v^2)^2\,dudv
=\boxed{\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{39.} 计算椭球面外侧通量
\[
\iint_\Sigma\frac{x\,dydz+y\,dzdx+z\,dxdy}{(x^2+y^2+z^2)^{3/2}}.
\]
\end{problemblock}
\begin{solutionblock}
\analysis{这是点源场 \(\boldsymbol r/r^3\) 穿过包围原点闭曲面的通量。}
该场在原点外散度为零，穿过任意包围原点的闭曲面通量等于穿过单位球面的通量：
\[
\boxed{4\pi}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{40.} 对任意闭曲面通量为零，求 \(f(x)\)，并计算题给内侧曲面积分。
\end{problemblock}
\begin{solutionblock}
向量场为
\[
\boldsymbol F=\left(yf'(x)+yz,\ -\frac12y^2f(x),\ -zy\sin x+y^2\right).
\]
任意闭曲面通量为零，故散度恒为零：
\[
\operatorname{div}\boldsymbol F
=y(f''-f-\sin x)=0.
\]
于是
\[
f''-f=\sin x,\quad f(0)=0,\quad f'(0)=1.
\]
解得
\[
\boxed{f(x)=\frac32\sinh x-\frac12\sin x}.
\]
因散度为零，抛物面侧面内侧通量等于顶面 \(z=1,r\le1\) 的外通量：
\[
\iint_{x^2+y^2\le1}(-y\sin x+y^2)\,dxdy=\iint y^2\,dxdy=\frac{\pi}{4}.
\]
故所求为
\[
\boxed{\frac{\pi}{4}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{41.} 上半单位球面上侧 \(\Sigma\)，连续函数 \(f(x,y)\) 满足
\[
f(x,y)=2xy^2+x^2+\iint_\Sigma y^3\,dydz+x^3\,dzdx+zf(x,y)\,dxdy.
\]
求 \(f(x,y)\)。
\end{problemblock}
\begin{solutionblock}
设曲面积分为常数 \(K\)，则
\[
f(x,y)=2xy^2+x^2+K.
\]
用底面闭合上半球，底面 \(z=0\) 通量为零。向量场散度为
\[
f(x,y).
\]
故
\[
K=\iiint_{\Omega}f(x,y)\,dv
=\iiint_\Omega x^2\,dv+K\,V,
\]
其中上半单位球
\[
\iiint_\Omega x^2\,dv=\frac{2\pi}{15},\qquad V=\frac{2\pi}{3}.
\]
解得
\[
K=\frac{2\pi}{15-10\pi}.
\]
因此
\[
\boxed{f(x,y)=2xy^2+x^2+\frac{2\pi}{15-10\pi}}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{42.} 直线过 \(A(1,0,0)\)、\(B(0,1,1)\)，绕 \(z\) 轴成曲面 \(\Sigma\)，并与 \(z=0,z=2\) 围成立体 \(\Omega\)。求曲面方程与形心。
\end{problemblock}
\begin{solutionblock}
直线参数为
\[
(x,y,z)=(1-s,s,s).
\]
即
\[
x=1-z,\quad y=z.
\]
绕 \(z\) 轴旋转保持 \(z\) 与半径平方，故
\[
\boxed{x^2+y^2=(1-z)^2+z^2}.
\]
立体关于 \(z\) 轴对称，故
\[
\bar x=\bar y=0.
\]
截面半径平方
\[
R^2(z)=2z^2-2z+1,\quad 0\le z\le2.
\]
体积
\[
V=\pi\int_0^2R^2(z)\,dz=\frac{10\pi}{3}.
\]
竖坐标
\[
\bar z=\frac{\pi\int_0^2zR^2(z)\,dz}{V}
=\frac{14\pi/3}{10\pi/3}
=\frac75.
\]
形心为
\[
\boxed{\left(0,0,\frac75\right)}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{43.} 确定 \(\lambda\)，使
\[
\boldsymbol A=\frac{2xy}{(x^4+y^2)^\lambda}\boldsymbol i
-\frac{x^2}{(x^4+y^2)^\lambda}\boldsymbol j
\]
在 \(x>0\) 上为某函数梯度，并求 \(u\)。
\end{problemblock}
\begin{solutionblock}
令 \(P,Q\) 为两个分量，梯度场要求 \(P_y=Q_x\)。计算并比较系数得
\[
\lambda=1.
\]
此时
\[
P=\frac{2xy}{x^4+y^2},\qquad Q=-\frac{x^2}{x^4+y^2}.
\]
注意
\[
d\arctan\frac{y}{x^2}
=-\frac{2xy}{x^4+y^2}dx+\frac{x^2}{x^4+y^2}dy.
\]
故
\[
\boxed{u(x,y)=-\arctan\frac{y}{x^2}+C}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{44.} 质点沿以 \(AB\) 为直径的半圆从 \(A(1,2)\) 到 \(B(3,4)\)，力大小为 \(OP\)，方向垂直 \(OP\) 且与 \(y\) 轴正向夹角小于 \(\pi/2\)。求功。
\end{problemblock}
\begin{solutionblock}
力向量为
\[
\boldsymbol F=(-y,x).
\]
功为
\[
W=\int_C -y\,dx+x\,dy.
\]
用直径 \(BA\) 闭合。半圆半径为
\[
\frac{|AB|}{2}=\sqrt2,
\]
半圆面积为 \(\pi\)。闭合曲线积分为
\[
2\times\text{面积}=2\pi.
\]
直径从 \(B\) 到 \(A\) 的积分为 \(2\)，所以半圆弧上的功为
\[
\boxed{2\pi-2}.
\]
\end{solutionblock}

\begin{problemblock}
\textbf{45.} 密度为 \(1\) 的空间体 \(\Omega:x^2+y^2\le z\le1\)。
\begin{enumerate}
\item 求对 \(z\) 轴的转动惯量。
\item 求对直线 \(x=y=z\) 的转动惯量。
\end{enumerate}
\end{problemblock}
\begin{solutionblock}
\analysis{柱坐标中 \(0\le z\le1,\ 0\le r\le\sqrt z\)。}
对 \(z\) 轴：
\[
I_z=\iiint_\Omega r^2\,dv
=2\pi\int_0^1dz\int_0^{\sqrt z}r^3\,dr
=\boxed{\frac{\pi}{6}}.
\]
对直线 \(x=y=z\)，单位方向为 \(\boldsymbol e=(1,1,1)/\sqrt3\)，距离平方为
\[
\rho^2=x^2+y^2+z^2-\frac{(x+y+z)^2}{3}.
\]
区域关于 \(z\) 轴对称，交叉项积分为零，故
\[
I=\frac23\iiint_\Omega(x^2+y^2+z^2)\,dv.
\]
其中
\[
\iiint_\Omega(x^2+y^2)\,dv=\frac{\pi}{6},\qquad
\iiint_\Omega z^2\,dv=\frac{\pi}{4}.
\]
于是
\[
I=\frac23\left(\frac{\pi}{6}+\frac{\pi}{4}\right)
=\boxed{\frac{5\pi}{18}}.
\]
\end{solutionblock}

\section{本章小结}
第九章共 \(45\) 题，核心是 Green 公式、Gauss 公式、Stokes 公式、路径无关、通量、形心与转动惯量。遇到闭曲线/闭曲面，优先考虑把积分转化为区域积分或体积分。
"""


def clean_project() -> None:
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    FIGURES.mkdir(parents=True, exist_ok=True)
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(exist_ok=True)


def render_pages() -> None:
    doc = fitz.open(str(PDF))
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        pix.save(str(FIGURES / f"page_{i:03d}.png"))


def write_project_files() -> None:
    (PROJECT / "main.tex").write_text(MAIN_TEX, encoding="utf-8")
    (CHAPTERS / "ch01.tex").write_text(CH01_TEX, encoding="utf-8")
    (CHAPTERS / "ch02.tex").write_text(CH02_TEX, encoding="utf-8")
    (CHAPTERS / "ch03.tex").write_text(CH03_TEX, encoding="utf-8")
    (CHAPTERS / "ch04.tex").write_text(CH04_TEX, encoding="utf-8")
    (CHAPTERS / "ch05.tex").write_text(CH05_TEX, encoding="utf-8")
    (CHAPTERS / "ch06.tex").write_text(CH06_TEX, encoding="utf-8")
    (CHAPTERS / "ch07.tex").write_text(CH07_TEX, encoding="utf-8")
    (CHAPTERS / "ch08.tex").write_text(CH08_TEX, encoding="utf-8")
    (CHAPTERS / "ch09.tex").write_text(CH09_TEX, encoding="utf-8")
    (PROJECT / "README.md").write_text(
        "# 武忠祥高数强化严选题数一做题本解析\n\n"
        "Overleaf 导入方式：上传 `wzx_gaoshu_solution_overleaf.zip`，主文件选择 `main.tex`，编译器建议使用 XeLaTeX。\n\n"
        "当前版本已包含完整原题页图片、LaTeX 工程结构，以及第一章至第九章全书解析。\n",
        encoding="utf-8",
    )


def write_manifest() -> None:
    tex_files = sorted(p.relative_to(PROJECT).as_posix() for p in PROJECT.rglob("*.tex"))
    figures = sorted(p.relative_to(PROJECT).as_posix() for p in FIGURES.glob("*.png"))
    manifest = [
        "Overleaf project manifest",
        f"source_pdf: {PDF.name}",
        f"tex_files: {len(tex_files)}",
        f"figure_pages: {len(figures)}",
        "",
        "TeX files:",
        *tex_files,
        "",
        "Original page figures:",
        *figures,
    ]
    (PROJECT / "MANIFEST.txt").write_text("\n".join(manifest), encoding="utf-8")


def zip_project() -> Path:
    zip_path = DIST / "wzx_gaoshu_solution_overleaf.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in PROJECT.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(PROJECT))
    return zip_path


def main() -> None:
    clean_project()
    render_pages()
    write_project_files()
    write_manifest()
    zip_path = zip_project()
    text = (ROOT / "extracted_text.txt").read_text(encoding="utf-8") if (ROOT / "extracted_text.txt").exists() else ""
    rough_numbers = sorted({int(m.group(1)) for m in re.finditer(r"(?<!\d)(\d{1,3})\.", text)})
    print(f"PDF: {PDF.name}")
    print(f"Project: {PROJECT}")
    print(f"Zip: {zip_path}")
    print(f"Rendered pages: {len(list(FIGURES.glob('*.png')))}")
    print(f"Rough numbered items detected: {len(rough_numbers)}")


if __name__ == "__main__":
    main()
