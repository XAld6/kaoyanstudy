# D:\xm 工作区整理说明

本工作区已按“交付文件 / 项目工程 / 学习资料 / 临时产物”重新分类。整理过程只移动文件，不删除内容。

最近整理：2026-06-18。根目录散落的临时检查脚本、提取脚本和临时文本已归档到 `90_temp_work/root_loose_20260618/`；原根目录 `tmp/` 已归档到 `90_temp_work/tmp_20260618/`；根目录残留的 `zy/sg/cy/` 学习资料已并入 `02_study_materials/zy/sg/cy/`。

## 当前根目录

| 目录 | 用途 |
|---|---|
| `00_deliverables/` | 最终交付文件、可上传压缩包 |
| `01_projects/` | 代码项目、LaTeX 工程、独立项目目录 |
| `02_study_materials/` | 学习资料、原始课程/题本资料 |
| `90_temp_work/` | 临时预览、OCR/检查、解压验证、打包 staging |

隐藏目录 `.git/`、`.claude/`、`.codex-playwright/` 仍留在根目录，用于工作区配置或工具缓存，不建议手动移动。

## 重要文件位置

| 内容 | 新位置 |
|---|---|
| 线性代数解析 Overleaf 上传包 | `D:\xm\00_deliverables\mz_linear_solution_project_overleaf.zip` |
| 线性代数解析 LaTeX 工程 | `D:\xm\01_projects\mz_linear_solution_project\` |
| 线性代数打包 staging / zip 验证目录 | `D:\xm\90_temp_work\` |
| 原 `zy` 学习资料目录 | `D:\xm\02_study_materials\zy\` |
| 2026-06-18 根目录临时脚本归档 | `D:\xm\90_temp_work\root_loose_20260618\` |
| 2026-06-18 根目录 tmp 归档 | `D:\xm\90_temp_work\tmp_20260618\` |
| 桥梁/施工课程新增资料 | `D:\xm\02_study_materials\zy\sg\cy\` |

## 项目工程

以下目录已归入 `01_projects/`：

- `cc1/`
- `dachaung/`
- `kaoyan-study-console/`
- `lyl660_latex/`
- `mz_linear_solution_project/`
- `overleaf_rc_sampling_solutions/`
- `xm1/`

## 维护建议

- 新完成的 zip、pdf、可上传包放到 `00_deliverables/`。
- 新的源码工程放到 `01_projects/`。
- 原始资料、课程文件、题本放到 `02_study_materials/`。
- OCR、预览图、编译缓存、解压验证目录放到 `90_temp_work/`。
- 不确定用途的文件先放 `90_temp_work/`，确认后再归档。
- `node_modules/`、`marker312/`、`__pycache__/`、LaTeX 中间产物和批量渲染/OCR 目录已写入工作区 `.gitignore`，日常搜索和版本管理时建议继续排除这些目录。
- 当前 `.git/` 目录缺少 `HEAD` 和 `config`，Git 不会把本目录识别为有效仓库；如果后续要版本管理，需要重新初始化或修复仓库元数据。
