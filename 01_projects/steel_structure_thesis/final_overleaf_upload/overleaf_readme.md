# Overleaf 使用说明

1. 将 `steel_structure_paper.tex` 上传到 Overleaf 项目根目录。
2. 将整个 `figures/` 文件夹上传到 Overleaf 项目根目录。
3. Overleaf 编译器选择 `XeLaTeX`。
4. 主文件选择 `steel_structure_paper.tex`。
5. 作者、班级、学号已填写为：顾诗渝，土木工程23101班，2340001087。主文件请优先使用 main.tex。

补充说明：

- `figures_insert_snippets.tex` 是独立图件插入片段，论文正文已经插入全部 15 张图，一般不需要再手动插入。
- `figures/` 中同时提供 PNG 和 SVG；论文默认引用 PNG，便于 Overleaf 直接编译。
- 若需要修改图片内容，可调整 `generate_steel_figures.py` 后重新运行生成。

