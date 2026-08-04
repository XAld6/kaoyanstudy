# 智爪识损 - OpenClaw 基础设施病害 AI 识别系统

**版本 2.0.0** · 本地可运行 Web 原型，闭环：

**上传巡检图片 → 图像质检 → 病害候选识别 → 量化分析 → 风险分级 → 人工复核 → 历史归档 → 多格式导出**

> 定位：智能辅助初筛与项目展示原型，不替代正式工程检测结论。

## 目录结构

```text
openclaw-damage-system/
├── backend/          # FastAPI + OpenCV + SQLite + PDF
├── frontend/         # React + Vite
├── samples/          # 固定演示样例包
├── scripts/
│   ├── build_samples.py
│   └── demo_run.py
├── start-all.bat
├── stop-all.bat
├── start-backend.bat
└── start-frontend.bat
```

## 快速启动

### 方式 A：一键启动（推荐）

```powershell
cd D:\xm\01_projects\dachaung\openclaw-damage-system
.\start-all.bat
```

浏览器打开：`http://127.0.0.1:5173`

结束服务：

```powershell
.\stop-all.bat
```

### 方式 B：分别启动

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

- 前端：`http://127.0.0.1:5173`
- 后端 API：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/health`

## 核心能力（v2）

| 模块 | 能力 |
|------|------|
| 检测 | 裂缝 / 剥落 / 渗水·色差；OpenCV 默认，YOLO 可插拔 |
| 工作流 | 6-Agent OpenClaw 兼容本地适配 |
| 质检 | 质量等级 A/B/C、评分、欠曝/过曝/模糊等问题标签 |
| 可解释 | 每个候选带中文解释说明 |
| 历史 | 筛选 / 排序 / **分页** / 多选 / 删除 / 重检 |
| 复核 | 单条复核、批量复核、复核后自动下一条 |
| 导出 | CSV / PDF ZIP / **JSON**；按筛选或选中 ID |
| 对比 | 双记录风险与量化对比 |
| 参数 | 灵敏度等阈值可调，**落盘持久化** |
| 运维 | 孤儿文件扫描清理、存储健康信息、WAL SQLite |
| 界面 | 暗色模式、统计面板、缩略图条、键盘导航 |

## 常用 API

```text
GET  /api/health
GET  /api/system
GET  /api/stats
GET  /api/records                 # 列表（可 sort/order/limit/offset）
GET  /api/records/page            # 分页 {items,total,page,pages}
GET  /api/records/{id}
GET  /api/records/{id}/neighbors
POST /api/detect
POST /api/detect/batch
POST /api/records/{id}/review
POST /api/records/{id}/redetect
POST /api/records/batch-redetect
POST /api/records/batch-review
POST /api/records/batch-delete
GET  /api/export/csv
GET  /api/export/pdf-zip
GET  /api/export/json
GET  /api/compare
GET|PUT /api/settings
POST /api/settings/reset
GET|POST /api/maintenance/orphans
```

## 快捷键

| 键 | 功能 |
|----|------|
| `U` | 上传 |
| `R` | 重新检测当前记录 |
| `S` | 参数面板 |
| `E` | 保存复核 |
| `↑↓` / `J K` / `←→` | 切换记录 |
| `Esc` | 关闭放大层 / 参数面板 |

## 演示样例

样例目录：`samples/`

| 文件 | 场景 |
|------|------|
| `01_plain_surface.png` | 正常表面 |
| `02_crack_synthetic.png` | 合成裂缝 |
| `03_spalling_synthetic.png` | 合成剥落 |
| `04_stain_synthetic.png` | 合成渗水/色差 |
| `05_mixed_damage.png` | 混合病害 |
| `06_sample_crack.png` | 内置裂缝样例 |
| `07_demo_concrete_crack.png` | 混凝土展示图 |

```powershell
python scripts\build_samples.py
python scripts\demo_run.py
python scripts\demo_run.py --pdf
```

### 建议答辩演示顺序

1. 上传 `01_plain_surface.png` → 低风险  
2. 上传 `02_crack_synthetic.png` → 裂缝标注 + 解释  
3. 上传 `03` / `04` → 剥落 / 渗水  
4. 上传 `05` 或 `07` → 多类型 + 风险 + 复核  
5. 调参数 → 重检 → 对比两条记录  
6. 导出 CSV / PDF 包 → 展示统计面板与暗色模式  

## 环境变量（可选）

| 变量 | 说明 |
|------|------|
| `OPENCLAW_DETECTOR` | `opencv`（默认）或 `yolo` |
| `OPENCLAW_YOLO_WEIGHTS` | YOLO 权重路径 |
| `OPENCLAW_YOLO_CONF` | YOLO 置信度阈值 |
| `OPENCLAW_DATA_DIR` / `UPLOAD_DIR` / `OUTPUT_DIR` / `DB_PATH` | 数据路径 |
| `OPENCLAW_SETTINGS_PATH` | 运行参数 JSON 路径 |
| `OPENCLAW_PDF_FONT_PATH` | PDF 中文字体 |

## 测试

```powershell
cd D:\xm\01_projects\dachaung\openclaw-damage-system
python -m pytest backend/tests -q
cd frontend
npm.cmd run build
```
