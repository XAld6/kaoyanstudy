# 考研学习控制台

一个自用的考研学习网页工具，聚焦“今日任务、执行记录、复盘、计划调整、进度对比、AI 建议”。

两种运行形态：

- **线上（VPS）**：部署到有域名的 VPS，前端静态产物由 Caddy 托管并自动 HTTPS，后端 FastAPI 由 systemd 守护，**学习数据保存在服务端 SQLite**，手机/电脑多端访问同一份数据。详见下文「线上部署」。
- **本地（Windows 本机开发）**：双击 `kaoyan-console.bat` 即可启动，数据仍走服务端 API；没有后端时前端会退化为“本地只读缓存”模式。

## 数据存储说明

- **唯一数据源是服务端 SQLite**（`/opt/kaoyan-console/data/app.db`）。
- 浏览器 localStorage 只保留**只读缓存**（离线可看、不可编辑），键为 `kaoyan-study-console:cache:v1`。
- 旧版 localStorage 数据（键 `kaoyan-study-console:v1`）不会被写入或删除，可在设置页「从本机旧数据一键迁移」导入服务器。
- 服务器每天 03:17 自动备份（`.db.gz` + `.json.gz` 双份，保留 30 天）。

## 一键启动（仅 Windows 本机）

推荐双击：

```text
kaoyan-console.bat
```

菜单说明：

- `1` 一键启动前端、后端，并打开浏览器
- `2` 保存并关闭服务进程
- `3` 查看前端/后端端口状态
- `4` 退出菜单

默认地址：

- 前端：`http://127.0.0.1:5188`
- 后端：`http://127.0.0.1:8018`

## 手动启动（本机开发）

前端：

```powershell
cd kaoyan-study-console\frontend
npm.cmd install
npm.cmd run dev
```

后端：

```powershell
cd kaoyan-study-console\backend
python -m pip install -r requirements.txt
$env:KAOYAN_DB_PATH = "$PWD\data\app.db"   # 可选；默认 backend/data/app.db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8018
```

> `.bat` / `.ps1` 启动脚本仅用于 Windows 本机开发；服务器部署见 `deploy/README.md`。

## 线上部署

前置条件：Ubuntu 类 VPS、一个已解析到 VPS 的域名、`/opt/kaoyan-console` 目录、GitHub 私有仓（deploy key 拉取）。

架构：

```text
浏览器 --HTTPS--> Caddy(自动证书 + Basic Auth)
                    ├── /api/*  → 127.0.0.1:8018（FastAPI/uvicorn，systemd 守护）
                    └── 静态文件 → /opt/kaoyan-console/web（前端构建产物）
数据：/opt/kaoyan-console/data/app.db（SQLite，WAL）
备份：/opt/kaoyan-console/backups/（每日 .db.gz + .json.gz，保留 30 天）
密钥：/etc/kaoyan-console.env（OPENAI_API_KEY 等，0640，不入库）
```

部署步骤、systemd unit、Caddyfile、备份/更新脚本与故障排查见 **`deploy/README.md`**。

首次启用流程：

1. 浏览器打开线上地址，登录 Basic Auth（用户名/口令在 Caddyfile 里配置的哈希）；
2. 设置页「从本机旧数据一键迁移」把旧版 localStorage 数据搬上服务器，或直接「导入 JSON 到服务器」；
3. 手机访问同一地址，能看到同一份数据。

## 功能地图

今日页：

- 添加今日任务、快速模板任务
- 勾选完成、记录实际学习分钟数（支持 +15 / +30 / 填满计划）
- 专注计时：正计时 / 番茄（15 / 25 / 45 分钟可选，记住上次选择），绑定任务后结束可自动累加实际时长
- 番茄完成后自动进入 5 分钟休息倒计时（可跳过；休息结束也会提醒）
- 今日专注统计：计时器记入的专注分钟与番茄个数（独立于任务实际时长）
- 键盘快捷键（计时进行中）：空格 暂停/继续 · Enter 结束并记入 · Esc 跳过休息/丢弃（输入框内不触发）
- 计时中顶部常驻条（任意页面可暂停/结束/跳过休息）+ 浏览器标签实时显示剩余/已用时间
- **刷新页面不丢计时**：番茄/正计时/休息进度写入 sessionStorage；离开期间已到点的番茄会按目标分钟记入，并尽量接上剩余休息
- 番茄到点提示音 + 系统通知（设置页可开关并测试）
- 逾期提醒：一键把逾期任务整理到当前日期
- 复盘模板：按当天完成率和未完成任务生成复盘草稿
- 收尾检查：检查复盘、实际时长、明日任务是否准备好
- 一键收尾：补复盘草稿 + 补完成任务时长 + 顺延未完成到明天
- 明日开局：把未完成任务整理到明天
- 刷新页面会记住当前标签页（sessionStorage）

