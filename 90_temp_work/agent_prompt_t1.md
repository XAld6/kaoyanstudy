任务 T1（改派，原 codex 后端不可用）：工作区安全整理。

1) 将 D:\xm 根目录下 3 个脚本 ssh_connect.py、ssh_interactive.py、status_check.py（含明文 SSH 密码，敏感）移动到 D:\xm\90_temp_work\_private\ssh_helpers\ 目录（不存在则创建）。
   用 PowerShell: New-Item -ItemType Directory -Force D:\xm\90_temp_work\_private\ssh_helpers; Move-Item 三个文件。
2) 用 git -C D:\xm diff .opencode/skills/xelatex-compile/SKILL.md 审查该文件的未提交改动（xelatex 编译技能增强），评估内容质量与是否值得提交，给出结论。
3) 审查结论写入 D:\xm\90_temp_work\cleanup_report_t1.md。

禁止：执行任何 git add/commit/push；删除任何文件；在报告中写入任何密码或凭据明文；触碰 _private 中其他内容。

完成后简要汇报移动结果与审查结论。
