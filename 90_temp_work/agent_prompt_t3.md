任务 T3：审计 D:\xm\00_deliverables 与 D:\xm\01_projects。

1) 00_deliverables：
   - 根部有 grok-register-panel.zip（2026-08-01），按组织规范交付 ZIP 应归入子目录。建议在 00_deliverables 下创建 grok-register-panel/ 子目录并移入该 zip（如无冲突则直接执行移动）。
   - 检查 leleche/（current + archive 结构）、resumes/、linear_algebra_solutions/、mz_linear_solution/、rc_sampling_solutions/ 是否符合 WORKSPACE_ORGANIZATION.md 描述。

2) 01_projects：
   - 检查各项目目录健康度：chatgpt-register-k12、CodexCont、dachaung、grok-register-panel、jglx_latex_project、kaoyan-study-console、mz_linear_solution_project、steel_structure_thesis、xm1、zy_latex_work。
   - 有无散落垃圾文件、README 是否存在、与 NESTED_REPOS.md 描述是否一致。
   - 注意：CodexCont、chatgpt-register-k12、grok-register-panel 是嵌套独立 git 仓库，不要改动其内部。

禁止：删除任何文件；执行 git 写操作（add/commit/push）；改动嵌套仓库内部。

产出：审计结论写入 D:\xm\90_temp_work\cleanup_report_t3.md，列出每项现状、执行的动作、建议。
