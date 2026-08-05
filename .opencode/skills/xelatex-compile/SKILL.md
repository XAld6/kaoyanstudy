---
name: xelatex-compile
description: Use ONLY when the user asks to compile/构建/生成 LaTeX/PDF, 处理 tex 文件, runs xelatex, or mentions 编译latex/编译tex. Triggers on keywords like "编译", "生成PDF", "build latex", "xelatex", "跑latex", "latex编译", "构建latex", "生成tex", "跑tex". Covers the full pipeline: Python build scripts → xelatex compile → PDF output.
---

# XeLaTeX 编译技能

## xelatex 位置

```
C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe
```

MiKTeX 26.5，系统已安装，可直接在 PATH 中调用 `xelatex`。

## 通用编译命令（推荐做法）

```powershell
# 在 .tex 所在目录执行，两遍编译并保存日志（pass1/pass2）
cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex > compile_pass1.txt 2>&1"
cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex > compile_pass2.txt 2>&1"
```

- `-interaction=nonstopmode`：遇错不停止交互
- `-halt-on-error`：遇真正错误才停止
- `-file-line-error`：错误信息附带文件名和行号
- **必须两遍编译**（pass1 + pass2），第二遍解决交叉引用、目录（TOC）、页码
- 工作目录必须是 `.tex` 文件所在目录
- **保存编译日志**（`compile_pass1.txt` / `compile_pass2.txt`）是本工作区的既有习惯，便于后续排查
- **不要用 PowerShell 的 `2>&1 | Out-File`**：会产生 NativeCommandError 噪音记录且中文可能乱码；`chcp 65001 & cmd /c ... > log 2>&1` 是实测最干净的写法（中文文件名正常、日志纯净）
- 若脚本或文档内部已自行调用 xelatex（如 jglx 的 build_final_overleaf.py），则无需手动编译

## 决策速查：用户说"编译X"时先定位项目

| 用户提到的关键词 | 项目类型 | 操作 |
|---|---|---|
| sg / 施工 / 章节测验 / 刷题版 / 解析版 | 类型 1 | 先跑对应 build 脚本 → 进输出目录编译 |
| jglx / 结构力学 / 结构计算 | 类型 3 | 直接 `python build_final_overleaf.py`，自动编译 |
| ky / sx / 考研数学 / 线性代数题解 | 类型 4 或类型 2 | 重建类先跑脚本；`mz_linear_solution_project` 直接编译 main.tex |
| 钢结构 / 论文 / steel | 类型 2 | 直接编译对应目录 main.tex |
| gcjjx / 工程经济 / 桥梁 / bridge | 类型 2 | 直接编译 main.tex / bridge_review_*.tex |

找不到匹配时：在工作区 glob `**/*.tex` 找 main.tex，用 类型 2 流程。

## LaTeX 项目类型及编译流程

### 类型 1：SG 学习资料项目（Python 构建脚本生成 .tex）

