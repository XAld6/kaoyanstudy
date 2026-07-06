from pathlib import Path

BASE = Path(r"D:\xm\mz_linear_solution_project\chapters")


def find_macro(text: str, start: int, name: str):
    needle = "\\" + name + "{"
    pos = text.find(needle, start)
    if pos < 0:
        return None
    i = pos + len(needle)
    depth = 1
    j = i
    while j < len(text) and depth:
        c = text[j]
        if c == "\\" and j + 1 < len(text) and text[j + 1] in "{}":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        j += 1
    return pos, i, j - 1, text[i : j - 1]


def replace_question_by_label(path: Path, mapping: dict[str, str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    changed = []
    for label, newq in mapping.items():
        lab = "\\textbf{" + label + "}"
        start = text.find(lab)
        if start < 0:
            raise RuntimeError(f"label not found: {path.name} {label}")
        block_end = text.find("\\end{solutionblock}", start)
        q = find_macro(text, start, "question")
        if not q or q[0] > block_end:
            raise RuntimeError(f"question not found in {path.name} {label}")
        _, q_content_start, q_content_end, _ = q
        text = text[:q_content_start] + newq.strip() + text[q_content_end:]
        changed.append(label)
    path.write_text(text, encoding="utf-8")
    return changed


M2 = {
    "2.4 例 2": r"""设
\[
A=\begin{pmatrix}
2&6&4\\
-1&-3&-2\\
2&6&4
\end{pmatrix}.
\]
求 \(A^n\)（\(n\ge3\)）。""",
    "2.4 例 3": r"""设 \(A\) 为四阶矩阵，其主对角线元素均为 \(1\)，非主对角线元素均为 \(-1\)。求 \(A^n\)。""",
    "2.4 例 5": r"""设
\[
A=\begin{pmatrix}
0&0&0\\
2&0&0\\
1&3&0
\end{pmatrix}.
\]
求 \(A^2\) 与 \(A^3\)。""",
    "2.4 例 6": r"""设
\[
A=\begin{pmatrix}
1&0&0\\
1&1&0\\
0&1&1
\end{pmatrix}.
\]
求 \(A^n\)（\(n\ge3\)）。""",
    "2.5 例 1": r"""设 \(A\) 为反对称矩阵，\(\alpha\) 为同维列向量。证明 \(\alpha^TA\alpha=0\)。""",
    "2.5 例 2": r"""设列向量 \(X\) 满足 \(X^TX=1\)，令
\[
H=E-2XX^T.
\]
证明 \(H\) 为对称矩阵且为正交矩阵。""",
    "2.6 例 1": r"""设
\[
A=\begin{pmatrix}
0&1&3\\
1&-1&0\\
-1&2&1
\end{pmatrix}.
\]
求伴随矩阵 \(A^*\)。""",
    "2.6 例 2": r"""设 \(A\) 为三阶矩阵，\(|A|=2\)。交换 \(A\) 的第 \(1\) 行与第 \(3\) 行得到 \(B\)，求 \(|BA^*|\)。""",
    "2.6 例 3": r"""设三阶矩阵 \(A\) 满足 \(A^*=A^T\)，且第一行三个元素相等并均为正数。求第一行元素的值，并判断正确选项。""",
    "2.6 例 4": r"""设 \(A\) 为方阵且 \(A^n=E\)。求 \((A^*)^n\)。""",
    "2.7 例 1": r"""设方阵 \(A\) 满足
\[
A^2-3A-10E=O.
\]
求 \(A^{-1}\) 与 \((A-4E)^{-1}\)。""",
    "2.7 例 3": r"""设同阶方阵 \(A,B,C\) 满足 \(ABC=E\)。判断 \(BCA,CAB,ACB,BAC,CBA\) 中哪些必等于 \(E\)。""",
    "2.7 例 5": r"""设 \(A,B\) 为同阶方阵。判断下列命题中正确的一项：
\begin{enumerate}
\item 若 \(A\) 或 \(B\) 可逆，则 \(AB\) 可逆；
\item 若 \(A\) 或 \(B\) 不可逆，则 \(AB\) 不可逆；
\item 若 \(A,B\) 均可逆，则 \(A+B\) 可逆；
\item 若 \(A,B\) 均不可逆，则 \(A+B\) 不可逆。
\end{enumerate}""",
    "2.7 例 6": r"""设
\[
A=\begin{pmatrix}
1&0&1\\
0&3&0\\
0&0&1
\end{pmatrix}.
\]
求 \((A+2E)^{-1}(A^2-4E)\)。""",
    "2.7 例 7": r"""设 \(A\) 为三阶可逆矩阵，\(|A|=\dfrac12\)。求行列式
\[
\left|(3A)^{-1}-2A^*\right|.
\]""",
    "2.7 例 8": r"""设 \(A,B\) 为同阶可逆矩阵，且 \(|A|=1,\ |B|=2,\ |A+B|=2\)。求
\[
\left|\left(A^{-1}+B^{-1}\right)^{-1}\right|.
\]""",
    "2.7 例 9": r"""设 \(A\) 为 \(n\ge3\) 阶可逆矩阵。判断关于伴随矩阵、逆矩阵和数乘矩阵伴随的四个结论是否正确。""",
    "2.7 例 10": r"""设
\[
A=\begin{pmatrix}
a&1&0\\
1&a&-1\\
0&1&a
\end{pmatrix}.
\]
(1) 若 \(A^3=O\)，求 \(a\)；(2) 在此条件下，解矩阵方程
\[
X-XA^2-AX+AXA^2=E.
\]""",
    "2.8 例 1": r"""计算矩阵乘积
\[
AB=\begin{pmatrix}
1&0&1&2\\
0&1&3&4\\
0&0&1&0\\
0&0&0&-1
\end{pmatrix}
\begin{pmatrix}
1&0&0&0\\
0&1&0&0\\
2&1&1&0\\
0&3&0&-1
\end{pmatrix}.
\]""",
    "2.8 例 2": r"""设
\[
A=\begin{pmatrix}
1&0&0&0&0\\
0&1&0&0&0\\
-1&2&1&0&0\\
1&1&0&1&0\\
0&1&0&0&1
\end{pmatrix},\quad
B=\begin{pmatrix}
1&0&0&0\\
-1&0&0&0\\
0&1&2&-1\\
0&2&1&2\\
0&1&2&1
\end{pmatrix}.
\]
求 \(AB\)。""",
    "2.8 例 3": r"""设分块矩阵
\[
A=\begin{pmatrix}C&O\\O&D\end{pmatrix},\quad
C=\begin{pmatrix}1&1\\2&2\end{pmatrix},\quad
D=\begin{pmatrix}0&1&0\\0&0&1\\0&0&0\end{pmatrix}.
\]
求 \(A^{100}\)。""",
    "2.8 例 4": r"""设
\[
A=\begin{pmatrix}
0&2&0\\
0&0&-3\\
4&0&0
\end{pmatrix}.
\]
求 \(A^{-1}\)。""",
    "2.8 例 5": r"""设 \(A,B\) 为二阶可逆矩阵，\(|A|=2,\ |B|=3\)，令
\[
M=\begin{pmatrix}O&A\\B&O\end{pmatrix}.
\]
求 \(M^*\)，并判断正确选项。""",
    "2.9 例 1": r"""将矩阵
\[
\begin{pmatrix}
1&-1&0&2\\
0&2&2&-1\\
0&0&3&-1\\
0&0&0&0
\end{pmatrix}
\]
化为标准形。""",
    "2.9 例 2": r"""设矩阵 \(A=(\alpha_1,\alpha_2,\alpha_3)\)，矩阵
\[
B=(3\alpha_1,\ 3\alpha_1-2\alpha_2,\ \alpha_3).
\]
判断 \(A\) 与 \(B\) 是否等价。""",
    "2.9 例 3": r"""设
\[
P=\begin{pmatrix}0&1&0\\1&0&0\\0&0&1\end{pmatrix},\quad
M=\begin{pmatrix}1&2&3\\4&5&6\\7&8&9\end{pmatrix},\quad
Q=\begin{pmatrix}1&-1&0\\0&1&0\\0&0&1\end{pmatrix}.
\]
求 \(PMQ\)。""",
    "2.9 例 4": r"""设三阶可逆矩阵 \(A=(\alpha_1,\alpha_2,\alpha_3)\)，\(|A|=2\)，且
\[
B=(\alpha_1,\alpha_2,3\alpha_1+\alpha_3).
\]
求 \(A^*B\)。""",
    "2.9 例 5": r"""设 \(P_1\) 表示交换矩阵的第 \(1,2\) 行，\(P_2\) 表示交换矩阵的第 \(2,3\) 列。若 \(P_1AP_2=E\)，判断 \(A^*\) 的正确表达式。""",
    "2.9 例 6": r"""设
\[
A=\begin{pmatrix}
0&1&3\\
1&-1&0\\
-1&2&1
\end{pmatrix}.
\]
求 \(A^{-1}\)。""",
    "2.10 例 1": r"""设 \(a_1,a_2,\ldots,a_5\) 两两不同，矩阵 \(A\) 的第 \(i\) 列为
\[
(1,a_i,a_i^2,a_i^3,(a_i+1)^3)^T\quad(i=1,2,\ldots,5).
\]
求 \(r(A)\)。""",
    "2.10 例 2": r"""设
\[
A=\begin{pmatrix}
1&2&-1&1\\
2&0&a&0\\
0&-4&5&-2
\end{pmatrix}.
\]
若 \(r(A)=2\)，求 \(a\)。""",
    "2.10 例 3": r"""设矩阵 \(A,B\) 满足 \(B\) 可逆，其中
\[
B=\begin{pmatrix}
1&0&4\\
0&2&0\\
2&0&3
\end{pmatrix}.
\]
根据题给矩阵 \(A\) 与 \(B\)，求 \(r(AB)\)。""",
    "2.10 例 4": r"""设 \(A\) 为 \(m\times n\) 矩阵，\(r(A)=r<m<n\)。判断关于子式、行列式和标准形的四个命题中正确命题的个数。""",
    "2.10 例 5": r"""设 \(A\) 为 \(m\times n\) 矩阵，\(B\) 为 \(n\times m\) 矩阵。判断关于 \(|AB|\) 与 \(m,n\) 大小关系的选项是否正确。""",
    "2.10 例 7": r"""设非零三阶矩阵 \(P\) 与
\[
Q=\begin{pmatrix}
1&2&3\\
2&4&k\\
3&6&9
\end{pmatrix}
\]
满足 \(PQ=O\)。判断 \(k\) 与 \(r(P)\) 的正确关系。""",
    "2.10 例 8": r"""设
\[
A=\begin{pmatrix}
a&b&b\\
b&a&b\\
b&b&a
\end{pmatrix},
\]
且 \(r(A^*)=1\)。判断 \(a,b\) 应满足的正确条件。""",
    "2.10 例 9": r"""设 \(A\) 为 \(n\) 阶幂等矩阵，即 \(A^2=A\)。证明并求与 \(r(A)\)、\(r(E-A)\) 有关的结论。""",
}

M3 = {
    "3.2 例 1": r"""求解线性方程组
\[
\begin{cases}
3x_1+x_2+x_3=2,\\
x_1+2x_2+2x_3=-1,\\
-x_1+2x_2+x_3=-5.
\end{cases}
\]""",
    "3.2 例 2": r"""判断增广矩阵
\[
\left(
\begin{array}{ccc|c}
1&-2&3&4\\
4&-2&-4&1\\
3&0&-7&5
\end{array}
\right)
\]
对应的线性方程组是否有解。""",
    "3.2 例 3": r"""求齐次线性方程组 \(Ax=0\) 的通解，其中
\[
A=\begin{pmatrix}
2&1&-1\\
1&-1&1\\
4&5&-5
\end{pmatrix}.
\]""",
    "3.2 例 4": r"""求非齐次线性方程组 \(Ax=b\) 的通解，其增广矩阵为
\[
\left(
\begin{array}{ccc|c}
2&1&-1&1\\
1&-1&1&2\\
4&5&-5&-1
\end{array}
\right).
\]""",
    "3.2 例 5": r"""求齐次线性方程组的通解，其系数矩阵为
\[
\begin{pmatrix}
1&3&5&1\\
2&3&4&2\\
1&2&3&1
\end{pmatrix}.
\]""",
    "3.2 例 6": r"""求非齐次线性方程组的通解，其增广矩阵为
\[
\left(
\begin{array}{cccc|c}
1&3&5&1&2\\
2&3&4&2&1\\
1&2&3&1&1
\end{array}
\right).
\]""",
    "3.3 例 1": r"""设齐次方程组的阶梯形系数矩阵为
\[
\begin{pmatrix}
1&-1&0&-2&5\\
0&0&1&3&0\\
0&0&0&0&1
\end{pmatrix}.
\]
判断题给四组选项中哪一组可以作为自由变量。""",
    "3.3 例 2": r"""设 \(A\) 为 \(m\times n\) 矩阵，\(B\) 为 \(n\times m\) 矩阵。若 \(m>n\)，判断齐次方程组 \((AB)x=0\) 的解的情况及正确选项。""",
    "3.3 例 3": r"""设非齐次线性方程组为 \(Ax=b\)，其中 \(A\) 为 \(m\times n\) 矩阵。判断关于 \(r(A)\) 与方程组解的四个命题中哪一个正确。""",
    "3.3 例 4": r"""设
\[
A=\begin{pmatrix}
1&1&1\\
1&2&a\\
1&4&a^2
\end{pmatrix}.
\]
若方程组 \(Ax=b\) 有无穷多解，判断参数 \(a,b\) 与集合 \(\Omega=\{1,2\}\) 的关系。""",
    "3.3 例 5": r"""设 \(Ax=0\) 是非齐次线性方程组 \(Ax=b\) 的导出组。判断关于导出组和非齐次方程组解的四个命题中哪一个正确。""",
    "3.3 例 6": r"""设线性方程组的系数矩阵为
\[
A=(a-b)E+bJ,
\]
其中 \(J\) 为 \(n\) 阶全 \(1\) 矩阵。讨论齐次方程组 \(Ax=0\) 的通解。""",
    "3.3 例 7": r"""设线性方程组的系数矩阵为
\[
A=\begin{pmatrix}
1&1&1&1\\
0&1&0&2\\
0&-1&a-3&-2\\
3&2&1&a
\end{pmatrix}.
\]
讨论方程组的解的情况，并在有无穷多解时写出通解。""",
}

M5 = {
    "5.1 例 6": r"""设 \(A\) 为 \(n\) 阶可逆矩阵，\(A\) 的每行元素之和均为 \(a\,(a\ne0)\)，且 \(|A|=1\)。求 \(A^*\) 的每行元素之和。""",
    "5.1 例 7": r"""设
\[
A=\begin{pmatrix}
a&-1&c\\
5&b&3\\
1-c&0&-a
\end{pmatrix},
\qquad |A|=-1.
\]
若 \(A\) 的伴随矩阵 \(A^*\) 有特征值 \(\lambda_0\)，且属于 \(\lambda_0\) 的特征向量为 \(\alpha=(-1,-1,1)^T\)，求 \(a,b,c\) 及 \(\lambda_0\)。""",
    "5.1 例 8": r"""设 \(A\) 为 \(n\) 阶实对称矩阵，\(P\) 为 \(n\) 阶可逆矩阵。已知 \(n\) 维列向量 \(\alpha\) 是矩阵 \(A\) 属于特征值 \(\lambda\) 的特征向量，判断矩阵 \((P^{-1}AP)^T\) 属于特征值 \(\lambda\) 的特征向量：
\[
\text{A. }P^{-1}\alpha\qquad
\text{B. }P^T\alpha\qquad
\text{C. }P\alpha\qquad
\text{D. }(P^{-1})^T\alpha.
\]""",
    "5.1 例 9": r"""若 \(\alpha_1\) 是矩阵 \(A\) 属于特征值 \(\lambda=1\) 的特征向量，\(\alpha_2,\alpha_3\) 是矩阵 \(A\) 属于特征值 \(\lambda=2\) 的两个线性无关特征向量。设
\[
AP=P\begin{pmatrix}
1&0&0\\
0&2&0\\
0&0&2
\end{pmatrix},
\]
判断矩阵 \(P\) 不可以是哪一个：
\[
\text{A. }(\alpha_1,-2\alpha_2,\alpha_3),\quad
\text{B. }(\alpha_1,\alpha_2+\alpha_3,\alpha_2-\alpha_3),
\]
\[
\text{C. }(\alpha_1,\alpha_3,\alpha_2),\quad
\text{D. }(\alpha_1+\alpha_2,\alpha_1-\alpha_2,\alpha_3).
\]""",
    "5.2 例 1": r"""设 \(\alpha=(1,2,3)^T\)，\(\beta=(1,\frac12,\frac13)^T\)，\(A=\alpha\beta^T\)。求 \(A^n\)。""",
    "5.2 例 2": r"""设 \(A=E+\alpha\beta^T\)，且 \(\alpha^T\beta=2\)。求 \(A^{-1}\)。""",
    "5.2 例 3": r"""设 \(\alpha\beta^T\) 为三阶矩阵，且 \(\alpha\beta^T\) 与
\[
\begin{pmatrix}2&0&0\\0&0&0\\0&0&0\end{pmatrix}
\]
相似。求 \(\beta^T\alpha\)。""",
    "5.2 例 4": r"""设
\[
A=\begin{pmatrix}2&1&3\\4&2&6\\6&3&9\end{pmatrix},
\qquad
B=A+E.
\]
求 \(A\) 与 \(B\) 的特征值和对应特征向量。""",
    "5.3 例 1": r"""已知矩阵
\[
A=\begin{pmatrix}-2&-2&1\\2&x&-2\\0&0&-2\end{pmatrix},
\qquad
B=\begin{pmatrix}2&1&0\\0&-1&0\\0&0&y\end{pmatrix}
\]
相似，求 \(x,y\)。""",
    "5.3 例 2": r"""设
\[
B=\begin{pmatrix}0&0&1\\0&1&0\\1&0&0\end{pmatrix},
\qquad A\sim B.
\]
求 \(r(A-2E)+r(A-E)\)。""",
    "5.3 例 3": r"""设 \(A=\alpha\alpha^T\)，其中 \(\alpha=(1,2,-1)^T\)，且 \(A\sim B\)。求 \(|(B+E)^*|\)。""",
}

M4 = {
    "4.1 例 2": r"""设
\[
\alpha=(a,0,\ldots,0,a)^T,
\qquad a<0,\qquad A=E-\alpha\alpha^T.
\]
若
\[
A^{-1}=E+a^{-1}\alpha\alpha^T,
\]
求 \(a\)。""",
    "4.1 例 3": r"""已知
\[
\alpha\beta^T=
\begin{pmatrix}
1&-1&2\\
-2&2&-4\\
3&-3&6
\end{pmatrix}.
\]
求 \(\alpha^T\beta\)。""",
    "4.3 例 1": r"""证明：单个非零向量线性无关；两个不成比例的向量线性无关。""",
    "4.3 例 4": r"""设 \(\alpha_1,\ldots,\alpha_s\) 线性无关，令
\[
\beta_1=\alpha_1,\quad
\beta_2=\alpha_1+\alpha_2,\quad
\ldots,\quad
\beta_s=\alpha_1+\cdots+\alpha_s.
\]
证明 \(\beta_1,\ldots,\beta_s\) 线性无关。""",
    "4.3 例 5": r"""设
\[
A\alpha_1=\alpha_1,\quad
A\alpha_2=\alpha_1+\alpha_2,\quad
A\alpha_3=\alpha_2+\alpha_3.
\]
证明 \(\alpha_1,\alpha_2,\alpha_3\) 线性无关。""",
    "4.3 例 6": r"""设 \(A^k\alpha=0\)，且 \(A^{k-1}\alpha\ne0\)。证明向量组
\[
\alpha,A\alpha,\ldots,A^{k-1}\alpha
\]
线性无关。""",
    "4.3 例 7": r"""设
\[
\alpha_1=(1,2,-1,5)^T,\quad
\alpha_2=(2,-1,1,1)^T.
\]
判断 \(\beta_1=(4,3,-1,11)^T\)、\(\beta_2=(4,3,0,11)^T\) 是否可由 \(\alpha_1,\alpha_2\) 线性表示；若可以，写出表示式。""",
    "4.3 例 8": r"""设向量组 \((I):\alpha_1,\alpha_2,\alpha_3\) 与 \((II):\beta_1,\beta_2,\beta_3\)，其中
\[
\alpha_1=\begin{pmatrix}0\\1\\2\\3\end{pmatrix},\quad
\alpha_2=\begin{pmatrix}3\\0\\1\\2\end{pmatrix},\quad
\alpha_3=\begin{pmatrix}2\\3\\0\\1\end{pmatrix}.
\]
判断 \((II)\) 是否可由 \((I)\) 线性表示。""",
    "4.3 例 9": r"""判断向量组线性相关与“某个向量可由其余向量线性表示”之间的等价关系，并选择正确选项。""",
    "4.3 例 10": r"""判断向量组线性无关与“任一向量都不能由其余向量线性表示”之间的等价关系，并选择正确选项。""",
    "4.3 例 12": r"""设 \(A=(\alpha_1,\alpha_2,\alpha_3,\alpha_4)\) 为 \(3\times4\) 矩阵，\(\beta_1,\beta_2,\beta_3\) 为其行向量。已知
\[
\begin{vmatrix}a_{12}&a_{14}\\a_{22}&a_{24}\end{vmatrix}\ne0.
\]
判断题给命题中哪些正确。""",
    "4.3 例 13": r"""设
\[
A=\begin{pmatrix}
1&1&\cdots&1\\
a_1&a_2&\cdots&a_s\\
\vdots&\vdots&&\vdots\\
a_1^{n-1}&a_2^{n-1}&\cdots&a_s^{n-1}
\end{pmatrix},
\qquad a_i\ne a_j\ (i\ne j).
\]
讨论列向量组 \(\alpha_1,\ldots,\alpha_s\) 的线性相关性。""",
    "4.3 例 14": r"""设 \(\alpha_1,\alpha_2,\alpha_3\) 线性相关，而 \(\alpha_2,\alpha_3,\alpha_4\) 线性无关。回答：\(\alpha_1\) 能否由 \(\alpha_2,\alpha_3\) 线性表示？\(\alpha_4\) 能否由 \(\alpha_1,\alpha_2,\alpha_3\) 线性表示？""",
    "4.3 例 15": r"""设向量组 \((I)\) 有 \(t\) 个向量，向量组 \((II)\) 有 \(s\) 个向量。判断关于“一个向量组可由另一个向量组线性表示”与线性相关性的四个命题中哪些正确。""",
    "4.4 例 1": r"""设向量组的秩为 \(r\)。判断关于任取 \(r+1\) 个向量的线性相关性的正确选项。""",
    "4.4 例 2": r"""设向量组 \(\alpha_1,\ldots,\alpha_s\) 的秩为 \(s-1\)。判断关于其子组秩和线性表示的四个命题中哪一个正确。""",
    "4.4 例 3": r"""设矩阵经初等行变换化为
\[
B=\begin{pmatrix}
1&2&2&1\\
0&1&2&2\\
0&0&0&1\\
0&0&0&0
\end{pmatrix}.
\]
判断原矩阵列向量组的极大无关组及线性表示关系，并选择不正确的选项。""",
    "4.4 例 4": r"""设五个向量 \(\alpha_1,\ldots,\alpha_5\) 的秩为 \(3\)。求一个包含 \(\alpha_1,\alpha_3\) 的极大线性无关组，并将其余向量由该组线性表示。""",
    "4.5 例 1": r"""已知向量组 \((I)\) 与 \((II)\) 均由三个三维向量组成，且
\[
\det(\alpha_1,\alpha_2,\alpha_3)=a+1,\qquad
\det(\beta_1,\beta_2,\beta_3)=6.
\]
判断两向量组何时等价。""",
    "4.5 例 2": r"""设
\[
k\alpha+l\beta+m\gamma=0,\qquad km\ne0.
\]
判断 \(\alpha,\beta,\gamma\) 之间的线性表示关系，并选择正确选项。""",
    "4.5 例 3": r"""设向量组 \((I)\) 有 \(k\) 个 \(n\) 维向量且线性无关。判断向量组 \((II)\) 线性无关与 \((I),(II)\) 等价之间的关系，并选择正确选项。""",
    "4.5 例 4": r"""设 \(AB=C\)，且 \(B\) 可逆。判断矩阵 \(A\) 与 \(C\) 的列向量组是否等价，并选择正确选项。""",
    "4.6 例 1": r"""求齐次线性方程组的基础解系和通解，其系数矩阵为
\[
\begin{pmatrix}
1&1&1&1&1\\
1&2&1&1&-1\\
1&3&1&1&-3\\
3&4&3&3&1
\end{pmatrix}.
\]""",
    "4.6 例 2": r"""设 \(\alpha_1,\alpha_2,\alpha_3\) 是齐次方程组的一个基础解系。判断题给四个向量组中哪一个仍是基础解系。""",
    "4.6 例 3": r"""设 \(A=(\alpha_1,\alpha_2,\alpha_3)\)，其中 \(\alpha_3=-\alpha_1+2\alpha_2\)，且 \(\alpha_1,\alpha_2\) 线性无关。求齐次方程组 \(Ax=0\) 的通解。""",
    "4.6 例 4": r"""设 \(r(B)=2\)，\(r(AB)=1\)。结合题给矩阵条件，求参数 \(a\) 及对应齐次方程组的通解。""",
    "4.6 例 5": r"""求非齐次线性方程组的通解，其增广矩阵为
\[
\left(
\begin{array}{cccc|c}
1&1&1&1&-1\\
4&3&5&-1&-1\\
2&1&3&-3&1
\end{array}
\right).
\]""",
    "4.6 例 6": r"""已知非齐次线性方程组有特解 \(x_0=(1,-1,1,-1)^T\)。求参数 \(\lambda,\mu\) 的关系及方程组通解。""",
    "4.6 例 7": r"""设
\[
A=\begin{pmatrix}a&1\\1&0\end{pmatrix},
\qquad
B=\begin{pmatrix}0&1\\1&b\end{pmatrix}.
\]
讨论矩阵方程 \(AC-CA=B\) 何时有解，并求通解 \(C\)。""",
    "4.6 例 8": r"""已知 \(\beta_1,\beta_2\) 是非齐次方程组 \(Ax=b\) 的两个不同解，\(\alpha_1,\alpha_2\) 是导出组 \(Ax=0\) 的基础解系。判断题给通解形式中哪一个正确。""",
    "4.6 例 9": r"""设三元非齐次线性方程组 \(Ax=\beta\) 有三个线性无关的解 \(\eta_1,\eta_2,\eta_3\)。判断其通解的正确表达式。""",
    "4.6 例 10": r"""已知 \(Ax=\beta\) 的通解为
\[
x=k(1,0,-3,2)^T+(1,-1,0,1)^T.
\]
令 \(B=(\alpha_2+\beta,\alpha_4,\alpha_3,\alpha_2,\alpha_1)\)，其中 \(A=(\alpha_1,\alpha_2,\alpha_3,\alpha_4)\)。求 \(Bx=\beta\) 的通解。""",
    "4.7 例 1": r"""设
\[
\alpha_1=(1,2,-1,0)^T,\quad
\alpha_2=(1,1,0,2)^T,\quad
\alpha_3=(2,1,1,a)^T.
\]
若 \(\alpha_1,\alpha_2,\alpha_3\) 张成空间维数为 \(2\)，求 \(a\)。""",
}


def main():
    for fname, mapping in [
        ("ch02_matrices.tex", M2),
        ("ch03_linear_systems_intro.tex", M3),
        ("ch04_vectors_systems.tex", M4),
        ("ch05_similarity.tex", M5),
    ]:
        changed = replace_question_by_label(BASE / fname, mapping)
        print(f"{fname}: {len(changed)} questions replaced")


if __name__ == "__main__":
    main()
