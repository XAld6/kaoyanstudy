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

## 通用编译命令

```powershell
xelatex -interaction=nonstopmode -halt-on-error -file-line-error <主tex文件名>
```

- `-interaction=nonstopmode`：遇错不停止交互
- `-halt-on-error`：遇真正错误才停止
- `-file-line-error`：错误信息附带文件名和行号
- **必须两遍编译**（pass1 + pass2），以解决交叉引用、目录（TOC）、页码等问题
- 工作目录必须是 `.tex` 文件所在目录

## LaTeX 项目类型及编译流程

### 类型 1：SG 学习资料项目（含 Python 构建脚本）

目录结构：`02_study_materials\zy\sg\`

流程：
1. **先跑 Python 构建脚本**生成 `.tex` 文件（在 `03_生成脚本\` 中）：
   - `build_study_guide.py` — 生成5个标准版本（无答案/乱序/解析/PPT/综合）
   - `build_practice_no_solution.py` — 生成刷题版（无答案无解析）
   - `build_practice_exam_style.py` — 生成试卷风格版
   - `build_practice_answer_key_exam_style.py` — 生成答案版
   - `build_practice_inline_answer_exam_style.py` — 生成答案跟题版
   - `build_review_answer_analysis.py` — 生成复习解析版
   - `build_review_selected_inline_answer.py` — 生成精选答案跟题版
   - 运行方式：`cd D:\xm\02_study_materials\zy\sg\03_生成脚本 ; python build_xxx.py`
   - 脚本输出 `.tex` 到 `D:\xm\02_study_materials\zy\sg\02_LaTeX工程\latex_out\`

2. **xelatex 编译** `.tex` → PDF：
   ```powershell
   cd D:\xm\02_study_materials\zy\sg\02_LaTeX工程\latex_out
   xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex
   xelatex -interaction=nonstopmode -halt-on-error -file-line-error <文件名>.tex
   ```
   - 两次编译，第二次解决目录和交叉引用
   - PDF 输出在同目录

3. **SG 项目的所有 .tex 文件**在 `02_LaTeX工程\latex_out\`：
   - `01_章节测验_无答案版.tex`
   - `01B_章节测验_乱序无答案版.tex`
   - `02_章节测验_解析版.tex`
   - `03_PPT重点提要.tex`
   - `04_PPT与章节测验综合版.tex`
   - `main.tex`（overleaf_project 中）

### 类型 2：独立 LaTeX 项目（直接编译 main.tex）

目录结构如：`01_projects\mz_linear_solution_project\`、`01_projects\steel_structure_thesis\`、`latex_review\`

流程：
```powershell
cd <项目目录>
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

两次编译，第二次解决交叉引用和目录。

## 编译后清理

编译产生辅助文件（`.aux`, `.log`, `.out`, `.toc` 等），一般保留以便下次增量编译更快。如需清理：
```powershell
Remove-Item *.aux, *.log, *.out, *.toc -Force -ErrorAction SilentlyContinue
```

## 常见问题

- **字体问题**：SG 项目用 `fontset=fandol`（内置于 MiKTeX）或 `fontset=windows`（依赖系统字体）
  - 若`fontset=windows`报字体缺失，改用 `fontset=fandol`
  - Overleaf 版本用 `fontset=fandol`
- **图片路径**：`.tex` 中 `images/` 目录需相对于编译工作目录存在
- **MiKTeX 更新提示**：编译日志末尾常见 "So far, you have not checked for MiKTeX updates"，不影响编译结果，可忽略
- **安全警告**：以管理员权限运行 xelatex 会有 "security risk: running with elevated privileges" 警告，可忽略