目录结构：`02_study_materials\zy\sg\`

流程：
1. **先跑 Python 构建脚本**生成 `.tex` 文件（在 `03_生成脚本\` 中），运行方式：
   `python D:\xm\02_study_materials\zy\sg\03_生成脚本\build_xxx.py`

   脚本与输出目录对应关系：
   | 脚本 | 输出目录（`02_LaTeX工程\`下） | 产物 |
   |---|---|---|
   | `build_study_guide.py` | `latex_out\` | 01 无答案 / 01B 乱序 / 02 解析 / 03 PPT提要 / 04 综合版 |
   | `build_practice_no_solution.py` | `practice_no_solution_overleaf\` | 无解析刷题版 |
   | `build_practice_exam_style.py` | `practice_no_solution_exam_style\` | 无解析刷题版（试卷风格） |
   | `build_practice_answer_key_exam_style.py` | `practice_answer_key_exam_style\` | 答案版（试卷风格） |
   | `build_practice_inline_answer_exam_style.py` | `practice_inline_answer_exam_style\` | 答案跟题版 |
   | `build_review_answer_analysis.py` | `practice_review_answer_with_analysis\` | 复习解析版 |
   | `build_review_selected_inline_answer.py` | `practice_review_selected_inline_answer\` | 精选答案跟题版 |

2. **xelatex 编译** `.tex` → PDF（在输出目录内执行两遍）：
   ```powershell
   cd D:\xm\02_study_materials\zy\sg\02_LaTeX工程\<输出目录>
   cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex > compile_pass1.txt 2>&1"
   cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex > compile_pass2.txt 2>&1"
   ```
   PDF 输出在同目录。

3. **目录中的常见 .tex 文件**（在 `02_LaTeX工程\` 各输出目录内）：
   - `latex_out\01_章节测验_无答案版.tex` 等5个版本
   - `practice_no_solution_overleaf\main.tex`、`practice_*\main.tex`
   - `overleaf_project\main.tex`

### 类型 2：独立 LaTeX 项目（直接编译 main.tex）

目录如：
- `01_projects\mz_linear_solution_project\`（线性代数题解，含 chapters\）
- `01_projects\steel_structure_thesis\`（钢结构论文，paper_overleaf\、final_overleaf_upload\ 各含 main.tex）
- `01_projects\zy_latex_work\`（桥梁复习，bridge_review_*.tex）
- `02_study_materials\zy\gcjjx\`（工程经济学，main.tex + overleaf_images\）

流程：
```powershell
cd <项目目录>
cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex > compile_pass1.txt 2>&1"
cmd /c "chcp 65001 >nul & xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex > compile_pass2.txt 2>&1"
```

### 类型 3：构建脚本内置编译（无需手动跑 xelatex）

- `01_projects\jglx_latex_project\build_final_overleaf.py`：内部自动执行
  `subprocess.run(["xelatex", "-interaction=nonstopmode", "main.tex"], cwd=jglx_final_overleaf)`
  即运行 `python build_final_overleaf.py` 后自动编译，只需检查输出 PDF 是否生成。
- 判断方法：构建脚本含 `subprocess.run(["xelatex", ...])` 即为内置编译。

### 类型 4：PDF 重建项目（Python 从源 PDF 提取内容生成 .tex）

目录如：`02_study_materials\zy\ky\sx\`（考研数学，基于 PDF 题解重建）

| 脚本 | 输出目录 | 说明 |
|---|---|---|
| `build_overleaf_project.py` | `overleaf_solution_project\` | 从源 PDF 提取生成 main.tex + chapters\ + figures\ |
| `ep\build_ep_solution_project.py` | `ep\ep_solution_project\` | 同上（EP 卷） |

流程：先跑脚本，再进入生成目录按类型 2 编译 main.tex。
注意：此类项目常需联网下载图片或引用 PDF 内嵌图，首次构建较慢；脚本可能依赖 fitz（PyMuPDF）等库。

## 编译成功判定

每遍编译输出末尾应有 "Output written on <xxx>.pdf"；确认 PDF 已更新：
```powershell
Get-Item <文件名>.pdf | Select-Object LastWriteTime, Length
```
- 两遍都出现 "Output written"，且 PDF 的 LastWriteTime 是最近时间，即成功
- pass2 末尾若提示 "Rerun to get cross-references right"，需再跑一遍直到提示消失
- 若脚本内置编译（类型 3），检查其输出 PDF 存在且时间戳最新即可

## 编译错误排查

1. 编译失败时，先看 `compile_pass2.txt`（或 `.log`）：
   ```powershell
   Select-String -Path compile_pass2.txt -Pattern "^!" | Select-Object -First 10
   ```
   `.log` 中以 `!` 开头的行是真正的 LaTeX 错误；若 log 里没有 `!` 行，通常是引用/字体/图片的警告。
2. 常见错误：
   - **Undefined control sequence**：命令拼写错或宏包未加载
   - **File not found (.png/.jpg)**：图片路径与编译工作目录不一致，检查 `images\` 相对路径
   - **Missing } inserted / Runaway argument**：大括号不配对，用 `-file-line-error` 提示定位到行
   - **Font 缺失**：见下方字体问题
3. 修改后重新编译仍报同样错误时，先删除 `.aux`/`.toc` 等缓存文件再重试。

## 编译后清理

编译产生辅助文件（`.aux`, `.log`, `.out`, `.toc` 等），一般保留以便下次增量编译更快。如需清理：
```powershell
Remove-Item *.aux, *.log, *.out, *.toc -Force -ErrorAction SilentlyContinue
```

## 常见问题

- **字体问题**：SG 项目用 `fontset=fandol`（内置于 MiKTeX）或 `fontset=windows`（依赖系统字体）
  - 若 `fontset=windows` 报字体缺失，改用 `fontset=fandol`
  - Overleaf 版本用 `fontset=fandol`
- **图片路径**：`.tex` 中 `images/` 目录需相对于编译工作目录存在
- **MiKTeX 更新提示**：编译日志末尾常见 "So far, you have not checked for MiKTeX updates"，不影响编译结果，可忽略
- **安全警告**：以管理员权限运行 xelatex 会有 "security risk: running with elevated privileges" 警告，可忽略
