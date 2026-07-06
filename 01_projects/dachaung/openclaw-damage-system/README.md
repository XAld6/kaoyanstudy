# 智爪识损 - OpenClaw基础设施病害AI识别系统

这是一个可本地运行的完整Web系统原型，实现“上传巡检图片 -> AI病害识别 -> OpenClaw/Lobster风格Agent工作流 -> 风险评估 -> 人工复核 -> 历史记录 -> PDF报告导出”的闭环。

## 运行方式

先安装后端依赖：

```powershell
cd D:\xm\dachaung\openclaw-damage-system\backend
C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements.txt
```

后端：

```powershell
cd D:\xm\dachaung\openclaw-damage-system\backend
C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd D:\xm\dachaung\openclaw-damage-system\frontend
npm.cmd run dev
```

访问：

```text
http://127.0.0.1:5173
```

## 核心能力

- 图片上传与文件管理
- OpenCV真实图像处理和病害候选区域识别
- 裂缝、剥落、渗水/色差疑似区域提示
- OpenClaw兼容式Agent工作流
- 风险等级判断与复核路由
- SQLite历史记录
- 标注图生成
- 人工复核状态保存
- PDF报告导出

## 示例图片

- `sample-crack.png`：轻量裂缝样例，可用于快速验证上传与识别流程。
- `demo-concrete-crack.png`：展示用混凝土裂缝图片，可用于演示标注图和报告导出效果。

## 定位说明

本系统定位为基础设施巡检的智能辅助初筛与项目展示原型，不替代正式工程检测结论。
