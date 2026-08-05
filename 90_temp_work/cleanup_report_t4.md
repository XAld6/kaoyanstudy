# T4 审计报告：02_study_materials / coding-workspace / 根目录杂项与 .gitignore

- 日期：2026-08-05
- 执行：opencode（子 agent T4）
- 范围：`02_study_materials/`（zy 下 gcjjx/jglx/ky/sg 结构完整性）、`coding-workspace/`（空目录是否仍需要）、`D:\xm` 根目录杂项（.gitignore 与 WORKSPACE_ORGANIZATION.md 一致性、应忽略未忽略文件、git status）
- 约束遵守情况：未删除任何文件；未执行任何 git 写操作（仅 `git status`/`git ls-files`/`git check-ignore`/`git log` 等只读命令）；未改动 `90_temp_work/_private`。

---

## 1. 02_study_materials — 结构完整性

### 1.1 结论：结构完整，与 WORKSPACE_ORGANIZATION.md 描述一致

`02_study_materials/zy/` 下 gcjjx / jglx / ky / sg 四个子目录均存在，且内容与 WORKSPACE_ORGANIZATION.md「02_study_materials — 学习资料」一节所列完全对应：

| 路径 | 文档描述 | 实际内容 | 状态 |
|---|---|---|---|
| `zy/gcjjx/` | 工程经济学相关 | 第二~六章章节测试 .md、main.tex/main.pdf、overleaf_images/、overleaf_revival_package.zip | ✓ |
| `zy/jglx/` | 结构力学作业与笔记 PDF | `6.作业&答案/`（第1~17次作业，37 个 PDF）、`7.作业讲解笔记/`（第1~14次笔记，22 个 PDF） | ✓ |
| `zy/ky/` | 考研资料（高数/线代 EP、武忠祥等）；`ky/sx/lyl660/` 为线代源 PDF | `ky/sx/`：ep/（高数+线代 EP 工程、OCR、overleaf 包）、`lyl660/source.pdf`、`overleaf_solution_project/`、`【A4留白版】武忠祥高数强化严选题数一做题本.pdf`、dist/、compiled_preview/、preview_pages/ | ✓ |
| `zy/sg/` | 施工课程：源文件、成品、LaTeX 工程、脚本 | `00_源文件/`（cy/、ppt/）、`01_最终成品/`（PDF/、Overleaf压缩包/）、`02_LaTeX工程/`、`03_生成脚本/`、`99_缓存与旧版/`、`cy/`、README_目录说明.txt | ✓ |

- `zy/ky/sx/lyl660/source.pdf` 存在（线代源 PDF，文档特别标注项）✓
- sg 顶层 `cy/`（10 个文件，桥梁课程材料）与 `00_源文件/cy/`（14 个文件，章节测试+3 PDF）**内容不重叠**，非重复归档 ✓

### 1.2 观察项（非缺失，仅记录）

1. **jglx 目录命名**：仅存在 `6.作业&答案`、`7.作业讲解笔记` 两个编号目录（无 1~5），编号按内容类别而非章次，内容实际覆盖第 1~17 次作业，无缺失，但命名可能引起「缺 1~5」的误读。
2. **gcjjx 内残留 LaTeX 编译产物**：`main.aux/.log/.out/.toc` 留在目录内（已被 .gitignore 忽略，不影响仓库），按「临时物 → 90_temp_work」规则可考虑后续移出（需单独确认）。
3. **ky/sx/ep 内嵌大量 OCR/渲染中间物**：`ep/ocr/`、`ep/xxx_project/tmp/`、`zip_verify/`、`preview_check/`、`preview_exact/`、`overleaf_staging/` 等属于「编译缓存、OCR、预览」类临时物，按 WORKSPACE_ORGANIZATION.md「临时物 → 90_temp_work」规则**违反归类约定**（已有 `90_temp_work/lyl660_ocr_20260609/`、`90_temp_work/jglx/cache_20260619/` 同类先例）。建议后续整理时整体迁至 `90_temp_work/`，本审计未做任何移动。
4. **sg `99_缓存与旧版/` 近乎空壳**：仅含 `__pycache__/` 与 `__pycache__scripts/`（共 7 个 .pyc，均被忽略），无实际「旧版」内容，可考虑归并或随临时物规则处置。

