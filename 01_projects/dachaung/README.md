# 智爪识损 · 大创项目工作区

宁夏理工学院 2026 大创 / 中国国际大学生创新大赛相关材料与原型系统。

**项目名：** 智爪识损——基于 OpenClaw 的基础设施病害 AI 全自动识别与诊断系统

## 目录结构（主线清晰）

```text
dachaung/
├── openclaw-damage-system/   # ★ 可运行原型系统（主交付）
├── submission/               # 申报书 docx + 改写/校验脚本
├── presentation/             # 答辩 PPT 与生成工具
├── sidecars/                 # 旁支/无关内容（不参与主线评审）
└── README.md                 # 本说明
```

| 目录 | 内容 | 是否主线 |
|------|------|----------|
| `openclaw-damage-system/` | FastAPI + React 巡检原型、样例、演示脚本、PDF 报告 | **是** |
| `submission/` | 申报书、通知要求、rewrite/verify 脚本 | **是** |
| `presentation/` | `ppt_rebuild` / `ppt_visuals` / PPT 生成脚本 | **是** |
| `sidecars/` | 技能库 `skill/`、结构设计成绩计算器等杂项 | 否 |

## 快速入口

### 1. 跑系统（答辩演示）

```powershell
cd D:\xm\01_projects\dachaung\openclaw-damage-system
.\start-all.bat
```

浏览器：`http://127.0.0.1:5173`  
样例图：`openclaw-damage-system/samples/`  
批跑：`python scripts\demo_run.py --pdf`

详见：`openclaw-damage-system/README.md`

### 2. 申报材料

路径：`submission/`

**建议主稿（与系统 v1.1 一致）：**

- `智爪识损-OpenClaw-v1.1文实对齐版.docx`

重新生成 / 校验：

```powershell
cd D:\xm\01_projects\dachaung\submission
python rewrite_v11_fact_aligned.py
python verify_v11_fact_aligned.py
```

历史稿仍保留在同目录，详见 `submission/README.md`。

### 3. 答辩 PPT

路径：`presentation/`

- 成品：`ppt_rebuild/slide01/`、`ppt_rebuild/slides02_12/`
- 预览页：`ppt_visuals/scheme_c_single_pages/`
- 生成脚本：`tools/create_slide01_pptx.py`、`tools/create_slides02_12_pptx.py`

### 4. 旁支（勿与主线混淆）

`sidecars/skill/`：技能爬取 / 小跃伴侣等，**不是智爪识损本体**。  
`sidecars/结构设计成绩自动计算.html`：独立小工具。

## 当前系统能力（v1.2）

- 三类病害初筛：裂缝 / 剥落 / 渗水·色差
- **可插拔检测后端**：默认 OpenCV；可配置 YOLO（未就绪自动回退）
- **批量检测**（最多 12 张）+ 历史筛选 / 统计 / 删除
- OpenClaw 兼容 6-Agent 本地工作流
- 前端分色展示 + metrics 卡片 + 后端状态徽章
- 人工复核、PDF 报告、固定样例批跑

> 定位：智能辅助初筛与项目展示原型，不替代正式工程检测结论。

## 整理说明（2026-07）

- 将 `skill/`、成绩计算器移入 `sidecars/`
- 将申报材料与脚本归入 `submission/`
- 将 PPT 相关归入 `presentation/`
- 根目录只保留四大板块 + 本 README
