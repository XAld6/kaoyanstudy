# T3 审计报告：00_deliverables / 01_projects

- 日期：2026-08-05
- 执行：opencode（子 agent T3）
- 范围：`00_deliverables/`（根目录 zip 归位 + 各子目录结构）、`01_projects/`（10 个项目目录健康度 + NESTED_REPOS.md 一致性）
- 约束遵守情况：未删除任何文件；未执行任何 git 写操作（仅只读的 `git status`/`git ls-files`/`git check-ignore`/`git rev-parse`）；未改动嵌套仓库内部（CodexCont、chatgpt-register-k12、dachaung/sidecars/skill、90_temp_work/grok-build-zh-20260801）。

---

## 1. 00_deliverables — 审计与已执行动作

### 1.1 根目录 zip 归位 ✅（已执行移动）

- **现状**：`00_deliverables/` 根部存在 `grok-register-panel.zip`（523,241 B，2026-08-01 20:01），未归入任何子目录，违反「交付 ZIP 归入子目录」规范。
- **冲突检查**：`00_deliverables/grok-register-panel/` 不存在 → 无冲突。该 zip 被 `.gitignore` 的 `*.zip`（行 83）忽略，移动不产生 git 跟踪变化。
- **执行动作**：新建 `00_deliverables/grok-register-panel/`，将 zip 移入为 `00_deliverables/grok-register-panel/grok-register-panel.zip`。
- **验证**：移动后 `00_deliverables/` 根部无散落文件；`git status` 对 00_deliverables 无任何输出（未引入 git 变更）。

### 1.2 子目录结构审计

| 子目录 | 现状 | 对照 WORKSPACE_ORGANIZATION.md | 结论 |
|---|---|---|---|
| `leleche/` | `current/`（5 个快照）+ `archive/`（r01–r07 共 7 个快照）+ `MANIFEST.md` | 「current/ 当前版 + archive/ 历史快照」 | ⚠️ 结构符合，但 MANIFEST 快照表仅列 r01–r08，`current/` 实际含 r09–r12 共 5 个快照未登记（见 1.3） |
| `resumes/` | `postgraduate_reexam_resume/` + `resume_competition_intern/` | 文档列两个简历子目录 | ✅ 完全一致 |
| `linear_algebra_solutions/` | 单个 `第一章_行列式_详细解析.md` | 「线性代数解答集」 | ✅ 一致（内容较单一，无异常） |
| `mz_linear_solution/` | 单个 Overleaf 包 ZIP | 「线代解题 Overleaf 包 ZIP」 | ✅ 一致 |
| `rc_sampling_solutions/` | 单个 Overleaf 包 ZIP | 「RC sampling 解答 Overleaf 包 ZIP」 | ✅ 一致 |

### 1.3 发现：leleche/MANIFEST.md 与 current/ 内容不同步

- `current/` 实际包含 r08–r12 共 5 个快照（`2026-07-07_r08_ch09_science_v10`、`2026-07-22_r09_midas_frame_analysis`、`2026-07-22_r10_numerical_simulation_step`、`2026-07-22_r11_midas_wheel_analysis`、`2026-07-23_r12_calculation_audit_revision`）。
- `MANIFEST.md` 快照表仅登记至 r08，未登记 r09–r12；「当前交付」仍指向 r08。
- **建议**：将 r09–r12 补入 MANIFEST 快照表（或按交付规则将旧版 r09/r10/r11 移入 `archive/`，仅保留 r12 为 `current/`，需单独确认，本次未动）。另注：current 各快照根目录平铺 `contact_1/2/3.jpg`（与 T2 报告在 `90_temp_work/leleche/active/` 发现的问题同型），可考虑随下次整理归入各快照 `images/`。

---

## 2. 01_projects — 逐项目健康度审计