计划页：

- 顶部快捷操作：复制上周、顺延未完成、整理逾期、一键减负、一键补块、生成周报
- 周视图和全部任务视图
- 按科目、优先级、状态筛选
- 复制上周计划到本周
- 批量提前/推后任务日期
- 批量调整可见任务优先级和状态
- 顺延未完成任务
- 本周容量对比和调整建议
- 一键减负：把过重日期的低优先级任务推后
- 一键补块：给偏少科目补一个 60 分钟基础块

进度页：

- 学习热力日历：最近 8/12/16 周实际学习量热力图，点击切换当前日期；显示连续天数与合计
- 查看最近 7/14/30 天科目计划时长和实际时长
- 调整各科每周目标小时数
- 一键生成周报（完成率、分科执行、调整提示、下周三条重点），支持复制与下载 Markdown
- 写入复盘：把周报摘要追加到当前日期复盘（同一周不会重复写入）

AI 教练：

- 使用最近 7 天任务、今日完成情况和复盘文本生成建议
- 固定结构：补哪科 / 砍哪块 / 明日三件事
- API 不可用时自动显示同结构的本地规则建议

设置页：

- 修改目标日期
- 新增、改名、删除科目
- 调整科目颜色和每周目标
- 配置 OpenAI 兼容 API（服务器上 Key 只读，只能通过 `/etc/kaoyan-console.env` 配置）
- 测试 API 连接
- 查看同步状态与数据概览
- 从本机旧数据一键迁移 / 导入 JSON 到服务器 / 从服务器下载备份 / 导出 JSON
- 导入 JSON 数据

## API 配置

**服务器（线上）**：API Key 只能写在服务器 `/etc/kaoyan-console.env`，网页只读、不回显：

```text
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

**本机开发**：可以通过环境变量（同上）或沿用 `backend/llm_config.local.json`（只读回退）。设置页的 Base URL / Model 可调整，用「测试连接」验证。

## 数据备份

**服务端自动备份**：每日 03:17 由 systemd timer 执行，产出双份：

- `app-<时间>.db.gz`：SQLite 一致快照（WAL 安全），可整机恢复
- `app-<时间>.json.gz`：网页可直接读回的 JSON 备份

保留 30 天。手动备份与恢复命令见 `deploy/README.md`。

**网页导出**（额外保险）：设置页「导出 JSON 备份」随时可用，导入前系统会先自动下载一份当前数据备份。

## 验证

前端测试和构建：

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

端到端同步验证（需先启动前后端）：

```powershell
node scripts/verify_sync.mjs            # online：水合/去抖推送/刷新持久
$env:VERIFY_PHASE="offline"; node scripts/verify_sync.mjs    # 离线只读
$env:VERIFY_PHASE="conflict"; node scripts/verify_sync.mjs   # 双标签页冲突
```

后端测试：

```powershell
cd backend
python -m pytest
```

## 项目结构

```text
kaoyan-study-console/
  frontend/              React + Vite + TypeScript 前端
    src/main.tsx         应用状态与页面编排（含服务端同步数据流）
    src/remoteStore.ts   服务端同步网络层（fetch/push/import + 去抖）
    src/storage.ts       本地只读缓存与旧数据迁移读取
    src/studyCore.ts     学习业务纯函数
    src/focusTimer.ts    专注计时
  backend/               FastAPI 后端
    app/main.py          API 入口（state/config/advice/health）
    app/db.py            SQLite 数据层（WAL、每请求连接、备份）
    app/state.py         数据校验与读写/合并（镜像前端校验规则）
  deploy/                VPS 部署物：Caddyfile、systemd unit、备份/更新脚本、运维文档
  docs/迁移说明.md        localStorage → 服务端迁移步骤
  kaoyan-console.bat     推荐入口（仅 Windows 本机）：打开中文菜单
  .runtime/              启动日志、PID、测试临时目录
```

## 常见问题

- **页面顶部出现「离线只读」红条**：连不上后端。检查 `systemctl status kaoyan-api` 与 `journalctl -u kaoyan-api`；恢复后页面会自动重试。
- **出现「数据冲突」**：另一台设备更新过数据。页面已自动下载本机版本，选择「加载服务器版本」或「用本机版本覆盖」即可。
- **提示音/系统通知不弹**：浏览器通知需要 HTTPS 安全上下文；线上域名必须启用 HTTPS（Caddy 自动提供），并到设置页「请求通知权限」。