# D:\xm 工作区组织说明

本工作区按四个根分类目录组织，整理遵循「归档优先、只移动不删除」的原则。

| 目录 | 用途 |
|---|---|
| `00_deliverables/` | 可交付成果：最终 PDF、源码 ZIP、版本快照、简历等 |
| `01_projects/` | 独立项目与可持续维护的源码工程 |
| `02_study_materials/` | 课程、题本、原始学习资料及其分类归档 |
| `90_temp_work/` | 临时工作包、编译中间物、OCR、审计与杂项下载 |

根目录仅保留：`.gitignore`、`WORKSPACE_ORGANIZATION.md`，以及工具配置目录（`.git/`、`.opencode/`、`.claude/` 等）。

---

## 00_deliverables — 交付成果

| 路径 | 内容 |
|---|---|
| `leleche/` | 勒勒车竞赛方案：`current/` 当前版 + `archive/` 历史快照；见 `leleche/MANIFEST.md` |
| `resumes/postgraduate_reexam_resume/` | 考研复试个人简历 |
| `resumes/resume_competition_intern/` | 竞赛导向通用实习简历 |
| `linear_algebra_solutions/` | 线性代数解答集 |
| `mz_linear_solution/` | 线代解题 Overleaf 包 ZIP |
| `rc_sampling_solutions/` | RC sampling 解答 Overleaf 包 ZIP |

### 勒勒车关键位置

- 当前交付：`00_deliverables/leleche/current/2026-07-07_r08_ch09_science_v10/`
- 历史快照：`00_deliverables/leleche/archive/`（r01–r07）
- 工作源码：`90_temp_work/leleche/active/`
- 历史工作包：`90_temp_work/leleche/snapshots/`

---

## 01_projects — 工程源码

| 项目 | 说明 |
|---|---|
| `chatgpt-register-k12/` | ChatGPT 注册/登录 K12 流水线（CLI + WebUI） |
| `CodexCont/` | Codex 中间件 / 代理 |
| `dachaung/` | 大创「智爪识损」：`openclaw-damage-system/` 原型、`submission/` 申报、`presentation/` PPT、`sidecars/` 旁支；见 `dachaung/README.md` |
| `grok-register-panel/` | Grok 注册自动化与实时监控面板源码 |
| `jglx_latex_project/` | 结构力学 LaTeX 题本（含 Overleaf 上传包） |
| `kaoyan-study-console/` | 考研学习控制台（前后端） |
| `mz_linear_solution_project/` | 线性代数解题 LaTeX 工程 |
| `steel_structure_thesis/` | 钢结构论文 Overleaf |
| `xm1/` | 墙体缺陷检测（YOLO 相关） |
| `zy_latex_work/` | 桥梁复习等 LaTeX 工程 |

---

## 02_study_materials — 学习资料

| 路径 | 内容 |
|---|---|
| `zy/gcjjx/` | 工程经济学相关 |
| `zy/jglx/` | 结构力学作业与笔记 PDF |
| `zy/ky/` | 考研资料（高数/线代 EP、武忠祥等）；`ky/sx/lyl660/` 为线代源 PDF |
| `zy/sg/` | 施工课程：源文件、成品、LaTeX 工程、脚本 |

---

## 90_temp_work — 临时工作

| 路径 | 内容 |
|---|---|
| `leleche/active/` | 勒勒车当前 LaTeX 工作包 |
| `leleche/snapshots/` | 勒勒车历史 LaTeX 工作包 |
| `jglx/cache_20260619/` | 结构力学 OCR/预览/审计缓存 |
| `zy_latex_work/cache_20260619/` | 桥梁 LaTeX 渲染缓存 |
| `lyl660_ocr_20260609/` | 线代书 OCR/检查产物 |
| `latex_review_20260705/` | 一次性审阅包与脚本 |
| `misc_downloads/` | 从学习资料中移出的安装包、种子、第三方源码（含 `nucleo-5b74652e-src/`）等杂项 |
| `grok/` | hermes/grok 网关相关一次性脚本与日志（`fix_hermes_auth.py`、`start_hermes_gateway.ps1` 等） |
| `nat-exhibition/` | 全国展览一次性页面（index.html + server.pl） |
| `transcript_ocr/` | 成绩单 OCR 产物 |
| `tmp/` | r12 渲染中间物（已被 gitignore） |
| `skills-audit-report.md` | Codex skills 审计报告（2026-06-20） |
| `_private/` | 本地凭据备份、SSH 辅助文件与机器专属配置；仅本机保留，不提交 |
| `README.md` | 本目录补充说明 |

---

## 规则

- **交付**：每项保留一个 `current/`；替换前将旧版整体移入 `archive/`，命名含日期、修订号与阶段。
- **快照**：保留 PDF、源码 ZIP 及必要展开源码；不改内部原始文件名。
- **资料**：归入 `02_study_materials/` 对应主题；不与源码或交付混放。
- **临时物**：编译缓存、OCR、预览、一次性审阅 → `90_temp_work/`。**清理前须单独确认。**
- **工程 vs 交付**：可维护源码在 `01_projects/`；完成交付副本在 `00_deliverables/`。
- **工具目录**：`.git/`、`.opencode/`、`.claude/`、`.codex-playwright/` 等保持原位，不作日常归档。
- **嵌套仓库**：`CodexCont/`、`chatgpt-register-k12/`、`dachaung/sidecars/skill/`、`90_temp_work/grok-build-zh-20260801/` 为独立 git 仓库；父仓不跟踪其内容，见 `01_projects/NESTED_REPOS.md`。整理时勿动其内部状态。

## 整理记录

- 2026-07-06：初次按四类目录归档（见 commit `249b27b` 相关说明）。
- 2026-07-11：收尾整理——交付 ZIP/简历归入子目录；安装包等移至 `90_temp_work/misc_downloads/`；审计报告迁入 `90_temp_work/`；更新本说明。未删除任何缓存或 OCR 产物。
- 2026-08-04：`grok-register-panel/` 迁入 `01_projects/`（父仓忽略，敏感 config 不入库）；`docs/` 的 superpowers 计划/规格并入 `.superpowers/brainstorm/blog-20260731/`；nucleo 源码归入 `misc_downloads/`；hermes 网关脚本归入 `90_temp_work/grok/`；`coding-workspace/` 为 coding-tools-mcp 运行目录，保留。
- 2026-08-05：四 agent 并行审计整理——含明文凭据的根目录 SSH 脚本移入 `90_temp_work/_private/ssh_helpers/`（不入库）；`00_deliverables/grok-register-panel.zip` 归入 `00_deliverables/grok-register-panel/`；`leleche/active/` 根目录 `contact_*.jpg` 移入 `images/`；`leleche/MANIFEST.md` 补登 r09–r12、当前交付指向 r12；`.gitignore` 清理 3 条过期条目、修正 grok-register-panel 注释、新增 `.hermes/` 忽略；审计报告存于 `90_temp_work/cleanup_report_t1..t4.md`（详见各报告与 commit 说明）。未删除任何文件；`grok-build-zh-20260801/target/`（约 1.4 GB 构建缓存）、`tmp/pdfs/` 线性代数 OCR 块等清理类建议待单独确认。