---

## 2. coding-workspace — 空目录是否仍需要

### 2.1 现状

- 完全空目录（0 个条目），创建于 2026-08-01，最近访问 2026-08-05。
- **git 不可见**：git 不跟踪空目录（`git ls-files coding-workspace` 为空）；未被 .gitignore 忽略（但空目录本就无碍）。

### 2.2 结论：按文档意图仍保留，但无任何 git/内容足迹

- WORKSPACE_ORGANIZATION.md「整理记录」（2026-08-04）明确记载：`coding-workspace/` 为 coding-tools-mcp 运行目录，保留。
- 仓库内除该文档与本次计划文件外，无 coding-tools-mcp 配置或引用（属外部工具的运行目录，正常不入库）。

### 2.3 建议

- **保留**（尊重 2026-08-04 决策）。若 coding-tools-mcp 已不再使用，可向用户单独确认后移除；本审计不删除。
- 若希望该目录在 git 中可追踪/被文档持续引用不悬空，可在其中放置 `README.md` 或 `.gitkeep`（需用户确认，属新增文件）。

---

## 3. 根目录杂项与 .gitignore 一致性

### 3.1 git status 现状（只读检查）

- 1 个已修改文件：`.opencode/skills/xelatex-compile/SKILL.md`（+95/-34，本次会话前已存在，非本 agent 改动）。
- 未跟踪文件（全部非忽略）：
  - `.hermes/plans/2026-08-05_workspace-cleanup.md`（本次工作区整理计划）
  - `90_temp_work/agent_prompt_t1.md`、`agent_prompt_t3.md`、`90_temp_work/cleanup_report_t1.md`（并行子 agent 产物，应随 orchestrator 统一提交）

### 3.2 .gitignore 与 WORKSPACE_ORGANIZATION.md 一致性核对

- 嵌套仓库列表：文档（WORKSPACE_ORGANIZATION.md:93）列 4 个 → 均验证存在 `.git/`：`01_projects/CodexCont/`、`01_projects/chatgpt-register-k12/`、`01_projects/dachaung/sidecars/skill/`、`90_temp_work/grok-build-zh-20260801/`；.gitignore 中 4 条对应忽略规则均正确。✓
- 工具目录：`.codex-playwright/`、`.worktrees/` 已忽略 ✓；`.opencode/`、`.superpowers/`、`.zcode/` 为**有意跟踪**（文档「工具配置目录保持原位」）；`.claude/`、`.agents/` 为空目录（git 天然忽略）。
- 敏感保护：`/90_temp_work/_private/` 已忽略，实测 `_private/workbuddy/id_ed25519`（`**/id_ed25519*` 兜底）均不入库 ✓。全仓 `git ls-files` 未发现 .db/.aux/.log/__pycache__/dist/.zip/.venv 等被误跟踪 ✓。

### 3.3 应忽略但未忽略的文件

- **未发现**应忽略却未忽略的文件。全部非忽略未跟踪项（.hermes 计划、90_temp_work 三个任务产物）均为本次整理流程的正常工作文件，应由 orchestrator 统一提交，不属于「应忽略」。

### 3.4 发现的问题

#### P1（中等）：`.hermes/` 处于未跟踪且未忽略的灰色地带

- `.hermes/plans/2026-08-05_workspace-cleanup.md` 显示为 untracked（`.gitignore` 未覆盖 `.hermes/`）。同类的 `.codex-playwright/`、`.worktrees/` 均已被忽略，`.opencode/` 等被跟踪，唯独 `.hermes/` 两者都不是。
- 建议二选一：**(a)** 在 .gitignore 增加 `.hermes/`（若为本地计划/草稿工作区）；**(b)** 正式跟踪（若打算保留计划留痕）。倾向 (a)，与 .codex-playwright 同类处理。

