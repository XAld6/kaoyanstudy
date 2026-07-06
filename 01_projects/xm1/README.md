# 校园建筑外墙脱落、裂缝 AI 图像识别巡检系统

完整可运行的校园建筑外墙巡检原型系统，包含 AI 图像识别、Web 上传演示、API 接口、SQLite 巡检记录、维修工单闭环和 Cloudflare Workers 测试页。

缺少训练权重时自动启用规则演示检测，保证首次运行即可演示。后续可使用真实数据训练 YOLO 替换 `data/models/best.pt`。

> 详细系统设计和业务流程见 [docs/system_design.md](docs/system_design.md)。

## 安装运行

```bash
cd d:\xm\xm1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\init_db.py
python scripts\generate_samples.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问 `http://127.0.0.1:8000`。

## 单图推理

```bash
python scripts\predict.py data\samples\sample_01_crack.jpg
```

输出结果图默认保存到 `data/results/`。

## 规则检测性能

演示模式优先使用 OpenCV 的 `connectedComponentsWithStats` 加速连通域检测，无 OpenCV 时自动回退 NumPy。提升性能可安装：

```bash
pip install opencv-python
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | Web 首页 |
| POST | `/api/detect` | 上传图片识别（字段 `file`） |
| POST | `/api/detect-batch` | 批量上传识别（字段 `files`） |
| POST | `/api/detect-sample` | 样例识别（字段 `sample`） |
| GET | `/api/records` | 历史巡检记录 |
| GET | `/api/tasks` | 巡检任务 |
| GET | `/api/work-orders` | 维修工单 |
| POST | `/api/generate-samples` | 生成演示图片 |

## Cloudflare Workers 测试页

项目内置 `cf-worker/`，可部署到 CF 域名测试远程访问。详见 [docs/cloudflare_worker.md](docs/cloudflare_worker.md)。

本地预览：

```bash
cd d:\xm\xm1\cf-worker
npm.cmd install
npm.cmd run dev
```

访问 `http://127.0.0.1:8787`。

## 真实 YOLO 训练

详见 [docs/dataset_format.md](docs/dataset_format.md)。简要步骤：

```bash
pip install -r requirements-yolo.txt
# 1. 准备数据放入 data/datasets/wall_defects/
# 2. 训练
python scripts\train.py --epochs 80 --imgsz 960 --batch 8
# 3. 复制 best.pt 到 data/models/best.pt
# 4. 重启服务，自动切换 YOLO 引擎
```

## 项目结构

```text
xm1/
  app/            FastAPI 应用
    main.py         路由定义与启动配置
    database.py     SQLAlchemy 模型与会话管理
    services.py     业务逻辑（检测、记录、工单）
    serializers.py  ORM→字典序列化
  cf-worker/      Cloudflare Workers 测试网页
  configs/        系统配置与 YOLO 数据配置
  data/           样例、上传、结果、模型和训练数据
  docs/           系统设计与数据集说明
  models/         检测器与风险评估
  scripts/        初始化、样例生成、推理、训练脚本
  static/         前端样式
  templates/      Web 页面与 Jinja2 宏
  utils/          配置、图片处理、样例生成工具
```
