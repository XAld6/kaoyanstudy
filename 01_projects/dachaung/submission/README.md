# submission — 申报材料

## 文档

| 文件 | 说明 |
|------|------|
| **`智爪识损-OpenClaw-v1.1文实对齐版.docx`** | **当前建议主稿**：与原型 v1.1 能力一致（OpenCV 默认 + YOLO 可插拔 + 可演示闭环） |
| `智爪识损-OpenClaw评审优化丰富版.docx` | 早期评审优化扩写版（表述偏“拟建深度模型”，答辩前请以 v1.1 版为准） |
| `智爪识损-基于OpenClaw的大创通知合规扩写版.docx` | 按大创通知合规扩写版 |
| `宁夏理工学院中国国际大学生创新大赛(2026)申报书-OpenClaw版.docx` | 大赛申报书源模板 |
| `submission_review.docx` | 中间审阅稿 |
| `notice_requirements.txt` | 从立项通知抽取的要求 |

## v1.1 文实对齐要点（写进材料的真实能力）

- 已有可本地运行的 Web 原型与 6-Agent 兼容工作流  
- 默认 **OpenCV** 三类病害初筛：裂缝 / 剥落 / 渗水·色差  
- **YOLO 可插拔**，未配置权重时自动回退，不虚构“已训练工业级模型”  
- 支持风险分级、人工复核、历史记录、PDF 报告、样例批跑  
- 定位：智能辅助初筛与展示原型，**不替代正式工程检测结论**

## 脚本

路径均相对本目录（`HERE`），在 `submission/` 下运行即可。

| 脚本 | 作用 |
|------|------|
| `rewrite_v11_fact_aligned.py` | **生成 v1.1 文实对齐版（推荐）** |
| `verify_v11_fact_aligned.py` | 校验 v1.1 版关键词与字数 |
| `rewrite_openclaw_evaluation_optimized.py` | 生成评审优化丰富版（旧） |
| `rewrite_notice_compliant_submission.py` | 生成通知合规扩写版 |
| `rewrite_openclaw_submission.py` | 从审阅稿生成大赛申报书 |
| `verify_*.py` | 校验对应 docx 关键内容 |
| `inspect_*.py` / `extract_notice_requirements.py` | 检查与抽取工具 |

示例：

```powershell
cd D:\xm\01_projects\dachaung\submission
python rewrite_v11_fact_aligned.py
python verify_v11_fact_aligned.py
```
