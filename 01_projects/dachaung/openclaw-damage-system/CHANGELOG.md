# Changelog

## 2.0.0 — 大规模升级

### 后端
- SQLite WAL + 索引（风险/复核/时间/置信度/文件名）
- 记录分页 `GET /api/records/page`、排序 `sort/order`、offset
- 邻居导航 `GET /api/records/{id}/neighbors`
- 批量重检 `POST /api/records/batch-redetect`
- 统计增强：时间线、复核分布、置信度分桶、by_kind
- JSON 导出、孤儿文件扫描/清理、存储健康信息
- 请求耗时头 `X-Process-Time-Ms`、版本头 `X-App-Version`
- 图像质量等级/评分/问题标签；候选可解释字段 `explanation`
- PDF/CSV 导出纳入质量字段与解释

### 前端
- 暗色模式（localStorage 持久化）
- 统计可视化面板（风险/复核/类型/时间线）
- 分页、排序、待复核/高风险快捷筛选
- 批量重检、复核后自动下一条
- 侧栏快捷入口、质量评分展示、候选解释列

### 运维
- `stop-all.bat` 一键结束 8000/5173 端口进程
- README 更新至 v2 API 与快捷键说明

## 1.5.0
- 批量复核、键盘导航、缩略图条、上一条/下一条

## 1.4.0
- 参数落盘、重新检测、多选导出/删除、图片放大

## 1.3.0
- CSV/PDF ZIP 导出、双记录对比、运行参数面板

## 1.2.0
- 批量检测、筛选、统计、删除、可插拔 YOLO