#### P2（轻微）：.gitignore 存在过期条目（指向已不存在的路径）

| 行号 | 规则 | 现状 |
|---|---|---|
| 119 | `workbuddy/` | 根目录无 workbuddy；实际 `_private/workbuddy/` 已由 `/90_temp_work/_private/` 覆盖 → 冗余 |
| 121 | `/restored_codex_tokens (1)/` | 路径已不存在 → 过期 |
| 122 | `/74c77e93-aaf7-40df-8e55-ffd5d0f6b3cc-sub2api.json` | 文件已不存在 → 过期 |
| 118/35 | `**/.codex_tmp/`、`marker312/` | 当前均无对应路径（保留可作前瞻，非错误） |

- 建议清理 119/121/122 三行（属 .gitignore 文本维护，不涉及任何文件操作）。

#### P3（轻微）：.gitignore 注释与嵌套仓库列表存在表述偏差

- .gitignore:109-112 将 `01_projects/grok-register-panel/` 归入「独立嵌套 Git 仓库」注释块，但该目录**没有 `.git/`**（`01_projects/grok-register-panel/.git` 不存在），是普通被父仓忽略的项目目录（文档 01_projects 表列它、嵌套仓库清单未列它，二者一致）。注释表述易误导，建议注释措辞改为「父仓忽略的独立项目目录」。

#### P4（提示）：WORKSPACE_ORGANIZATION.md 与 .gitignore 的规则边界建议补一句

- 文档「规则 → 工具目录」仅举例 `.git/、.opencode/、.claude/、.codex-playwright/`，未提及 `.hermes/`、`.agents/`、`.superpowers/`、`.zcode/`。若采用 P1 方案 (a)，建议在文档中补注「本地计划/草稿类工具目录（如 `.hermes/`、`.agents/`）被忽略、不入库」，使两份文件表述一致。

#### P5（提示）：根目录存在未提交改动

- `.opencode/skills/xelatex-compile/SKILL.md` 有未提交修改。若该改动为本轮有意变更，应随 orchestrator 统一提交；否则需回退确认。

---

## 4. 问题清单汇总与建议

| # | 优先级 | 位置 | 问题 | 建议 |
|---|---|---|---|---|
| 1 | 中 | `.gitignore` + `.hermes/` | `.hermes/` 未跟踪且未忽略 | 加入 `.gitignore`（推荐）或正式跟踪 |
| 2 | 低 | `.gitignore:119/121/122` | 过期条目指向不存在路径 | 清理文本条目 |
| 3 | 低 | `.gitignore:109-112` | grok-register-panel 被标注为嵌套仓库（实为被忽略的普通项目） | 修正注释措辞 |
| 4 | 低 | `WORKSPACE_ORGANIZATION.md:92` | 工具目录清单未含 .hermes/.agents 等 | 补注本地草稿工具目录的忽略约定 |
| 5 | 低 | 根目录 | SKILL.md 存在未提交修改 | 随统一提交或回退 |
| 6 | 低 | `02_study_materials` | ky/sx/ep 内嵌 OCR/渲染中间物、gcjjx 残留编译产物，违反「临时物→90_temp_work」约定（但均已被 gitignore） | 后续单独确认后迁移；本审计未动 |
| 7 | 信息 | `coding-workspace/` | 空目录、git 不可见，仅文档声明保留 | 保留；确认 coding-tools-mcp 仍使用 |
| 8 | 信息 | `02_study_materials` | 结构完整无缺失；jglx 编号命名、sg 99_ 空壳为记录项 | 无需处理 |

## 5. 合规性确认

- 未删除任何文件 ✓
- 未执行任何 git 写操作（无 add/commit/restore/checkout 等）✓
- 未读取或改动 `90_temp_work/_private` 内容 ✓
