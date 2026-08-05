# T2 90_temp_work 目录审计与归类报告

日期：2026-08-05
审计范围：`D:\xm\90_temp_work\` 下全部 11 个子目录（grok、grok-build-zh-20260801、jglx、latex_review_20260705、leleche、lyl660_ocr_20260609、misc_downloads、nat-exhibition、tmp、transcript_ocr、zy_latex_work）。
对照基准：`WORKSPACE_ORGANIZATION.md` 第 64–99 行 与 `90_temp_work/README.md`。
限制：未删除任何文件；未移动大型目录整体；未执行任何 git 写操作；未触碰 `_private/`（仅做了目录级查看）。

---

## 逐目录审计结果

### 1. grok/ — ✅ 与描述一致
- 现状：`fix_hermes_auth.py`、`start_hermes_gateway.ps1`、`test_hermes_apis.py`、`hermes_gateway_stdout.log`（0 B）、`hermes_gateway_stderr.log`（95 B），共 5 个文件。
- 对照：README 描述“hermes/grok 网关一次性脚本与日志（fix_hermes_auth.py、start_hermes_gateway.ps1、test_hermes_apis.py、hermes_gateway_*.log）”——完全吻合。
- 问题：无。stdout 日志为空、stderr 仅 95 B，属正常运行痕迹。

### 2. grok-build-zh-20260801/ — ✅ 嵌套独立 git 仓库，不属父仓管理
- 现状：完整 Rust 工程（Cargo.toml、crates/、bin/、docs/、prod/、third_party/ 等），含自身 `.git/`；文件 8235 个，约 1.5 GB，其中 `target/` 构建产物约 1.4 GB。
- 对照：`WORKSPACE_ORGANIZATION.md` 规则节明确其为嵌套独立 git 仓库，父仓忽略其内容；README 表格未列此项（仅出现在顶层规则），属文档缺省而非内容错位。
- 问题：`target/` 为 Rust 构建缓存，体积大，但位于嵌套仓库内部，按规则不得改动。
- 建议：可考虑在嵌套仓库内执行 `cargo clean` 释放约 1.4 GB（需单独确认，勿动其内部 git 状态）。

### 3. jglx/cache_20260619/ — ✅ 与描述一致
- 现状：OCR 缓存（`_final_ocr_cache/` 794 个文件）、多组预览/美化渲染（`_final_preview*`、`_beautified_*`、`_perfect_preview`、`_render_ch0*/`）、审计产物（`audit_sources_report.txt`、`includegraphics_audit.txt`、`manual_correction_audit*.md`、`strict_retype_figure_audit.*`、`final_build*.log` 等），共 940 个文件约 68 MB。
- 对照：WORKSPACE 描述“结构力学 OCR/预览/审计缓存”——吻合。
- 问题：无分类性问题。个别 OCR 对缺 `_ocr.jpg`（如 12 作业 p018/p019、部分 `作业答` 序列），属内部 OCR 产物不完整，非归档问题。

### 4. latex_review_20260705/ — ✅ 与描述一致
- 现状：`main.tex` + `out/`（aux/log/lof/out/toc/pdf 编译产物）+ `scripts/`（`test_scan_tex_path.py`、`_read_pdf.py`、`_scan_tex.py`），共 10 个文件。
- 对照：描述“一次性审阅包与脚本”——吻合。

### 5. leleche/ — ⚠️ 大体一致，发现 1 处图片放置不一致
- 现状：`active/`（main.tex、fig_catalog.tex、tab_catalog.tex、build/、images/、rendered/、review_rendered/）+ `snapshots/2026-07-06_latex_revision/`。
- 对照：WORKSPACE 描述“active 当前 LaTeX 工作包、snapshots 历史工作包”——吻合。
- 问题：`active/` 根目录平铺 3 张源图 `contact_1.jpg`、`contact_2.jpg`、`contact_3.jpg`（各约 150–190 KB），而其余照片（schemeA/B/C_photo*.jpg、fig3-1_user.png）均在 `active/images/` 下；snapshot 版无 contact 文件。`main.tex`/`fig_catalog.tex` 均未引用 contact 图（仅用它们生成过 `review_rendered/contact_*.png`）。这三张图属于**放错层级**的源图。
- 建议：将 `contact_1.jpg`、`contact_2.jpg`、`contact_3.jpg` 移入 `active/images/`（或随其用途归入 `active/review_rendered/` 来源区）。因三图已被父仓 git 跟踪，移动会留下 git 删除/新增记录，需在确认后连同 `git add -A` 一并处理，故本次未执行移动，仅记录建议。

### 6. lyl660_ocr_20260609/ — ✅ 与描述一致
- 现状：`extraction/`（key67_ocr.json、多组 txt、source_render_120/、key67_render/）+ `inspection/`（sample_pages_1_6.txt、render/），共 29 个文件约 4 MB。
- 对照：描述“线代书 OCR/检查产物”，且源 PDF 确位于 `02_study_materials/zy/ky/sx/lyl660/source.pdf`——吻合。

### 7. misc_downloads/ — ✅ 与描述一致
- 现状：`event.ics`（日历）、`Hermes.Agent.CN.Desktop_0.3.2_x64-setup.exe`（安装包，约 83 MB）、`nucleo-5b74652e.zip`（+ 展开目录 `nucleo-5b74652e-src/`，42 个文件）、`ubuntu-24.04.4-live-server-amd64.iso.torrent`（种子）。
- 对照：描述“安装包、种子、日历、第三方源码（含 nucleo-5b74652e-src/）等杂项”——完全吻合。
- 问题：无。

### 8. nat-exhibition/ — ✅ 与描述一致
- 现状：`index.html` + `server.pl`，共 2 个文件。
- 对照：描述“全国展览一次性页面（index.html + server.pl）”——完全吻合。

### 9. tmp/ — ⚠️ 文档描述不完整，存在与“r12 渲染中间物”无关的内容
- 现状：顶层为 r12 相关（`r12_check/`、`r12_front/`、`r12_pages/`、`r12_pages2/`、`final_text.txt`、`leleche_rules.txt`、`patch_test.txt`、`r12_main.txt`，内容为“第十九届全国大学生结构设计竞赛理论方案”），**符合**“r12 渲染中间物（已被 gitignore）”。
- 问题：`tmp/pdfs/` 子目录（181 个文件约 29 MB）内容混杂：
  - **线性代数 OCR 块**：`linear_algebra_workbook.pdf`（17 MB，OCR 文本对应“27《没咋了》线性代数通关讲义”）、`reference.html`（studylib.net 下载页被 Cloudflare 拦截的 “Just a moment...” 挑战页，6 KB）、`ocr/`（page-01..74.txt）、`pages160/`（page-01..74.jpg）、`preview/`（page-01..06.png）。该块与 leleche r12 完全无关，不属于“r12 渲染中间物”。
  - leleche 侧内容：`r09_midas_pages/`、`r10_simulation_pages/`、`r11_wheel_pages/`（c-*/p-*/final-*/q-*/*.png），属 leleche 早期版本渲染页。
- 建议（仅建议，未执行）：
  - 将 `tmp/pdfs/linear_algebra_workbook.pdf`、`reference.html`、`ocr/`、`pages160/`、`preview/` 从 tmp 中分离，归入 `lyl660_ocr_20260609/`（若该 OCR 属线代书作业）或另建 `线性代数讲义 OCR` 目录；`reference.html` 可作为“下载失败记录”一并归档。
  - `r09/r10/r11_*_pages` 与 leleche r12 渲染页关系更近，可归入 `leleche/active/rendered/` 对应历史区或保留在 tmp。
  - 说明：因整体约 29 MB 属“大型目录整体”，本次未执行移动；tmp/ 整体已被父仓 gitignore，移动不影响 git 跟踪，待确认后操作。
- 备注：README 对 tmp/ 的描述“r12 渲染中间物”未涵盖上述混杂内容，建议在确认归类后同步更新 README。

### 10. transcript_ocr/ — ✅ 与描述一致
- 现状：`page_1/2/3.png` + `page_1/2/3.txt`，共 6 个文件约 1.3 MB。
- 对照：描述“成绩单 OCR 产物（page_*.png/txt）”——完全吻合。

### 11. zy_latex_work/cache_20260619/ — ✅ 与描述一致
- 现状：`rendered/`（appendix-01..45、inline-01..36 等 PNG）+ `rendered_final/`（appendix-26..45、inline-28..34 PNG），共 67 个文件约 10 MB。
- 对照：描述“桥梁 LaTeX 渲染缓存”——吻合。

---

## 散落文件检查（90_temp_work 根目录）

| 文件 | 状态 | 结论 |
|---|---|---|
| `README.md` | 被跟踪 | 正常，目录说明 |
| `skills-audit-report.md` | 被跟踪 | 正常，WORKSPACE 已登记 |
| `cleanup_report_t1.md` | 未跟踪 | 正常，T1 审计报告产物，应保留 |
| `agent_prompt_t1.md` | 未跟踪 | T1 任务说明副本；保留作为审计记录，或可移入任务记录目录 |
| `agent_prompt_t3.md` | 未跟踪 | T3 任务说明副本；同上 |

根目录无异常散落文件。`_private/` 未被触碰（内含 ssh_helpers/、restored_codex_tokens/、workbuddy/ 等，均保持原位）。

---

## 已执行动作

- 未执行任何移动（唯一候选 `leleche/active/contact_*.jpg` 为 git 已跟踪文件，移动会引入未提交的删除/新增状态，与“执行 git 写操作”红线冲突，故只记录建议）。
- 未删除任何文件，未移动大型目录整体，未触碰 `_private/`。

## 建议动作汇总（均未执行，等待确认）

1. **leleche/active/contact_1..3.jpg** → 移入 `active/images/`，并 `git add -A` 提交移动记录。
2. **tmp/pdfs 线性代数 OCR 块**（pdf + reference.html + ocr/ + pages160/ + preview/）→ 从 tmp 分离归入 `lyl660_ocr_20260609/` 或新建独立 OCR 目录；`reference.html` 可归入 misc_downloads 作下载失败记录。
3. **tmp/pdfs r09/r10/r11 渲染页** → 视需要归入 `leleche/active/rendered/` 历史区。
4. **tmp/ README 描述** → 在完成上述归类后同步更新 `90_temp_work/README.md` 中 tmp/ 一行的描述。
5. **grok-build-zh-20260801/target/** → 在嵌套仓库内执行 `cargo clean` 释放约 1.4 GB（需确认，属删除类建议，未动手）。
6. **l 弹性：文档一致性** → WORKSPACE_ORGANIZATION.md 第 68–82 行与 README 表格基本一致，可补充 `grok-build-zh-20260801/` 到 README 表格（当前仅在顶层规则中提及）。

## 结论

11 个目录中 9 个与 WORKSPACE_ORGANIZATION.md / README 描述完全一致；`leleche/active/` 存在 3 张图片层级不一致，`tmp/pdfs/` 混杂了与“r12 渲染中间物”无关的线性代数 OCR 内容，为本次审计主要发现。上述均以建议形式记录，未做任何删除或不可逆操作。