| 项目 | README | 嵌套 .git | 散落垃圾 | 与文档一致 | 结论 |
|---|---|---|---|---|---|
| `chatgpt-register-k12/` | ✅ README.md | ✅（.git 存在，嵌套仓库） | 无 | ✅ | 健康，未改动 |
| `CodexCont/` | ✅ README.md + README_zh.md | ✅（.git 存在，嵌套仓库） | `gptpoc.egg-info/`（打包元数据） | ✅ | 健康，未改动 |
| `dachaung/` | ✅ README.md | 根无 .git；`sidecars/skill/` 为嵌套仓库 | 根目录 `.codex_tmp/`（ppt_extract/pytest-basetemp/pytest-cache，已被 `**/.codex_tmp/` 忽略）；`sidecars/` 根另有 `结构设计成绩自动计算*.html`（README 自述为旁支杂项） | ✅ | 健康，未改动嵌套仓库 |
| `grok-register-panel/` | ✅ README.md | **无 .git**（见 2.1） | `__pycache__/`、`log/`、`.venv/`（均被忽略） | ✅ | 健康，未改动 |
| `jglx_latex_project/` | ❌ 根无 README | 无 | 根目录含构建脚本 + 多组 Overleaf zip 与同名展开目录（`jglx_final_overleaf/` 与 `.zip` 并存等）；`_archive/` 内为历史包 | ⚠️ | 缺 README；同名 zip/目录并存可考虑归档（见 2.3） |
| `kaoyan-study-console/` | ✅ README.md | 无 | `.runtime/`（忽略）、`.superpowers/`（跟踪中，brainstorm 内容） | ✅ | 健康 |
| `mz_linear_solution_project/` | ✅ README.md | 无 | 根目录残留编译产物 `main.aux/log/out/toc`（已忽略）；多个审计 .txt（`block_summaries_2_4.txt` 等，已跟踪） | ✅ | 健康；编译产物可后续清理 |
| `steel_structure_thesis/` | ❌ 根无 README | 无 | 根目录多版本 PDF/zip/tex 平铺；`最终上传版/`、`final_overleaf_upload/`、`paper_overleaf/` 三套目录并存；`steel_structure_final_overleaf_upload__1_.pdf` 与 `...__1_ (1).pdf` 相似但哈希不同（非重复） | ⚠️ | 缺 README；目录/文件冗余（见 2.3） |
| `xm1/` | ✅ README.md | 无 | 无 | ✅ | 健康 |
| `zy_latex_work/` | ❌ 根无 README | 无 | `__pycache__/`（忽略）、根目录 `.aux/.log/.toc`（已忽略） | ⚠️ | 缺 README；编译产物可后续清理 |

### 2.1 关键事实澄清：grok-register-panel **不是**嵌套独立 git 仓库

- 任务描述称「CodexCont、chatgpt-register-k12、grok-register-panel 是嵌套独立 git 仓库」。实测：`git -C .../grok-register-panel rev-parse --show-toplevel` 返回 `D:/xm`（即父仓），且该目录**无 `.git/`**。
- `NESTED_REPOS.md` 仅列 `CodexCont/`、`chatgpt-register-k12/`、`dachaung/sidecars/skill/`、`90_temp_work/grok-build-zh-20260801/`——**未列** grok-register-panel，与实测一致，NESTED_REPOS.md 表述正确。
- `grok-register-panel/` 是「被父仓 .gitignore:112 忽略的普通项目目录」（git ls-files 计数为 0，与 T4 报告 P3 结论一致）。无论如何，本次未改动其内部。

### 2.2 NESTED_REPOS.md 一致性

- 文档列出的 4 个嵌套仓库全部实测存在 `.git/`：`01_projects/CodexCont/`、`01_projects/chatgpt-register-k12/`、`01_projects/dachaung/sidecars/skill/`、`90_temp_work/grok-build-zh-20260801/` ✅
- WORKSPACE_ORGANIZATION.md:93 嵌套仓库清单与此一致 ✅
- 结论：NESTED_REPOS.md 与现状一致，无需改动。

### 2.3 建议（均未执行，等待确认）

1. **jglx_latex_project/**：根目录补 `README.md`；同名 Overleaf zip 与展开目录可考虑统一为「保留 zip、展开目录移入 `_archive/`」（涉及被跟踪文件移动，需确认后随 git add 处理）。
2. **steel_structure_thesis/**：根目录补 `README.md`；`最终上传版/`、`final_overleaf_upload/`、`paper_overleaf/` 三套目录建议在 README 中明确各自用途（当前无说明），多版本根文件按 `final_overleaf_upload/` 内 `overleaf_readme.md` 判定后决定归档去向。
3. **mz_linear_solution_project/ 与 zy_latex_work/**：根目录 `.aux/.log/.toc` 编译产物为已忽略垃圾，可在确认后删除或移出（属删除类，本次未动）。
4. **leleche/MANIFEST.md**：补登 r09–r12（见 1.3）。
5. **dachaung/sidecars/**：`结构设计成绩自动计算*.html` 属旁支杂项且已随父仓跟踪，README 已自述 sidecars 为旁支，可保留；`.codex_tmp/` 已被忽略，无需处理。

---

## 3. 合规性确认

- 唯一已执行动作：创建 `00_deliverables/grok-register-panel/` 并移入 zip（任务明确授权、无冲突、不影响 git 跟踪）。
- 未删除任何文件 ✓
- 未执行任何 git 写操作 ✓
- 未改动嵌套仓库内部（CodexCont、chatgpt-register-k12、dachaung/sidecars/skill、90_temp_work/grok-build-zh-20260801）✓
- 未读取或改动 `90_temp_work/_private` ✓
